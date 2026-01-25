"""Hardware detection service for GPU/VRAM and system resource detection."""

import asyncio
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class GPUInfo:
    """GPU information."""

    detected: bool
    name: Optional[str] = None
    vendor: Optional[str] = None  # nvidia, amd, apple, intel
    vram_total_gb: Optional[float] = None
    vram_available_gb: Optional[float] = None
    compute_capability: Optional[str] = None


@dataclass
class CPUInfo:
    """CPU information."""

    name: str
    cores: int
    threads: int
    ram_total_gb: float
    ram_available_gb: float


@dataclass
class ModelRecommendation:
    """A model recommendation."""

    name: str
    reason: str


@dataclass
class Recommendations:
    """Hardware-based model recommendations."""

    max_model_params: str
    recommended_models: List[ModelRecommendation]
    inference_mode: str  # "GPU" or "CPU"


@dataclass
class HardwareInfo:
    """Complete hardware information."""

    gpu: GPUInfo
    cpu: CPUInfo
    recommendations: Recommendations


# Model recommendation table based on available VRAM
_VRAM_RECOMMENDATIONS = [
    # (min_vram_gb, max_params, models_with_reasons)
    (0, "3B", [
        ("llama3.2:1b", "Lightweight, fast inference"),
        ("phi3:mini", "Good quality for small size"),
    ]),
    (4, "7B", [
        ("llama3.2:3b", "Balanced performance"),
        ("qwen2.5:3b", "Strong multilingual support"),
    ]),
    (6, "7B", [
        ("qwen2.5-coder:7b", "Excellent for coding tasks"),
        ("mistral:7b", "Strong general purpose"),
    ]),
    (8, "13B", [
        ("llama3.1:8b", "High quality general purpose"),
        ("codellama:13b", "Advanced coding capabilities"),
    ]),
    (12, "14B", [
        ("qwen2.5:14b", "Premium quality model"),
        ("deepseek-coder:14b", "Professional coding model"),
    ]),
    (16, "70B-q4", [
        ("llama3.1:70b-q4", "Large model, quantized"),
        ("mixtral:8x7b", "Mixture of experts"),
    ]),
    (24, "70B", [
        ("llama3.1:70b", "Full precision large model"),
        ("qwen2.5:72b", "Premium large model"),
    ]),
]

# CPU-only recommendations (when no GPU is detected)
_CPU_RECOMMENDATIONS = [
    # (min_ram_gb, max_params, models_with_reasons)
    (0, "1B", [
        ("llama3.2:1b", "Minimal resource usage"),
    ]),
    (8, "3B", [
        ("llama3.2:1b", "Fast CPU inference"),
        ("phi3:mini", "Optimized for CPU"),
    ]),
    (16, "7B", [
        ("llama3.2:3b", "Good CPU performance"),
        ("qwen2.5:3b", "Efficient inference"),
    ]),
    (32, "7B", [
        ("qwen2.5-coder:7b", "Usable on high-RAM systems"),
        ("mistral:7b", "Acceptable CPU performance"),
    ]),
]


async def _run_command(cmd: List[str]) -> Optional[str]:
    """Run a command and return stdout, or None on failure.

    Uses asyncio.create_subprocess_exec for safe execution (no shell injection).
    """
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await process.communicate()
        if process.returncode == 0:
            return stdout.decode("utf-8", errors="replace")
        return None
    except FileNotFoundError:
        return None
    except Exception as e:
        logger.debug(f"Command {cmd} failed: {e}")
        return None


def _parse_nvidia_smi(output: str) -> GPUInfo:
    """Parse nvidia-smi output to extract GPU information."""
    gpu_info = GPUInfo(detected=True, vendor="nvidia")

    # Parse nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader
    # Example output: "NVIDIA GeForce RTX 3080, 10240 MiB, 8500 MiB"
    lines = output.strip().split("\n")
    if lines:
        parts = lines[0].split(",")
        if len(parts) >= 1:
            gpu_info.name = parts[0].strip()

        # Parse memory (in MiB from nvidia-smi)
        if len(parts) >= 2:
            mem_total = parts[1].strip()
            mem_match = re.match(r"(\d+)\s*MiB", mem_total)
            if mem_match:
                gpu_info.vram_total_gb = int(mem_match.group(1)) / 1024

        if len(parts) >= 3:
            mem_free = parts[2].strip()
            mem_match = re.match(r"(\d+)\s*MiB", mem_free)
            if mem_match:
                gpu_info.vram_available_gb = int(mem_match.group(1)) / 1024

    return gpu_info


