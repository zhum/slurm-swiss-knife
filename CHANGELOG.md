# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **QoS Options Constants**: `QOS_OPTIONS`, `QOS_FLAGS`, `PREEMPT_MODE_VALUES` for autocomplete and validation
- **Account Options Constants**: `ACCOUNT_OPTIONS` for autocomplete and validation
- **QoS Autocomplete**: Tab completion for QoS create/update with flags and preempt mode values
- **Account Autocomplete**: Tab completion for account create/update with filter options and `set` keyword
- **Account Update Modes**: Two update scenarios:
  1. Simple: `modify accounts NAME key=value [...]`
  1. WHERE/SET: `modify accounts key=value [...] set newkey=newvalue [...]`
- **Account Filters**: Filter accounts by field (e.g., `show accounts organization=nvidia`)
- **Profile Fields Refactoring**: Moved `RESOURCE_FIELDS` into resource classes via `get_profile_fields()` method
- **Mock sacctmgr Enhancements**: Support for create, modify, delete commands with flag handling

### Fixed

- Fixed `Qos.create()`, `Account.create()`, `Node.create()`, `User.create()` missing `verbose` parameter
- Fixed autocomplete registration for `./slurm-cli` invocation

## [0.0.0]

- **Output Profiles** for customizing pretty output format
  - Profile files loaded from `/etc/slurm/cli.profiles` or `~/.config/slurm-cli.profiles`
  - `--profile` CLI option to select named profile (default, compact, minimal, oneline, detailed)
  - `--profile-str` CLI option for inline profile specification
  - Customizable columns and styles per resource type
  - Template-based output with Rich markup support
  - Template syntax: `{field}` for values, `[color]text[/color]` for styling, `\n` for newlines
  - Example: `accounts.template=[cyan]{name}[/cyan] - {description}`
- **SLURM Mock System** for testing without a real cluster
  - Mock command scripts (`mocks/scontrol`, `sacctmgr`, `squeue`, `sinfo`) supporting both JSON and text formats
  - Recording script (`utils/record_slurm_outputs.sh`) to capture real SLURM outputs
  - Comprehensive documentation (`mocks/README.md`, `utils/MOCK_USAGE.md`)
  - Support for 15+ SLURM commands (nodes, partitions, reservations, qos, accounts, users, jobs, config)
  - CI/CD ready - add `mocks/` to PATH for testing without cluster access
- Python utility `utils/show_part.py` - converted from bash/awk for partition statistics display

## [0.1.0] - 2025-12-15

- Initial release
- CLI tool for Slurm cluster management
- Autocomplete functionality for commands and parameters
- Support for managing partitions, nodes, jobs, users, QoS, accounts, and reservations
- Interactive command-line interface
- Rich console output with Click and Rich libraries
- Fast autocomplete with fuzzy matching
- Modern Python packaging structure with src layout
- Comprehensive test suite with pytest
- Pre-commit hooks configuration
- Type hints support with py.typed marker
- Documentation improvements
- CI/CD configuration with GitHub Actions
- Development tools: black, isort, flake8, mypy
- Tox configuration for multi-environment testing

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
