"""Unit tests for the hardware detection service."""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from pathlib import Path

from app.services.hardware_service import (
    GPUInfo,
    CPUInfo,
    ModelRecommendation,
    Recommendations,
    HardwareInfo,
    detect_hardware,
    _parse_nvidia_smi,
    _parse_proc_cpuinfo,
    _parse_proc_meminfo,
    _get_recommendations,
    _run_command,
    _detect_nvidia_gpu,
    _detect_amd_gpu,
    _detect_cpu_and_ram,
)


class TestGPUInfo:
    """Tests for GPUInfo dataclass."""

    def test_gpu_info_detected(self):
        """Test GPUInfo with detected GPU."""
        gpu = GPUInfo(
            detected=True,
            name="NVIDIA GeForce RTX 3080",
            vendor="nvidia",
            vram_total_gb=10.0,
            vram_available_gb=8.5,
        )
        assert gpu.detected is True
        assert gpu.name == "NVIDIA GeForce RTX 3080"
        assert gpu.vendor == "nvidia"
        assert gpu.vram_total_gb == 10.0
        assert gpu.vram_available_gb == 8.5

    def test_gpu_info_not_detected(self):
        """Test GPUInfo when no GPU is detected."""
        gpu = GPUInfo(detected=False)
        assert gpu.detected is False
        assert gpu.name is None
        assert gpu.vendor is None
        assert gpu.vram_total_gb is None
        assert gpu.vram_available_gb is None


class TestCPUInfo:
    """Tests for CPUInfo dataclass."""

    def test_cpu_info(self):
        """Test CPUInfo dataclass."""
        cpu = CPUInfo(
            name="AMD Ryzen 9 5900X",
            cores=12,
            threads=24,
            ram_total_gb=32.0,
            ram_available_gb=24.5,
        )
        assert cpu.name == "AMD Ryzen 9 5900X"
        assert cpu.cores == 12
        assert cpu.threads == 24
        assert cpu.ram_total_gb == 32.0
        assert cpu.ram_available_gb == 24.5


class TestParseNvidiaSmi:
    """Tests for nvidia-smi output parsing."""

    def test_parse_nvidia_smi_standard_output(self):
        """Test parsing standard nvidia-smi output."""
        output = "NVIDIA GeForce RTX 3080, 10240 MiB, 8500 MiB"
        gpu = _parse_nvidia_smi(output)

        assert gpu.detected is True
        assert gpu.vendor == "nvidia"
        assert gpu.name == "NVIDIA GeForce RTX 3080"
        assert gpu.vram_total_gb == pytest.approx(10.0, rel=0.01)
        assert gpu.vram_available_gb == pytest.approx(8.3, rel=0.1)

    def test_parse_nvidia_smi_multi_gpu(self):
        """Test parsing nvidia-smi with multiple GPUs (uses first)."""
        output = """NVIDIA GeForce RTX 3090, 24576 MiB, 20000 MiB
NVIDIA GeForce RTX 3080, 10240 MiB, 8500 MiB"""
        gpu = _parse_nvidia_smi(output)

        assert gpu.detected is True
        assert gpu.name == "NVIDIA GeForce RTX 3090"
        assert gpu.vram_total_gb == pytest.approx(24.0, rel=0.01)

    def test_parse_nvidia_smi_partial_output(self):
        """Test parsing nvidia-smi with only name."""
        output = "NVIDIA GeForce GTX 1080"
        gpu = _parse_nvidia_smi(output)

        assert gpu.detected is True
        assert gpu.name == "NVIDIA GeForce GTX 1080"
        assert gpu.vram_total_gb is None


