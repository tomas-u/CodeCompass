"""Admin/debug API endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app.models.project import Project

router = APIRouter()


@router.delete("/database/clear")
async def clear_database(db: Session = Depends(get_db)):
    """Clear all data from database tables (for development/testing).

    This truncates tables but keeps the schema intact.
    No backend restart required.
    """
    # Count records before deletion
    project_count = db.query(Project).count()

    # Delete all projects (only table currently)
    db.query(Project).delete()
    db.commit()

    return {
        "message": "Database cleared successfully",
        "tables_cleared": ["projects"],
        "records_deleted": {
            "projects": project_count
        },
        "timestamp": datetime.utcnow().isoformat()
    }
