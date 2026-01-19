"""Database configuration and session management."""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

# Create SQLite database engine
# check_same_thread=False is needed for FastAPI to work with SQLite
# Use DATABASE_URL from env if set, otherwise use default local path
SQLALCHEMY_DATABASE_URL = settings.database_url or f"sqlite:///./{settings.database_name}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False  # Set to True for SQL query logging during development
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db():
    """
    Dependency function to get database session.

    Usage in FastAPI routes:
        @router.get("/")
        def endpoint(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize database - create all tables.
    Called on application startup.
    """
    # Import all models here so they are registered with Base
    from app.models import project  # noqa: F401
    from app.models import diagram  # noqa: F401
    from app.models import chat  # noqa: F401
    from app.models import code_chunk  # noqa: F401

    Base.metadata.create_all(bind=engine)
