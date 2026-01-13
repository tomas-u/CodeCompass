"""Mock analysis service for testing status updates.

This is a temporary implementation to test polling functionality.
Will be replaced by real analysis engine in Story #33.
"""

import asyncio
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.project import Project, ProjectStatus
from app.database import SessionLocal


async def simulate_analysis(project_id: str):
    """Simulate analysis by updating project status over time.

    This allows testing of the polling functionality before implementing
    the real analysis engine.

    Status progression: pending → cloning → scanning → analyzing → ready
    """
    # Create a new database session for this background task
    db = SessionLocal()

    try:
        # Wait a bit before starting
        await asyncio.sleep(2)

        # Update to cloning
        project = db.query(Project).filter(Project.id == project_id).first()
        if project:
            project.status = ProjectStatus.cloning
            project.updated_at = datetime.utcnow()
            db.commit()

        await asyncio.sleep(3)

        # Update to scanning
        project = db.query(Project).filter(Project.id == project_id).first()
        if project:
            project.status = ProjectStatus.scanning
            project.updated_at = datetime.utcnow()
            db.commit()

        await asyncio.sleep(4)

        # Update to analyzing
        project = db.query(Project).filter(Project.id == project_id).first()
        if project:
            project.status = ProjectStatus.analyzing
            project.updated_at = datetime.utcnow()
            db.commit()

        await asyncio.sleep(5)

        # Update to ready with mock stats
        project = db.query(Project).filter(Project.id == project_id).first()
        if project:
            project.status = ProjectStatus.ready
            project.updated_at = datetime.utcnow()
            project.last_analyzed_at = datetime.utcnow()
            project.stats = {
                "files": 42,
                "directories": 8,
                "lines_of_code": 1250,
                "languages": {
                    "TypeScript": {
                        "files": 28,
                        "lines": 812
                    },
                    "Python": {
                        "files": 14,
                        "lines": 438
                    }
                }
            }
            db.commit()

    except Exception as e:
        print(f"Error in mock analysis: {e}")
        # Mark project as failed
        project = db.query(Project).filter(Project.id == project_id).first()
        if project:
            project.status = ProjectStatus.failed
            project.updated_at = datetime.utcnow()
            db.commit()
    finally:
        db.close()
