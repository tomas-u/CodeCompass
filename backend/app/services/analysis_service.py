"""Real code analysis service using Tree-sitter."""

import asyncio
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

from app.database import SessionLocal
from app.models.project import Project
from app.schemas.project import ProjectStatus, SourceType
from app.services.git_service import GitService
from app.services.analyzer.generic_analyzer import GenericAnalyzer
from app.services.chunking_service import ChunkingService
from app.services.llm import get_embedding_provider, get_vector_service
from app.config import settings

logger = logging.getLogger(__name__)


async def _debug_delay(phase: str) -> None:
    """Add debug delay between analysis phases if configured."""
    if settings.debug_analysis_delay > 0:
        logger.debug(f"Debug delay: waiting {settings.debug_analysis_delay}s after {phase}")
        await asyncio.sleep(settings.debug_analysis_delay)


async def run_analysis(project_id: str) -> None:
    """
    Run complete code analysis on a project.

    Status progression: pending → cloning → scanning → analyzing → ready
    On error: status → failed

    Args:
        project_id: Project ID to analyze
    """
    db = SessionLocal()
    git_service = GitService()

    try:
        # Load project from database
        logger.info(f"Starting analysis for project {project_id}")
        project = db.query(Project).filter(Project.id == project_id).first()

        if not project:
            logger.error(f"Project not found: {project_id}")
            return

        # ========================================================================
        # Phase 1: CLONING
        # ========================================================================
        if project.source_type == SourceType.git_url:
            logger.info(f"Phase 1: Cloning repository for project {project_id}")
            project.status = ProjectStatus.cloning
            db.commit()
            await _debug_delay("cloning status set")

            # Determine clone location
            clone_dir = Path("./repos") / project_id
            clone_dir.parent.mkdir(parents=True, exist_ok=True)

            # Clone repository
            success, error = git_service.clone_repository(
                git_url=project.source,
                local_path=str(clone_dir),
                branch=project.branch,
                max_size_mb=settings.max_repo_size_mb
            )

            if not success:
                raise Exception(f"Failed to clone repository: {error}")

            # Update local path
            project.local_path = str(clone_dir)
            db.commit()

        elif project.source_type == SourceType.local_path:
            logger.info(f"Using local path for project {project_id}")

            # Validate local path exists
            local_path = Path(project.source)
            if not local_path.exists():
                raise Exception(f"Local path does not exist: {project.source}")

            if not local_path.is_dir():
                raise Exception(f"Local path is not a directory: {project.source}")

            # Set local_path
            project.local_path = project.source
            db.commit()

        else:
            raise Exception(f"Unknown source type: {project.source_type}")

        # ========================================================================
        # Phase 2: SCANNING
        # ========================================================================
        logger.info(f"Phase 2: Scanning repository for project {project_id}")
        project.status = ProjectStatus.scanning
        db.commit()
        await _debug_delay("scanning status set")

        # Initialize analyzer
        analyzer = GenericAnalyzer(
            repo_path=project.local_path,
            max_file_size_mb=settings.max_file_size_mb,
            use_gitignore=True
        )

        # ========================================================================
        # Phase 3: ANALYZING
        # ========================================================================
        logger.info(f"Phase 3: Analyzing code for project {project_id}")
        project.status = ProjectStatus.analyzing
        db.commit()
        await _debug_delay("analyzing status set")

        # Run analysis
        stats = analyzer.analyze()

        # ========================================================================
        # Phase 4: EMBEDDING
        # ========================================================================
        logger.info(f"Phase 4: Generating embeddings for project {project_id}")
        project.status = ProjectStatus.embedding
        project.stats = stats  # Save stats now in case embedding fails
        db.commit()
        await _debug_delay("embedding status set")

        # Try to generate embeddings (graceful failure)
        try:
            embedding_provider = get_embedding_provider()
            vector_service = get_vector_service()

            # Check if embedding service is available
            embedding_healthy = await embedding_provider.health_check()
            vector_healthy = await vector_service.health_check()

            if embedding_healthy and vector_healthy:
                chunking_service = ChunkingService(
                    max_file_size_mb=settings.max_file_size_mb
                )

                chunk_count = await chunking_service.chunk_project(
                    project_id=project_id,
                    repo_path=project.local_path,
                    db=db,
                    embedding_provider=embedding_provider,
                    vector_service=vector_service,
                )
                logger.info(f"Generated {chunk_count} chunks for project {project_id}")
            else:
                logger.warning(
                    f"Embedding services unavailable (embedding: {embedding_healthy}, "
                    f"vector: {vector_healthy}), skipping embedding phase"
                )
        except Exception as e:
            # Log but don't fail - embedding is optional
            logger.warning(f"Embedding phase failed for project {project_id}: {e}")

        # ========================================================================
        # Phase 5: READY
        # ========================================================================
        logger.info(f"Phase 5: Analysis complete for project {project_id}")
        project.status = ProjectStatus.ready
        project.last_analyzed_at = datetime.utcnow()
        db.commit()

        logger.info(f"Successfully analyzed project {project_id}: "
                   f"{stats['files']} files, {stats['lines_of_code']} LOC")

    except Exception as e:
        # Set failed status
        logger.error(f"Analysis failed for project {project_id}: {e}")
        try:
            project = db.query(Project).filter(Project.id == project_id).first()
            if project:
                project.status = ProjectStatus.failed
                db.commit()
        except Exception as db_error:
            logger.error(f"Failed to update status to failed: {db_error}")

    finally:
        db.close()


async def re_analyze(project_id: str, force: bool = False) -> None:
    """
    Re-run analysis on an existing project.

    Args:
        project_id: Project ID to re-analyze
        force: Force re-analysis even if recently analyzed
    """
    db = SessionLocal()

    try:
        project = db.query(Project).filter(Project.id == project_id).first()

        if not project:
            logger.error(f"Project not found: {project_id}")
            return

        # Check if already analyzing
        if project.status in [ProjectStatus.cloning, ProjectStatus.scanning, ProjectStatus.analyzing, ProjectStatus.embedding]:
            logger.warning(f"Project {project_id} is already being analyzed")
            return

        # Reset status to pending
        project.status = ProjectStatus.pending
        db.commit()

        # Run analysis
        await run_analysis(project_id)

    finally:
        db.close()


async def cancel_analysis(project_id: str) -> bool:
    """
    Cancel ongoing analysis.

    Args:
        project_id: Project ID

    Returns:
        True if cancelled, False if not analyzing
    """
    db = SessionLocal()

    try:
        project = db.query(Project).filter(Project.id == project_id).first()

        if not project:
            return False

        # Check if analyzing
        if project.status not in [ProjectStatus.cloning, ProjectStatus.scanning, ProjectStatus.analyzing, ProjectStatus.embedding]:
            return False

        # Set to failed status
        project.status = ProjectStatus.failed
        db.commit()

        logger.info(f"Cancelled analysis for project {project_id}")
        return True

    finally:
        db.close()
