"""Report generation service using LLM."""

import logging
import re
import time
from typing import Optional, List, Dict, Any, Tuple
from uuid import uuid4
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.report import Report
from app.schemas.report import ReportType
from app.services.llm import get_llm_provider, get_embedding_provider, get_vector_service
from app.services.llm.base import ChatMessage

logger = logging.getLogger(__name__)


# Report generation prompts
ARCHITECTURE_REPORT_PROMPT = """You are a senior software architect analyzing a codebase. Generate a comprehensive architecture report based on the following project data.

## Project Information
- **Name:** {project_name}
- **Description:** {description}
- **Total Files:** {files}
- **Total Lines of Code:** {lines_of_code}
- **Directories:** {directories}

## Language Breakdown
{language_breakdown}

## Key Entry Points and Files
{key_files}

## Sample Code Context
{code_context}

---

Generate a detailed architecture report with the following sections. Use markdown formatting.

## 1. Executive Summary
Provide a brief overview of the codebase (2-3 paragraphs). Include the primary purpose, tech stack, and overall architecture pattern.

## 2. Technology Stack
List all detected technologies, frameworks, and languages with their roles in the project.

## 3. Architecture Pattern
Identify and describe the architecture pattern(s) used (e.g., MVC, microservices, monolith, layered, etc.). Explain how the code is organized.

## 4. Key Components
Describe the main modules/packages and their responsibilities. Reference specific directories and files.

## 5. Data Flow
Explain how data flows through the application. Identify entry points and key processing paths.

## 6. Dependencies
Summarize external dependencies and internal module relationships.

## 7. Recommendations
Provide 2-3 actionable recommendations for improving the codebase architecture.

---

IMPORTANT:
- Reference actual file paths from the project data
- Be specific and factual - only describe what you can observe
- Do not fabricate features or files that don't exist
- Format file references as `path/to/file.ext:line` where applicable"""


SUMMARY_REPORT_PROMPT = """You are a technical writer creating a project summary. Generate a concise summary report based on the following project data.

## Project Information
- **Name:** {project_name}
- **Description:** {description}
- **Total Files:** {files}
- **Total Lines of Code:** {lines_of_code}
- **Directories:** {directories}

## Language Breakdown
{language_breakdown}

---

Generate a project summary with the following sections. Use markdown formatting.

## 1. Overview
Brief description of what this project does (1-2 paragraphs).

## 2. Quick Stats
Key metrics in a table format.

## 3. Getting Started
Inferred setup instructions based on the detected technologies.

## 4. Project Structure
Brief overview of the directory structure and organization.

---

Be concise and factual. Only describe what you can observe from the data."""


DEPENDENCIES_REPORT_PROMPT = """You are a software architect analyzing project dependencies. Generate a dependency analysis report based on the following project data.

## Project Information
- **Name:** {project_name}
- **Total Files:** {files}
- **Lines of Code:** {lines_of_code}

## Language Breakdown
{language_breakdown}

## Internal Module Dependencies
{dependency_data}

---

Generate a dependency analysis report with the following sections. Use markdown formatting.

## 1. Overview
Summary of the dependency structure.

## 2. External Dependencies
List detected package managers and external libraries.

## 3. Internal Dependencies
Describe how internal modules depend on each other.

## 4. Dependency Graph Summary
Summarize the module dependency graph (nodes, edges, depth).

## 5. Potential Issues
Identify any potential dependency issues:
- Circular dependencies
- High coupling
- Unused imports

## 6. Recommendations
Suggestions for improving dependency management.

---

Be factual and reference actual data from the analysis."""


