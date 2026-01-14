"""Test data factories for creating test objects."""

from uuid import uuid4
from datetime import datetime
from pathlib import Path
from app.models.project import Project
from app.schemas.project import SourceType, ProjectStatus


# Path to sample repositories
FIXTURES_DIR = Path(__file__).parent
SAMPLE_REPOS_DIR = FIXTURES_DIR / "sample_repos"


def create_test_project(
    name="Test Project",
    source_type=SourceType.local_path,
    source=None,
    branch="main",
    status=ProjectStatus.pending,
    local_path=None,
    settings=None,
    stats=None,
    **kwargs
):
    """
    Factory for creating test Project instances.
    
    Args:
        name: Project name
        source_type: SourceType enum (git_url or local_path)
        source: Git URL or local path (auto-generates if None)
        branch: Git branch name
        status: ProjectStatus enum
        local_path: Where repo is cloned locally
        settings: Project settings dict
        stats: Project stats dict
        **kwargs: Additional fields to override
    
    Returns:
        Project: SQLAlchemy Project instance
    
    Example:
        >>> project = create_test_project(name="My Test", status=ProjectStatus.ready)
        >>> project = create_test_project(source_type=SourceType.git_url, source="https://github.com/user/repo.git")
    """
    # Generate default source if not provided
    if source is None:
        if source_type == SourceType.git_url:
            source = "https://github.com/test/test-repo.git"
        else:
            source = str(SAMPLE_REPOS_DIR / "python_simple")
    
    # Create project instance
    project = Project(
        id=kwargs.get('id', str(uuid4())),
        name=name,
        source_type=source_type,
        source=source,
        branch=branch,
        status=status,
        local_path=local_path,
        settings=settings,
        stats=stats,
        description=kwargs.get('description'),
        created_at=kwargs.get('created_at', datetime.utcnow()),
        updated_at=kwargs.get('updated_at', datetime.utcnow()),
        last_analyzed_at=kwargs.get('last_analyzed_at'),
    )
    
    return project


def create_test_project_with_stats(
    name="Test Project with Stats",
    files=10,
    lines_of_code=500,
    directories=3,
    languages=None,
    **kwargs
):
    """
    Factory for creating test Project with populated stats.
    
    Args:
        name: Project name
        files: Number of files
        lines_of_code: Total lines of code
        directories: Number of directories
        languages: Dict of language stats (auto-generates if None)
        **kwargs: Additional fields passed to create_test_project
    
    Returns:
        Project: SQLAlchemy Project instance with stats
    
    Example:
        >>> project = create_test_project_with_stats(files=50, lines_of_code=2500)
    """
    # Generate default language stats if not provided
    if languages is None:
        languages = {
            "Python": {"files": 6, "lines": 300},
            "JavaScript": {"files": 4, "lines": 200}
        }
    
    stats = {
        "files": files,
        "lines_of_code": lines_of_code,
        "directories": directories,
        "languages": languages
    }
    
    return create_test_project(
        name=name,
        status=ProjectStatus.ready,
        stats=stats,
        last_analyzed_at=datetime.utcnow(),
        **kwargs
    )


def get_sample_repo_path(repo_name):
    """
    Get the absolute path to a sample repository.
    
    Args:
        repo_name: Name of the sample repo ('python_simple', 'javascript_simple', 'mixed_language')
    
    Returns:
        Path: Absolute path to the sample repository
    
    Example:
        >>> path = get_sample_repo_path('python_simple')
        >>> assert path.exists()
    """
    repo_path = SAMPLE_REPOS_DIR / repo_name
    if not repo_path.exists():
        raise ValueError(f"Sample repository '{repo_name}' does not exist at {repo_path}")
    return repo_path


def create_test_settings(
    ignore_patterns=None,
    analyze_languages=None
):
    """
    Factory for creating test project settings.
    
    Args:
        ignore_patterns: List of file patterns to ignore
        analyze_languages: List of languages to analyze
    
    Returns:
        dict: Project settings dictionary
    
    Example:
        >>> settings = create_test_settings(ignore_patterns=['*.log', '*.tmp'])
    """
    return {
        "ignore_patterns": ignore_patterns or ["*.log", "node_modules", "__pycache__"],
        "analyze_languages": analyze_languages or ["python", "javascript", "typescript"]
    }


def create_test_stats(
    files=0,
    directories=0,
    lines_of_code=0,
    languages=None
):
    """
    Factory for creating test project stats.
    
    Args:
        files: Number of files
        directories: Number of directories
        lines_of_code: Total lines of code
        languages: Dict of language stats
    
    Returns:
        dict: Project stats dictionary
    
    Example:
        >>> stats = create_test_stats(files=10, lines_of_code=500)
    """
    return {
        "files": files,
        "directories": directories,
        "lines_of_code": lines_of_code,
        "languages": languages or {}
    }
