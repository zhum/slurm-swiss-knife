# Installation

## Requirements

- Python 3.9 or higher
- pip or Poetry package manager
- Access to a Slurm cluster (or use [mock system](../development/mocks.md) for testing)

## From PyPI

The easiest way to install slurm-cli:

```bash
pip install slurm-cli
```

## From Source

### Using Poetry (Recommended)

```bash
# Clone the repository
git clone https://github.com/zhum/slurm-cli.git
cd slurm-cli

# Install dependencies using Poetry
poetry install

# Activate the virtual environment
poetry shell

# Verify installation
slurm-cli --version
```

### Using pip

```bash
# Clone the repository
git clone https://github.com/zhum/slurm-cli.git
cd slurm-cli

# Install in development mode
pip install -e .

# Verify installation
slurm-cli --version
```

## Development Installation

For development, install with dev dependencies:

```bash
# Using Poetry
poetry install --with dev

# Install pre-commit hooks
poetry run pre-commit install
```

This includes:

- `pytest` - Testing framework
- `black` - Code formatter
- `isort` - Import sorter
- `flake8` - Linter
- `mypy` - Type checker

## Verifying Installation

After installation, verify that slurm-cli is working:

```bash
# Check version
slurm-cli --version

# Show help
slurm-cli --help

# Test with mock data (no Slurm required)
PATH=$PATH:./mocks slurm-cli show partitions
```

## Next Steps

- [Set up autocomplete](autocomplete.md) for enhanced productivity
- [Quick start guide](quickstart.md) to learn basic commands