async def _detect_nvidia_gpu() -> Optional[GPUInfo]:
    """Detect NVIDIA GPU using nvidia-smi."""
    output = await _run_command([
        "nvidia-smi",
        "--query-gpu=name,memory.total,memory.free",
        "--format=csv,noheader",
    ])

    if output:
        return _parse_nvidia_smi(output)

    return None


async def _detect_amd_gpu() -> Optional[GPUInfo]:
    """Detect AMD GPU using rocm-smi or sysfs."""
    # Try rocm-smi first
    output = await _run_command(["rocm-smi", "--showmeminfo", "vram"])
    if output:
        gpu_info = GPUInfo(detected=True, vendor="amd")

        # Parse VRAM info from rocm-smi output
        total_match = re.search(r"Total Memory.*?:\s*(\d+)", output)
        used_match = re.search(r"Used Memory.*?:\s*(\d+)", output)

        if total_match:
            # rocm-smi reports in bytes
            total_bytes = int(total_match.group(1))
            gpu_info.vram_total_gb = total_bytes / (1024 ** 3)

        if total_match and used_match:
            used_bytes = int(used_match.group(1))
            total_bytes = int(total_match.group(1))
            gpu_info.vram_available_gb = (total_bytes - used_bytes) / (1024 ** 3)

        return gpu_info

    # Fallback: Check sysfs for AMD GPUs
    drm_path = Path("/sys/class/drm")
    if drm_path.exists():
        for card_dir in drm_path.glob("card*/device"):
            vendor_file = card_dir / "vendor"
            if vendor_file.exists():
                try:
                    vendor_id = vendor_file.read_text().strip()
                    # AMD vendor ID is 0x1002
                    if vendor_id == "0x1002":
                        gpu_info = GPUInfo(detected=True, vendor="amd", name="AMD GPU")

                        # Try to get VRAM from mem_info_vram_total
                        vram_file = card_dir / "mem_info_vram_total"
                        if vram_file.exists():
                            vram_bytes = int(vram_file.read_text().strip())
                            gpu_info.vram_total_gb = vram_bytes / (1024 ** 3)

                        vram_used_file = card_dir / "mem_info_vram_used"
                        if vram_used_file.exists() and gpu_info.vram_total_gb:
                            vram_used = int(vram_used_file.read_text().strip())
                            total_bytes = int(vram_file.read_text().strip())
                            gpu_info.vram_available_gb = (total_bytes - vram_used) / (1024 ** 3)

                        return gpu_info
                except (ValueError, IOError):
                    continue

    return None


def _parse_proc_cpuinfo(content: str) -> Optional[Dict[str, Any]]:
    """Parse /proc/cpuinfo content."""
    cpu_info: Dict[str, Any] = {
        "name": "Unknown CPU",
        "cores": 1,
        "threads": 1,
    }

    # Count processors for thread count
    processors = re.findall(r"^processor\s*:\s*\d+", content, re.MULTILINE)
    cpu_info["threads"] = len(processors) if processors else 1

    # Get model name
    model_match = re.search(r"model name\s*:\s*(.+)", content)
    if model_match:
        cpu_info["name"] = model_match.group(1).strip()

    # Get core count (physical cores)
    cores_match = re.search(r"cpu cores\s*:\s*(\d+)", content)
    if cores_match:
        cpu_info["cores"] = int(cores_match.group(1))
    else:
        # Fallback: use thread count
        cpu_info["cores"] = cpu_info["threads"]

    return cpu_info


