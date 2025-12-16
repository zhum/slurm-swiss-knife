# Contributing

Thank you for your interest in contributing to Slurm CLI!

## Getting Started

### Prerequisites

- Python 3.9 or higher
- Poetry for dependency management
- Git

### Development Setup

```bash
# Clone the repository
git clone https://github.com/zhum/slurm-cli.git
cd slurm-cli

# Install dependencies including dev tools
poetry install --with dev

# Install pre-commit hooks
poetry run pre-commit install

# Verify setup
poetry run pytest
```

## Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/my-new-feature
# or
git checkout -b fix/bug-description
```

### 2. Make Changes

Follow the coding style guidelines below.

### 3. Format Code

```bash
# Run formatter
make format
# or
poetry run black --line-length=72 src tests
poetry run isort --profile=black src tests
```

### 4. Run Tests

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=slurm_cli

# Run specific test file
poetry run pytest tests/test_users.py

# Run specific test
poetry run pytest tests/test_users.py::TestUserUpdate::test_update_user_simple
```

### 5. Run Quick Fix Script

```bash
./quick-fix.sh
```

### 6. Commit Changes

```bash
git add .
git commit -m "feat: add new feature description"
```

### 7. Submit Pull Request

Push your branch and create a pull request on GitHub.

## Coding Style

### Python Style

- Line length: 72 characters (enforced by black)
- Use type hints for all function signatures
- Follow PEP 8 guidelines
- Use docstrings for all public functions/classes

### Example

```python
from typing import Any, Dict, List, Optional


def my_function(
    name: str,
    options: Optional[Dict[str, Any]] = None,
    verbose: bool = False,
) -> List[str]:
    """Short description of the function.

    Longer description if needed.

    Args:
        name: The name parameter
        options: Optional configuration options
        verbose: Enable verbose output

    Returns:
        List of result strings
    """
    if options is None:
        options = {}
    
    results = []
    # Implementation
    return results
```

### Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Classes | PascalCase | `UserManager` |
| Functions | snake_case | `get_user_list` |
| Constants | UPPER_SNAKE | `MAX_RETRIES` |
| Variables | snake_case | `user_name` |
| Private | _prefix | `_internal_method` |

## Project Structure

```
slurm-cli/
├── src/slurm_cli/           # Main package
│   ├── __init__.py
│   ├── cli.py               # CLI entry point
│   └── utils/               # Resource handlers
│       ├── accounts.py
│       ├── users.py
│       ├── qos.py
│       └── ...
├── tests/                   # Test files
│   ├── test_accounts.py
│   ├── test_users.py
│   └── ...
├── mocks/                   # Mock Slurm commands
│   ├── data/               # Mock data files
│   ├── sacctmgr
│   └── scontrol
├── docs/                    # Documentation
└── pyproject.toml          # Project configuration
```

## Adding New Features

### Adding a New Resource

1. Create `src/slurm_cli/utils/newresource.py`
2. Implement the resource class inheriting from `BaseSlurmResource`
3. Add `get_profile_fields()` method
4. Implement `show()`, `create()`, `update()`, `delete()` methods
5. Add autocomplete support with `generate_autocomplete_options()`
6. Register in `cli.py`
7. Add tests in `tests/test_newresource.py`
8. Add mock data if needed
9. Add documentation

### Example Resource Class

```python
from typing import Any, List, Optional
from .base_resource import BaseSlurmResource
from .utils import console


class NewResource(BaseSlurmResource):
    """Handle new resource operations."""

    @classmethod
    def get_profile_fields(cls) -> dict:
        """Return field descriptions for profiles."""
        return {
            "name": "Resource name",
            "description": "Resource description",
        }

    @classmethod
    def show(
        cls,
        name: Optional[str] = None,
        style: str = "pretty",
        **kwargs,
    ) -> None:
        """Show resource information."""
        # Implementation

    @classmethod
    def create(
        cls,
        name: str,
        verbose: bool = False,
        **kwargs: Any,
    ) -> None:
        """Create a new resource."""
        # Implementation

    @classmethod
    def update(
        cls,
        name: str,
        verbose: bool = False,
        **kwargs: Any,
    ) -> None:
        """Update a resource."""
        # Implementation

    @classmethod
    def delete(cls, name: str) -> None:
        """Delete a resource."""
        # Implementation
```

## Testing

### Writing Tests

```python
import subprocess
from unittest.mock import patch, MagicMock

from slurm_cli.utils.newresource import NewResource


class TestNewResourceCreate:
    """Tests for NewResource.create method."""

    def test_create_success(self):
        """Test successful resource creation."""
        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_result.returncode = 0

        with patch.object(subprocess, "run", return_value=mock_result):
            NewResource.create("testname")
            # Assertions

    def test_create_failure(self):
        """Test creation failure handling."""
        error = subprocess.CalledProcessError(1, "cmd", stderr="Error")
        with patch.object(subprocess, "run", side_effect=error):
            NewResource.create("testname")
            # Assertions
```

### Test Coverage

Aim for high test coverage:

```bash
poetry run pytest --cov=slurm_cli --cov-report=html
open htmlcov/index.html
```

## Documentation

### Updating Docs

1. Edit files in `docs/`
2. Build locally to test:
   ```bash
   poetry run mkdocs serve
   ```
3. View at http://localhost:8000

### Docstring Format

Use Google-style docstrings:

```python
def function(arg1: str, arg2: int = 0) -> bool:
    """Short description.

    Longer description if needed.

    Args:
        arg1: Description of arg1
        arg2: Description of arg2

    Returns:
        Description of return value

    Raises:
        ValueError: When arg1 is empty
    """
```

## Commit Messages

Follow conventional commits:

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation
- `test:` Tests
- `refactor:` Code refactoring
- `chore:` Maintenance

Examples:

```
feat: add user update with WHERE/SET syntax
fix: correct adminlevel validation
docs: add QoS management guide
test: add tests for bulk user update
```

## Questions?

- Open an issue on GitHub
- Check existing issues for answers