class TestParseProcCpuinfo:
    """Tests for /proc/cpuinfo parsing."""

    def test_parse_proc_cpuinfo_standard(self):
        """Test parsing standard /proc/cpuinfo."""
        content = """processor	: 0
vendor_id	: GenuineIntel
cpu family	: 6
model name	: Intel(R) Core(TM) i7-10700K CPU @ 3.80GHz
cpu cores	: 8

processor	: 1
vendor_id	: GenuineIntel
cpu family	: 6
model name	: Intel(R) Core(TM) i7-10700K CPU @ 3.80GHz
cpu cores	: 8
"""
        result = _parse_proc_cpuinfo(content)

        assert result["name"] == "Intel(R) Core(TM) i7-10700K CPU @ 3.80GHz"
        assert result["cores"] == 8
        assert result["threads"] == 2

    def test_parse_proc_cpuinfo_amd(self):
        """Test parsing AMD CPU info."""
        content = """processor	: 0
model name	: AMD Ryzen 9 5900X 12-Core Processor
cpu cores	: 12

processor	: 1
model name	: AMD Ryzen 9 5900X 12-Core Processor
cpu cores	: 12
"""
        result = _parse_proc_cpuinfo(content)

        assert result["name"] == "AMD Ryzen 9 5900X 12-Core Processor"
        assert result["cores"] == 12
        assert result["threads"] == 2

    def test_parse_proc_cpuinfo_no_cores(self):
        """Test parsing with missing cpu cores field."""
        content = """processor	: 0
model name	: Some CPU

processor	: 1
model name	: Some CPU

processor	: 2
model name	: Some CPU

processor	: 3
model name	: Some CPU
"""
        result = _parse_proc_cpuinfo(content)

        assert result["name"] == "Some CPU"
        assert result["cores"] == 4  # Falls back to thread count
        assert result["threads"] == 4


class TestParseProcMeminfo:
    """Tests for /proc/meminfo parsing."""

    def test_parse_proc_meminfo_standard(self):
        """Test parsing standard /proc/meminfo."""
        content = """MemTotal:       32870912 kB
MemFree:         1234567 kB
MemAvailable:   25165824 kB
Buffers:          123456 kB
Cached:          5678901 kB
"""
        result = _parse_proc_meminfo(content)

        assert result["total_gb"] == pytest.approx(31.35, rel=0.01)
        assert result["available_gb"] == pytest.approx(24.0, rel=0.01)

    def test_parse_proc_meminfo_no_available(self):
        """Test parsing when MemAvailable is missing (old kernels)."""
        content = """MemTotal:       16777216 kB
MemFree:         8388608 kB
Buffers:          123456 kB
"""
        result = _parse_proc_meminfo(content)

        assert result["total_gb"] == pytest.approx(16.0, rel=0.01)
        assert result["available_gb"] == pytest.approx(8.0, rel=0.01)

    def test_parse_proc_meminfo_empty(self):
        """Test parsing empty meminfo."""
        content = ""
        result = _parse_proc_meminfo(content)

        assert result["total_gb"] == 0.0
        assert result["available_gb"] == 0.0


class TestGetRecommendations:
    """Tests for model recommendation logic."""

    def test_recommendations_low_vram(self):
        """Test recommendations for low VRAM (< 4GB)."""
        gpu = GPUInfo(detected=True, vendor="nvidia", vram_available_gb=3.0)
        cpu = CPUInfo(name="CPU", cores=4, threads=8, ram_total_gb=16.0, ram_available_gb=12.0)

        recs = _get_recommendations(gpu, cpu)

        assert recs.inference_mode == "GPU"
        assert recs.max_model_params == "3B"
        assert any("llama3.2:1b" in m.name for m in recs.recommended_models)

    def test_recommendations_medium_vram(self):
        """Test recommendations for medium VRAM (8-12GB)."""
        gpu = GPUInfo(detected=True, vendor="nvidia", vram_available_gb=10.0)
        cpu = CPUInfo(name="CPU", cores=4, threads=8, ram_total_gb=16.0, ram_available_gb=12.0)

        recs = _get_recommendations(gpu, cpu)

        assert recs.inference_mode == "GPU"
        assert recs.max_model_params == "13B"
        assert any("llama3.1:8b" in m.name for m in recs.recommended_models)

    def test_recommendations_high_vram(self):
        """Test recommendations for high VRAM (24+ GB)."""
        gpu = GPUInfo(detected=True, vendor="nvidia", vram_available_gb=24.0)
        cpu = CPUInfo(name="CPU", cores=4, threads=8, ram_total_gb=32.0, ram_available_gb=24.0)

        recs = _get_recommendations(gpu, cpu)

        assert recs.inference_mode == "GPU"
        assert recs.max_model_params == "70B"
        assert any("llama3.1:70b" in m.name for m in recs.recommended_models)

    def test_recommendations_no_gpu(self):
        """Test recommendations when no GPU is detected."""
        gpu = GPUInfo(detected=False)
        cpu = CPUInfo(name="CPU", cores=8, threads=16, ram_total_gb=32.0, ram_available_gb=28.0)

        recs = _get_recommendations(gpu, cpu)

        assert recs.inference_mode == "CPU"
        assert any("llama3.2" in m.name or "qwen2.5" in m.name for m in recs.recommended_models)

    def test_recommendations_gpu_no_vram_info(self):
        """Test recommendations when GPU is detected but VRAM info is missing."""
        gpu = GPUInfo(detected=True, vendor="nvidia", vram_available_gb=None)
        cpu = CPUInfo(name="CPU", cores=4, threads=8, ram_total_gb=16.0, ram_available_gb=12.0)

        recs = _get_recommendations(gpu, cpu)

        # Should fall back to CPU mode
        assert recs.inference_mode == "CPU"

    def test_recommendations_low_ram_cpu_only(self):
        """Test CPU recommendations with low RAM."""
        gpu = GPUInfo(detected=False)
        cpu = CPUInfo(name="CPU", cores=4, threads=8, ram_total_gb=4.0, ram_available_gb=2.0)

        recs = _get_recommendations(gpu, cpu)

        assert recs.inference_mode == "CPU"
        assert recs.max_model_params == "1B"


