# Test Fixtures

This directory contains reusable test fixtures and sample repositories for CodeCompass tests.

## Directory Structure

```
fixtures/
├── README.md                    # This file
├── factories.py                 # Factory functions for creating test data
└── sample_repos/               # Sample repositories for testing analysis
    ├── python_simple/          # Simple Python project
    ├── javascript_simple/      # Simple JavaScript project
    └── mixed_language/         # Mixed Python + JavaScript project
```

## Sample Repositories

### python_simple/

A minimal Python project with realistic structure:
- **main.py** - Entry point with imports from utils
- **utils.py** - Helper functions
- **requirements.txt** - Package dependencies
- **.gitignore** - Standard Python patterns

**Use cases:**
- Testing Python code analysis
- Testing import extraction
- Testing .gitignore filtering

### javascript_simple/

A minimal JavaScript/Node.js project:
- **index.js** - Entry point with ES6 imports
- **utils.js** - Utility functions with exports
- **package.json** - NPM configuration
- **.gitignore** - Standard Node patterns (node_modules)

**Use cases:**
- Testing JavaScript code analysis
- Testing ES6 module detection
- Testing package.json parsing

### mixed_language/

A project combining Python and JavaScript:
- **Python files:** api.py, models.py, helpers.py
- **JavaScript files:** client.js, ui.js, config.js
- **.gitignore** - Combined Python + Node patterns

**Use cases:**
- Testing multi-language detection
- Testing language statistics aggregation
- Testing mixed project analysis

## Using Test Factories

The `factories.py` module provides factory functions for creating test data.

### Basic Usage

```python
from tests.fixtures.factories import create_test_project

# Create a simple test project
project = create_test_project(name="My Test Project")

# Create a project with specific status
project = create_test_project(
    name="Analyzing Project",
    status=ProjectStatus.analyzing
)

# Create a git URL project
project = create_test_project(
    name="Git Project",
    source_type=SourceType.git_url,
    source="https://github.com/user/repo.git"
)
```

### Creating Projects with Stats

```python
from tests.fixtures.factories import create_test_project_with_stats

# Create a project with populated statistics
project = create_test_project_with_stats(
    name="Analyzed Project",
    files=50,
    lines_of_code=2500,
    directories=10,
    languages={
        "Python": {"files": 30, "lines": 1500},
        "JavaScript": {"files": 20, "lines": 1000}
    }
)
```

### Using Sample Repositories

```python
from tests.fixtures.factories import get_sample_repo_path

# Get path to sample repository
python_repo = get_sample_repo_path('python_simple')
assert python_repo.exists()

# Create project pointing to sample repo
project = create_test_project(
    source_type=SourceType.local_path,
    source=str(python_repo)
)
```

### Creating Settings and Stats

```python
from tests.fixtures.factories import create_test_settings, create_test_stats

# Create custom settings
settings = create_test_settings(
    ignore_patterns=['*.log', '*.tmp', 'build/'],
    analyze_languages=['python', 'javascript']
)

# Create custom stats
stats = create_test_stats(
    files=100,
    directories=15,
    lines_of_code=5000,
    languages={
        "Python": {"files": 60, "lines": 3000},
        "TypeScript": {"files": 40, "lines": 2000}
    }
)

# Use in project
project = create_test_project(settings=settings, stats=stats)
```

## Factory Function Reference

### `create_test_project(**kwargs)`

Creates a test Project instance with sensible defaults.

**Parameters:**
- `name` (str): Project name (default: "Test Project")
- `source_type` (SourceType): git_url or local_path (default: local_path)
- `source` (str): Git URL or path (auto-generates if None)
- `branch` (str): Git branch (default: "main")
- `status` (ProjectStatus): Project status (default: pending)
- `local_path` (str): Local clone path (default: None)
- `settings` (dict): Project settings (default: None)
- `stats` (dict): Project stats (default: None)
- `**kwargs`: Additional fields (id, description, timestamps, etc.)

**Returns:** `Project` instance

### `create_test_project_with_stats(**kwargs)`

Creates a test Project with populated statistics.

**Parameters:**
- `name` (str): Project name
- `files` (int): Number of files (default: 10)
- `lines_of_code` (int): Total LOC (default: 500)
- `directories` (int): Number of directories (default: 3)
- `languages` (dict): Language breakdown (auto-generates if None)
- `**kwargs`: Additional fields passed to create_test_project

**Returns:** `Project` instance with stats and status=ready

### `get_sample_repo_path(repo_name)`

Gets the absolute path to a sample repository.

**Parameters:**
- `repo_name` (str): 'python_simple', 'javascript_simple', or 'mixed_language'

**Returns:** `Path` object

**Raises:** `ValueError` if repository doesn't exist

### `create_test_settings(**kwargs)`

Creates project settings dictionary.

**Parameters:**
- `ignore_patterns` (list): File patterns to ignore
- `analyze_languages` (list): Languages to analyze

**Returns:** dict

### `create_test_stats(**kwargs)`

Creates project stats dictionary.

**Parameters:**
- `files` (int): Number of files
- `directories` (int): Number of directories
- `lines_of_code` (int): Total LOC
- `languages` (dict): Language breakdown

**Returns:** dict

## Best Practices

1. **Use factories for consistency** - Always use factory functions rather than creating objects manually
2. **Customize via kwargs** - Pass custom values as keyword arguments for flexibility
3. **Use sample repos for integration tests** - Point to sample_repos/ for realistic test data
4. **Don't modify sample repos** - Treat them as read-only test data
5. **Chain factories** - Combine settings/stats factories with project factories

## Example Test

```python
import pytest
from tests.fixtures.factories import (
    create_test_project,
    get_sample_repo_path,
    create_test_settings
)
from app.services.analysis_service import analyze_project

def test_python_project_analysis():
    """Test analyzing a Python project."""
    # Arrange
    repo_path = get_sample_repo_path('python_simple')
    settings = create_test_settings(ignore_patterns=['*.pyc'])
    project = create_test_project(
        name="Python Test",
        source=str(repo_path),
        settings=settings
    )
    
    # Act
    result = analyze_project(project)
    
    # Assert
    assert result.stats['files'] == 2  # main.py and utils.py
    assert 'Python' in result.stats['languages']
```

## Maintenance

When adding new fixtures:
1. Follow existing naming conventions
2. Keep sample code simple and parseable
3. Include realistic imports/exports
4. Update this README with usage examples
5. Ensure .gitignore patterns are present
