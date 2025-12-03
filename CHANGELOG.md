# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **SLURM Mock System** for testing without a real cluster
  - Mock command scripts (`mocks/scontrol`, `sacctmgr`, `squeue`, `sinfo`) supporting both JSON and text formats
  - Recording script (`utils/record_slurm_outputs.sh`) to capture real SLURM outputs
  - Comprehensive documentation (`mocks/README.md`, `utils/MOCK_USAGE.md`)
  - Support for 15+ SLURM commands (nodes, partitions, reservations, qos, accounts, users, jobs, config)
  - CI/CD ready - add `mocks/` to PATH for testing without cluster access
- Python utility `utils/show_part.py` - converted from bash/awk for partition statistics display
- Modern Python packaging structure with src layout
- Comprehensive test suite with pytest
- Pre-commit hooks configuration
- Type hints support with py.typed marker
- Documentation improvements
- CI/CD configuration with GitHub Actions
- Development tools: black, isort, flake8, mypy
- Tox configuration for multi-environment testing
- Initial release
- CLI tool for Slurm cluster management
- Autocomplete functionality for commands and parameters
- Support for managing partitions, nodes, jobs, users, QoS, accounts, and reservations
- Interactive command-line interface
- Rich console output with Click and Rich libraries
- Fast autocomplete with fuzzy matching

### Changed

- Migrated to Poetry for dependency management and packaging
- Updated project structure to follow modern Python packaging standards
- Renamed project from slurm-swiss-knife to slurm-cli
- Enhanced pyproject.toml with proper Poetry configuration and metadata
- Updated package name from slurm_swiss_knife to slurm_cli

### Fixed

- Improved package structure and organization
- Better separation of source code and tests
- Enhanced development workflow