class TestRunCommand:
    """Tests for command execution helper."""

    @pytest.mark.asyncio
    async def test_run_command_success(self):
        """Test successful command execution."""
        with patch("asyncio.create_subprocess_exec") as mock_exec:
            mock_process = MagicMock()
            mock_process.communicate = AsyncMock(return_value=(b"output", b""))
            mock_process.returncode = 0
            mock_exec.return_value = mock_process

            result = await _run_command(["echo", "test"])

            assert result == "output"

    @pytest.mark.asyncio
    async def test_run_command_failure(self):
        """Test command execution failure."""
        with patch("asyncio.create_subprocess_exec") as mock_exec:
            mock_process = MagicMock()
            mock_process.communicate = AsyncMock(return_value=(b"", b"error"))
            mock_process.returncode = 1
            mock_exec.return_value = mock_process

            result = await _run_command(["false"])

            assert result is None

    @pytest.mark.asyncio
    async def test_run_command_not_found(self):
        """Test command not found."""
        with patch("asyncio.create_subprocess_exec", side_effect=FileNotFoundError):
            result = await _run_command(["nonexistent-command"])

            assert result is None


class TestDetectNvidiaGpu:
    """Tests for NVIDIA GPU detection."""

    @pytest.mark.asyncio
    async def test_detect_nvidia_gpu_present(self):
        """Test detection when NVIDIA GPU is present."""
        nvidia_output = "NVIDIA GeForce RTX 4090, 24576 MiB, 20000 MiB"

        with patch("app.services.hardware_service._run_command", new_callable=AsyncMock) as mock_cmd:
            mock_cmd.return_value = nvidia_output

            gpu = await _detect_nvidia_gpu()

            assert gpu is not None
            assert gpu.detected is True
            assert gpu.vendor == "nvidia"
            assert "RTX 4090" in gpu.name

    @pytest.mark.asyncio
    async def test_detect_nvidia_gpu_not_present(self):
        """Test detection when NVIDIA GPU is not present."""
        with patch("app.services.hardware_service._run_command", new_callable=AsyncMock) as mock_cmd:
            mock_cmd.return_value = None

            gpu = await _detect_nvidia_gpu()

            assert gpu is None


class TestDetectAmdGpu:
    """Tests for AMD GPU detection."""

    @pytest.mark.asyncio
    async def test_detect_amd_gpu_with_rocm(self):
        """Test AMD GPU detection with rocm-smi."""
        rocm_output = """
GPU Memory Info:
Total Memory: 17179869184
Used Memory: 1073741824
"""
        with patch("app.services.hardware_service._run_command", new_callable=AsyncMock) as mock_cmd:
            mock_cmd.return_value = rocm_output

            gpu = await _detect_amd_gpu()

            assert gpu is not None
            assert gpu.detected is True
            assert gpu.vendor == "amd"

    @pytest.mark.asyncio
    async def test_detect_amd_gpu_not_present(self):
        """Test AMD GPU detection when not present."""
        with patch("app.services.hardware_service._run_command", new_callable=AsyncMock) as mock_cmd:
            mock_cmd.return_value = None
            with patch("pathlib.Path.exists", return_value=False):
                gpu = await _detect_amd_gpu()

                assert gpu is None