class ReportGenerator:
    """Service for generating analysis reports using LLM."""

    def __init__(self, db: Session):
        """Initialize report generator with database session."""
        self.db = db
        self._llm_provider = None
        self._embedding_provider = None
        self._vector_service = None

    @property
    def llm_provider(self):
        """Lazy load LLM provider."""
        if self._llm_provider is None:
            self._llm_provider = get_llm_provider()
        return self._llm_provider

    @property
    def embedding_provider(self):
        """Lazy load embedding provider."""
        if self._embedding_provider is None:
            self._embedding_provider = get_embedding_provider()
        return self._embedding_provider

    @property
    def vector_service(self):
        """Lazy load vector service."""
        if self._vector_service is None:
            self._vector_service = get_vector_service()
        return self._vector_service

    async def generate_report(
        self,
        project_id: str,
        report_type: ReportType,
        force: bool = False,
    ) -> Report:
        """
        Generate a report for a project.

        Args:
            project_id: Project ID
            report_type: Type of report to generate
            force: Regenerate even if report exists

        Returns:
            Generated Report object

        Raises:
            ValueError: If project not found
            RuntimeError: If LLM unavailable
        """
        # Load project
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError(f"Project not found: {project_id}")

        if project.status.value != "ready":
            raise ValueError(f"Project is not ready for report generation: {project.status}")

        # Check for existing report
        if not force:
            existing = self.db.query(Report).filter(
                Report.project_id == project_id,
                Report.type == report_type.value,
            ).first()
            if existing:
                logger.info(f"Returning existing {report_type.value} report for project {project_id}")
                return existing

        # Check LLM availability
        if not await self.llm_provider.health_check():
            raise RuntimeError("LLM provider is not available")

        # Generate based on report type
        if report_type == ReportType.architecture:
            return await self._generate_architecture_report(project)
        elif report_type == ReportType.summary:
            return await self._generate_summary_report(project)
        elif report_type == ReportType.dependencies:
            return await self._generate_dependencies_report(project)
        else:
            raise ValueError(f"Unsupported report type: {report_type}")

    async def _generate_architecture_report(self, project: Project) -> Report:
        """Generate architecture report."""
        start_time = time.time()
        logger.info(f"Generating architecture report for project {project.id}")

        # Build context
        prompt = await self._build_architecture_prompt(project)

        # Generate with LLM
        messages = [
            ChatMessage(role="system", content="You are a senior software architect."),
            ChatMessage(role="user", content=prompt),
        ]

        result = await self.llm_provider.chat(messages, temperature=0.3, max_tokens=2000)

        # Parse into sections
        content = result.content
        sections = self._parse_sections(content)

        # Extract metadata
        metadata = self._extract_metadata(project, content)

        # Calculate generation time
        generation_time_ms = int((time.time() - start_time) * 1000)

        # Create or update report
        report = self._save_report(
            project_id=project.id,
            report_type=ReportType.architecture,
            title="Architecture Overview",
            content=content,
            sections=sections,
            metadata=metadata,
            model_used=result.model,
            generation_time_ms=generation_time_ms,
        )

        logger.info(f"Generated architecture report in {generation_time_ms}ms")
        return report

    async def _generate_summary_report(self, project: Project) -> Report:
        """Generate summary report."""
        start_time = time.time()
        logger.info(f"Generating summary report for project {project.id}")

        # Build prompt
        prompt = self._build_summary_prompt(project)

        # Generate with LLM
        messages = [
            ChatMessage(role="system", content="You are a technical writer."),
            ChatMessage(role="user", content=prompt),
        ]

        result = await self.llm_provider.chat(messages, temperature=0.3, max_tokens=1500)

        # Parse into sections
        content = result.content
        sections = self._parse_sections(content)

        # Calculate generation time
        generation_time_ms = int((time.time() - start_time) * 1000)

        # Create or update report
        report = self._save_report(
            project_id=project.id,
            report_type=ReportType.summary,
            title="Project Summary",
            content=content,
            sections=sections,
            metadata={"languages": list(project.stats.get("languages", {}).keys())},
            model_used=result.model,
            generation_time_ms=generation_time_ms,
        )

        logger.info(f"Generated summary report in {generation_time_ms}ms")
        return report

    async def _generate_dependencies_report(self, project: Project) -> Report:
        """Generate dependencies report."""
        start_time = time.time()
        logger.info(f"Generating dependencies report for project {project.id}")

        # Build prompt
        prompt = self._build_dependencies_prompt(project)

        # Generate with LLM
        messages = [
            ChatMessage(role="system", content="You are a software architect analyzing dependencies."),
            ChatMessage(role="user", content=prompt),
        ]

        result = await self.llm_provider.chat(messages, temperature=0.3, max_tokens=1500)

        # Parse into sections
        content = result.content
        sections = self._parse_sections(content)

        # Calculate generation time
        generation_time_ms = int((time.time() - start_time) * 1000)

        # Create or update report
        report = self._save_report(
            project_id=project.id,
            report_type=ReportType.dependencies,
            title="Dependency Analysis",
            content=content,
            sections=sections,
            metadata={"languages": list(project.stats.get("languages", {}).keys())},
            model_used=result.model,
            generation_time_ms=generation_time_ms,
        )

        logger.info(f"Generated dependencies report in {generation_time_ms}ms")
        return report

    async def _build_architecture_prompt(self, project: Project) -> str:
        """Build prompt for architecture report."""
        stats = project.stats or {}

        # Format language breakdown
        languages = stats.get("languages", {})
        if languages:
            lang_lines = []
            for lang, data in languages.items():
                if isinstance(data, dict):
                    files = data.get("files", 0)
                    lines = data.get("lines", 0)
                    lang_lines.append(f"- **{lang}:** {files} files, {lines} lines")
                else:
                    lang_lines.append(f"- **{lang}:** {data} files")
            language_breakdown = "\n".join(lang_lines)
        else:
            language_breakdown = "No language breakdown available"

        # Get key files from code chunks (entry points, main files)
        key_files = await self._get_key_files(project.id)

        # Get sample code context using RAG
        code_context = await self._get_code_context(
            project.id,
            "main entry point application architecture initialization"
        )

        return ARCHITECTURE_REPORT_PROMPT.format(
            project_name=project.name,
            description=project.description or "No description provided",
            files=stats.get("files", 0),
            lines_of_code=stats.get("lines_of_code", 0),
            directories=stats.get("directories", 0),
            language_breakdown=language_breakdown,
            key_files=key_files or "No key files identified",
            code_context=code_context or "No code context available",
        )

    def _build_summary_prompt(self, project: Project) -> str:
        """Build prompt for summary report."""
        stats = project.stats or {}

        # Format language breakdown
        languages = stats.get("languages", {})
        if languages:
            lang_lines = []
            for lang, data in languages.items():
                if isinstance(data, dict):
                    files = data.get("files", 0)
                    lang_lines.append(f"- **{lang}:** {files} files")
                else:
                    lang_lines.append(f"- **{lang}:** {data} files")
            language_breakdown = "\n".join(lang_lines)
        else:
            language_breakdown = "No language breakdown available"

        return SUMMARY_REPORT_PROMPT.format(
            project_name=project.name,
            description=project.description or "No description provided",
            files=stats.get("files", 0),
            lines_of_code=stats.get("lines_of_code", 0),
            directories=stats.get("directories", 0),
            language_breakdown=language_breakdown,
        )

    def _build_dependencies_prompt(self, project: Project) -> str:
        """Build prompt for dependencies report."""
        stats = project.stats or {}

        # Format language breakdown
        languages = stats.get("languages", {})
        if languages:
            lang_lines = []
            for lang, data in languages.items():
                if isinstance(data, dict):
                    files = data.get("files", 0)
                    lang_lines.append(f"- **{lang}:** {files} files")
                else:
                    lang_lines.append(f"- **{lang}:** {data} files")
            language_breakdown = "\n".join(lang_lines)
        else:
            language_breakdown = "No language breakdown available"

        # Get dependency data if available
        dependency_data = "Dependency graph data not available"
        if "dependency_graph" in stats:
            dg = stats["dependency_graph"]
            dependency_data = f"""
- **Modules:** {dg.get('nodes', 0)}
- **Dependencies:** {dg.get('edges', 0)}
- **Max Depth:** {dg.get('max_depth', 'unknown')}
"""

        return DEPENDENCIES_REPORT_PROMPT.format(
            project_name=project.name,
            files=stats.get("files", 0),
            lines_of_code=stats.get("lines_of_code", 0),
            language_breakdown=language_breakdown,
            dependency_data=dependency_data,
        )

    async def _get_key_files(self, project_id: str) -> str:
        """Get key files from vector database."""
        try:
            from app.models.code_chunk import CodeChunk

            # Query for important files (main, app, index, etc.)
            chunks = self.db.query(CodeChunk).filter(
                CodeChunk.project_id == project_id,
                CodeChunk.chunk_type.in_(["file", "function", "class"]),
            ).limit(10).all()

            if not chunks:
                return "No key files identified"

            files = set()
            for chunk in chunks:
                files.add(chunk.file_path)

            return "\n".join([f"- `{f}`" for f in sorted(files)[:10]])
        except Exception as e:
            logger.warning(f"Error getting key files: {e}")
            return "Unable to retrieve key files"

    async def _get_code_context(self, project_id: str, query: str) -> str:
        """Get relevant code context using vector search."""
        try:
            # Check if services are available
            embedding_healthy = await self.embedding_provider.health_check()
            vector_healthy = await self.vector_service.health_check()

            if not embedding_healthy or not vector_healthy:
                return "Vector search not available"

            # Generate query embedding
            query_embedding = await self.embedding_provider.embed_single(query)

            # Search for relevant chunks
            chunks = await self.vector_service.search(
                query_vector=query_embedding,
                project_id=project_id,
                limit=3,
            )

            if not chunks:
                return "No relevant code found"

            # Format context
            context_parts = []
            for chunk in chunks:
                context_parts.append(f"### `{chunk.file_path}` (lines {chunk.line_start}-{chunk.line_end})")
                content = chunk.content[:500] + "..." if len(chunk.content) > 500 else chunk.content
                context_parts.append(f"```\n{content}\n```\n")

            return "\n".join(context_parts)
        except Exception as e:
            logger.warning(f"Error getting code context: {e}")
            return "Unable to retrieve code context"

    def _parse_sections(self, content: str) -> List[Dict[str, str]]:
        """Parse markdown content into sections."""
        sections = []

        # Split by ## headers
        pattern = r'^## (\d+\.?\s*)?(.+?)$'
        lines = content.split('\n')

        current_section = None
        current_content = []

        for line in lines:
            match = re.match(pattern, line)
            if match:
                # Save previous section
                if current_section:
                    sections.append({
                        "id": self._slugify(current_section),
                        "title": current_section,
                        "content": '\n'.join(current_content).strip(),
                    })

                # Start new section
                current_section = match.group(2).strip()
                current_content = []
            elif current_section:
                current_content.append(line)

        # Save last section
        if current_section:
            sections.append({
                "id": self._slugify(current_section),
                "title": current_section,
                "content": '\n'.join(current_content).strip(),
            })

        return sections

    def _slugify(self, text: str) -> str:
        """Convert text to slug."""
        return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')

    def _extract_metadata(self, project: Project, content: str) -> Dict[str, Any]:
        """Extract metadata from project and generated content."""
        stats = project.stats or {}
        languages = list(stats.get("languages", {}).keys())

        # Try to detect frameworks from content
        frameworks = []
        framework_keywords = ["fastapi", "react", "vue", "django", "flask", "express", "nextjs", "angular"]
        content_lower = content.lower()
        for fw in framework_keywords:
            if fw in content_lower:
                frameworks.append(fw)

        # Try to detect patterns
        patterns = []
        pattern_keywords = ["mvc", "repository", "factory", "singleton", "microservice", "monolith", "layered"]
        for p in pattern_keywords:
            if p in content_lower:
                patterns.append(p)

        return {
            "languages": languages,
            "frameworks": frameworks,
            "patterns_detected": patterns,
        }

    def _save_report(
        self,
        project_id: str,
        report_type: ReportType,
        title: str,
        content: str,
        sections: List[Dict[str, str]],
        metadata: Dict[str, Any],
        model_used: str,
        generation_time_ms: int,
    ) -> Report:
        """Save or update report in database."""
        # Check for existing report
        existing = self.db.query(Report).filter(
            Report.project_id == project_id,
            Report.type == report_type.value,
        ).first()

        if existing:
            # Update existing
            existing.title = title
            existing.content = content
            existing.sections = sections
            existing.report_metadata = metadata
            existing.model_used = model_used
            existing.generation_time_ms = str(generation_time_ms)
            existing.updated_at = datetime.utcnow()
            self.db.commit()
            return existing
        else:
            # Create new
            report = Report(
                id=str(uuid4()),
                project_id=project_id,
                type=report_type.value,
                title=title,
                content=content,
                sections=sections,
                report_metadata=metadata,
                model_used=model_used,
                generation_time_ms=str(generation_time_ms),
            )
            self.db.add(report)
            self.db.commit()
            return report

    async def generate_all_reports(self, project_id: str, force: bool = False) -> List[Report]:
        """Generate all report types for a project."""
        reports = []
        for report_type in [ReportType.summary, ReportType.architecture, ReportType.dependencies]:
            try:
                report = await self.generate_report(project_id, report_type, force=force)
                reports.append(report)
            except Exception as e:
                logger.error(f"Error generating {report_type.value} report: {e}")

        return reports
