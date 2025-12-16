# Slurm CLI

A CLI tool for Slurm cluster management with autocomplete functionality.

## Features

- Interactive command-line interface for Slurm cluster management via slurm commands wrapping
- Autocomplete support for commands and parameters
- Support for managing partitions, nodes, jobs, users, QoS, accounts, and reservations
- Rich console output with colored and formatted text
- Fast fuzzy matching for autocomplete suggestions

## Installation

### From PyPI

The easiest way to install slurm-cli is using pip:

```bash
pip install slurm-cli
```

### From Source

To install from source:

```bash
# Clone the repository
git clone https://github.com/zhum/slurm-cli.git
cd slurm-cli

# Install dependencies using Poetry
poetry install

# Activate the virtual environment
poetry shell
```

### Development Setup

For development, you'll also want to install the development dependencies:

```bash
poetry install --with dev
poetry run pre-commit install
```

## Usage

Run the CLI tool:

```bash
slurm-cli
```

Or with Poetry:

```bash
poetry run slurm-cli
```

### Autocomplete Setup

To enable bash autocompletion for this command:

1. Install the completion script:

```bash
eval "$(_CLICK_COMPLETE=bash_source slurm-cli)"
```

1. Add the above line to your `~/.bashrc` or `~/.bash_profile` to make it permanent.

1. Restart your shell or run: `source ~/.bashrc`

Alternatively, you can generate a completion script file:

```bash
_CLICK_COMPLETE=bash_source slurm-cli > \
    ~/.local/share/bash-completion/completions/slurm-cli
```

## Development

### Running Tests

```bash
poetry run pytest
# or with coverage
poetry run pytest --cov=slurm_cli
```

### Code Formatting

```bash
poetry run black src tests
poetry run isort src tests
```

### Type Checking

```bash
poetry run mypy src/
```

### All Checks

```bash
make check
# or
poetry run tox
```

### Building Documentation

```bash
make docs
# or
poetry run mkdocs build

# Serve locally
make docs-serve
# or
poetry run mkdocs serve
# Then open http://localhost:8000
```

## Project Structure

```text
slurm-cli/
├── src/
│   └── slurm_cli/          # Main package
│       ├── __init__.py
│       ├── cli.py          # CLI entry point
│       └── utils/          # Utility functions
├── tests/                  # Test files
├── docs/                   # Documentation
├── pyproject.toml         # Poetry configuration
├── Makefile               # Development commands
├── tox.ini                # Multi-environment testing
├── .pre-commit-config.yaml # Pre-commit hooks
└── README.md              # This file
```

## Requirements

- Python 3.9 or higher
- Slurm cluster environment
- Required Python packages (automatically installed):
  - click>=8.1.0
  - rich>=13.0.0
  - fast-autocomplete[levenshtein]>=0.9.0
  - rapidfuzz>=3.13.0

## License

MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for a list of changes.