def _parse_proc_meminfo(content: str) -> Dict[str, float]:
    """Parse /proc/meminfo content."""
    mem_info: Dict[str, float] = {
        "total_gb": 0.0,
        "available_gb": 0.0,
    }

    # MemTotal and MemAvailable are in kB
    total_match = re.search(r"MemTotal:\s*(\d+)\s*kB", content)
    if total_match:
        mem_info["total_gb"] = int(total_match.group(1)) / (1024 * 1024)

    avail_match = re.search(r"MemAvailable:\s*(\d+)\s*kB", content)
    if avail_match:
        mem_info["available_gb"] = int(avail_match.group(1)) / (1024 * 1024)
    else:
        # Fallback: use MemFree if MemAvailable not present
        free_match = re.search(r"MemFree:\s*(\d+)\s*kB", content)
        if free_match:
            mem_info["available_gb"] = int(free_match.group(1)) / (1024 * 1024)

    return mem_info


async def _detect_cpu_and_ram() -> CPUInfo:
    """Detect CPU and RAM information from /proc filesystem."""
    cpu_name = "Unknown CPU"
    cores = 1
    threads = 1
    ram_total = 0.0
    ram_available = 0.0

    # Read /proc/cpuinfo
    cpuinfo_path = Path("/proc/cpuinfo")
    if cpuinfo_path.exists():
        try:
            content = cpuinfo_path.read_text()
            parsed = _parse_proc_cpuinfo(content)
            if parsed:
                cpu_name = parsed["name"]
                cores = parsed["cores"]
                threads = parsed["threads"]
        except IOError as e:
            logger.debug(f"Failed to read /proc/cpuinfo: {e}")

    # Read /proc/meminfo
    meminfo_path = Path("/proc/meminfo")
    if meminfo_path.exists():
        try:
            content = meminfo_path.read_text()
            mem = _parse_proc_meminfo(content)
            ram_total = mem["total_gb"]
            ram_available = mem["available_gb"]
        except IOError as e:
            logger.debug(f"Failed to read /proc/meminfo: {e}")

    return CPUInfo(
        name=cpu_name,
        cores=cores,
        threads=threads,
        ram_total_gb=round(ram_total, 2),
        ram_available_gb=round(ram_available, 2),
    )


def _get_recommendations(gpu: GPUInfo, cpu: CPUInfo) -> Recommendations:
    """Generate model recommendations based on hardware."""
    if gpu.detected and gpu.vram_available_gb is not None:
        # GPU-based recommendations
        vram = gpu.vram_available_gb
        inference_mode = "GPU"

        # Find the appropriate recommendation tier
        max_params = "3B"
        models: List[tuple] = _VRAM_RECOMMENDATIONS[0][2]

        for min_vram, params, model_list in _VRAM_RECOMMENDATIONS:
            if vram >= min_vram:
                max_params = params
                models = model_list

        recommendations = [
            ModelRecommendation(name=name, reason=reason)
            for name, reason in models
        ]

        return Recommendations(
            max_model_params=max_params,
            recommended_models=recommendations,
            inference_mode=inference_mode,
        )
    else:
        # CPU-only recommendations
        ram = cpu.ram_available_gb
        inference_mode = "CPU"

        max_params = "1B"
        models = _CPU_RECOMMENDATIONS[0][2]

        for min_ram, params, model_list in _CPU_RECOMMENDATIONS:
            if ram >= min_ram:
                max_params = params
                models = model_list

        recommendations = [
            ModelRecommendation(name=name, reason=reason)
            for name, reason in models
        ]

        return Recommendations(
            max_model_params=max_params,
            recommended_models=recommendations,
            inference_mode=inference_mode,
        )


async def detect_hardware() -> HardwareInfo:
    """Detect system hardware and generate recommendations.

    Returns:
        HardwareInfo with GPU, CPU, and model recommendations.
    """
    # Try to detect GPU (NVIDIA first, then AMD)
    gpu = await _detect_nvidia_gpu()
    if not gpu:
        gpu = await _detect_amd_gpu()
    if not gpu:
        gpu = GPUInfo(detected=False)

    # Detect CPU and RAM
    cpu = await _detect_cpu_and_ram()

    # Generate recommendations
    recommendations = _get_recommendations(gpu, cpu)

    return HardwareInfo(
        gpu=gpu,
        cpu=cpu,
        recommendations=recommendations,
    )


# Export for convenience
__all__ = [
    "GPUInfo",
    "CPUInfo",
    "ModelRecommendation",
    "Recommendations",
    "HardwareInfo",
    "detect_hardware",
]
