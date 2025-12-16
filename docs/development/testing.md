# Testing

Slurm CLI uses pytest for testing with comprehensive coverage of all features.

## Running Tests

### Basic Test Run

```bash
# Run all tests
poetry run pytest

# Run with verbose output
poetry run pytest -v

# Run specific test file
poetry run pytest tests/test_users.py

# Run specific test class
poetry run pytest tests/test_users.py::TestUserUpdate

# Run specific test
poetry run pytest tests/test_users.py::TestUserUpdate::test_update_user_simple
```

### Quick Test Run

```bash
# Stop on first failure
poetry run pytest -x

# Quiet output
poetry run pytest -q

# Combined
poetry run pytest -x -q
```

### Test Coverage

```bash
# Run with coverage
poetry run pytest --cov=slurm_cli

# Generate HTML report
poetry run pytest --cov=slurm_cli --cov-report=html

# View report
open htmlcov/index.html
```

## Test Structure

```
tests/
├── __init__.py
├── test_accounts.py      # Account tests
├── test_associations.py  # Association tests
├── test_cli.py          # CLI command tests
├── test_cli_extended.py # Extended CLI tests
├── test_coordinators.py # Coordinator tests
├── test_events.py       # Event tests
├── test_nodes.py        # Node tests
├── test_partitions.py   # Partition tests
├── test_profiles.py     # Profile tests
├── test_qos.py          # QoS tests
├── test_reservations.py # Reservation tests
├── test_resources.py    # Resource base tests
├── test_slurm_config.py # Config tests
└── test_users.py        # User tests
```

## Writing Tests

### Test Class Structure

```python
import subprocess
from unittest.mock import patch, MagicMock
import pytest

from slurm_cli.utils.users import User


def create_mock_subprocess_result(stdout="", returncode=0):
    """Helper to create mock subprocess results."""
    mock_result = MagicMock()
    mock_result.stdout = stdout
    mock_result.returncode = returncode
    return mock_result


class TestUserCreate:
    """Tests for User.create method."""

    def test_create_user_success(self):
        """Test successful user creation."""
        mock_result = create_mock_subprocess_result(stdout="")
        with patch.object(subprocess, "run", return_value=mock_result):
            User.create("newuser")
            # Verify success

    def test_create_user_with_options(self):
        """Test user creation with options."""
        mock_result = create_mock_subprocess_result()
        with patch.object(
            subprocess, "run", return_value=mock_result
        ) as mock_run:
            User.create("newuser", account="myaccount")
            
            # Verify correct arguments
            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            assert "account=myaccount" in call_args

    def test_create_user_failure(self):
        """Test user creation failure handling."""
        error = subprocess.CalledProcessError(
            1, "sacctmgr", stderr="User exists"
        )
        with patch.object(subprocess, "run", side_effect=error):
            # Should handle error gracefully
            User.create("existinguser")
```

### Testing Output

```python
import io
from contextlib import redirect_stdout

class TestUserShow:
    def test_show_users_output(self):
        """Test show users output format."""
        mock_data = {"users": [{"name": "user1"}]}
        mock_result = create_mock_subprocess_result(
            stdout=json.dumps(mock_data)
        )
        
        with patch.object(subprocess, "run", return_value=mock_result):
            output = io.StringIO()
            with redirect_stdout(output):
                User.show()
            
            result = output.getvalue()
            assert "user1" in result
```

### Testing Validation

```python
class TestUserUpdate:
    def test_update_invalid_adminlevel(self):
        """Test that invalid adminlevel is rejected."""
        with patch.object(subprocess, "run") as mock_run:
            output = io.StringIO()
            with redirect_stdout(output):
                User.update("testuser", adminlevel="superuser")
            
            # Should NOT call subprocess
            mock_run.assert_not_called()
            
            # Should print error
            result = output.getvalue()
            assert "Invalid adminlevel" in result
```

## Using Mock System

### With Mock Commands

```bash
# Add mocks to PATH
PATH=$PATH:./mocks poetry run pytest

# Or set in test
import os
os.environ["PATH"] = f"./mocks:{os.environ['PATH']}"
```

### Mock Data Files

Test data is stored in `mocks/data/`:

```
mocks/data/
├── accounts.json
├── users.json
├── qos.json
├── partitions.json
├── nodes.json
├── reservations.json
└── ...
```

## Test Categories

### Unit Tests

Test individual functions/methods in isolation:

```python
class TestUserInit:
    def test_user_init_with_name(self):
        user = User("testuser")
        assert user.name == "testuser"
```

### Integration Tests

Test interactions between components:

```python
@pytest.mark.integration
class TestCLIIntegration:
    def test_show_users_command(self):
        # Test full CLI command flow
        pass
```

### Slow Tests

Mark slow tests for optional skipping:

```python
@pytest.mark.slow
class TestSlowOperations:
    def test_large_dataset(self):
        # Slow test
        pass
```

Run excluding slow tests:

```bash
poetry run pytest -m "not slow"
```

## Fixtures

### Common Fixtures

```python
@pytest.fixture
def mock_subprocess():
    """Fixture to mock subprocess calls."""
    with patch.object(subprocess, "run") as mock:
        yield mock

@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "users": [
            {"name": "user1", "administrator_level": "None"},
            {"name": "user2", "administrator_level": "Admin"},
        ]
    }
```

### Using Fixtures

```python
class TestUserShow:
    def test_show_with_fixture(self, mock_subprocess, sample_user_data):
        mock_subprocess.return_value = create_mock_subprocess_result(
            stdout=json.dumps(sample_user_data)
        )
        User.show()
        mock_subprocess.assert_called_once()
```

## Continuous Integration

Tests run automatically on:

- Pull requests
- Pushes to main branch

Configuration in `.github/workflows/`:

```yaml
- name: Run tests
  run: poetry run pytest --cov=slurm_cli
```

## Debugging Tests

### Print Debug Output

```bash
poetry run pytest -s  # Don't capture stdout
```

### Drop into Debugger

```bash
poetry run pytest --pdb  # Drop into pdb on failure
```

### Verbose Failures

```bash
poetry run pytest -vv  # Extra verbose
```