class TestDetectCpuAndRam:
    """Tests for CPU and RAM detection."""

    @pytest.mark.asyncio
    async def test_detect_cpu_and_ram(self):
        """Test CPU and RAM detection from /proc."""
        cpuinfo_content = """processor	: 0
model name	: Intel Core i9-12900K
cpu cores	: 16

processor	: 1
model name	: Intel Core i9-12900K
cpu cores	: 16
"""
        meminfo_content = """MemTotal:       65536000 kB
MemAvailable:   52428800 kB
"""
        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.read_text") as mock_read:
                mock_read.side_effect = [cpuinfo_content, meminfo_content]

                cpu = await _detect_cpu_and_ram()

                assert cpu.name == "Intel Core i9-12900K"
                assert cpu.cores == 16
                assert cpu.threads == 2
                assert cpu.ram_total_gb == pytest.approx(62.5, rel=0.01)
                assert cpu.ram_available_gb == pytest.approx(50.0, rel=0.01)

    @pytest.mark.asyncio
    async def test_detect_cpu_and_ram_missing_files(self):
        """Test fallback when /proc files don't exist."""
        with patch("pathlib.Path.exists", return_value=False):
            cpu = await _detect_cpu_and_ram()

            assert cpu.name == "Unknown CPU"
            assert cpu.cores == 1
            assert cpu.threads == 1
            assert cpu.ram_total_gb == 0.0


class TestDetectHardware:
    """Integration tests for detect_hardware function."""

    @pytest.mark.asyncio
    async def test_detect_hardware_with_nvidia(self):
        """Test full hardware detection with NVIDIA GPU."""
        nvidia_output = "NVIDIA GeForce RTX 3080, 10240 MiB, 8500 MiB"
        cpuinfo = "processor\t: 0\nmodel name\t: AMD Ryzen 9 5900X\ncpu cores\t: 12\n"
        meminfo = "MemTotal:\t32870912 kB\nMemAvailable:\t25165824 kB\n"

        with patch("app.services.hardware_service._run_command", new_callable=AsyncMock) as mock_cmd:
            # nvidia-smi succeeds, rocm-smi would fail
            mock_cmd.return_value = nvidia_output

            with patch("pathlib.Path.exists", return_value=True):
                with patch("pathlib.Path.read_text") as mock_read:
                    mock_read.side_effect = [cpuinfo, meminfo]

                    hardware = await detect_hardware()

                    assert hardware.gpu.detected is True
                    assert hardware.gpu.vendor == "nvidia"
                    assert hardware.cpu.name == "AMD Ryzen 9 5900X"
                    assert hardware.recommendations.inference_mode == "GPU"

    @pytest.mark.asyncio
    async def test_detect_hardware_no_gpu(self):
        """Test hardware detection without GPU."""
        cpuinfo = "processor\t: 0\nmodel name\t: Intel Core i5-10400\ncpu cores\t: 6\n"
        meminfo = "MemTotal:\t16777216 kB\nMemAvailable:\t12582912 kB\n"

        with patch("app.services.hardware_service._run_command", new_callable=AsyncMock) as mock_cmd:
            # Both nvidia-smi and rocm-smi fail
            mock_cmd.return_value = None

            with patch("pathlib.Path.exists") as mock_exists:
                # /proc files exist, but /sys/class/drm doesn't have AMD GPU
                def exists_side_effect(self=None):
                    path_str = str(self) if hasattr(self, '__str__') else ""
                    return "/proc" in path_str

                mock_exists.side_effect = lambda: True
                with patch("pathlib.Path.read_text") as mock_read:
                    mock_read.side_effect = [cpuinfo, meminfo]
                    with patch("pathlib.Path.glob", return_value=[]):
                        hardware = await detect_hardware()

                        assert hardware.gpu.detected is False
                        assert hardware.cpu.name == "Intel Core i5-10400"
                        assert hardware.recommendations.inference_mode == "CPU"


class TestHardwareInfoStructure:
    """Tests for HardwareInfo dataclass structure."""

    def test_hardware_info_structure(self):
        """Test HardwareInfo dataclass has all expected fields."""
        gpu = GPUInfo(detected=True, name="Test GPU", vendor="nvidia", vram_total_gb=8.0, vram_available_gb=6.0)
        cpu = CPUInfo(name="Test CPU", cores=4, threads=8, ram_total_gb=16.0, ram_available_gb=12.0)
        recommendations = Recommendations(
            max_model_params="7B",
            recommended_models=[ModelRecommendation(name="test:model", reason="Test")],
            inference_mode="GPU",
        )

        hardware = HardwareInfo(gpu=gpu, cpu=cpu, recommendations=recommendations)

        assert hardware.gpu == gpu
        assert hardware.cpu == cpu
        assert hardware.recommendations == recommendations
        assert hardware.recommendations.recommended_models[0].name == "test:model"
