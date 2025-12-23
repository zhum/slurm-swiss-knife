# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **Jobs Resource**: New `jobs` resource for viewing and managing Slurm jobs
  - `slurm-cli show jobs` - list jobs with filters (user=, state=, partition=, account=)
  - `slurm-cli update jobs JOBID key=value` - update job properties
  - `slurm-cli delete jobs JOBID` - cancel a job (uses scancel)
  - Supports all output styles (pretty, json, csv) and profiles
  - Profile configs: default (all columns), compact (key info), minimal, oneline, detailed
  - Aliases: `job`, `j`
- **Node Filter Syntax**: Select nodes by filter instead of explicit names
  - `nodes=partition=NAME` - nodes from a partition
  - `nodes=state=STATE` - nodes by state (idle, alloc, drain, etc.)
  - `nodes=user=USERNAME` - nodes running user's jobs
  - `nodes=reservation=NAME` - nodes in a reservation
  - Works anywhere `nodes=` is accepted (partitions, reservations, etc.)
- **Association Create Command**: Create user associations with `slurm-cli create associations`
  - Supports positional username or `name=`/`user=` syntax
  - Accepts all association options (account, partition, qos, fairshare, limits)
- **User Create `name=` Syntax**: Allow `name=username` anywhere in create arguments
- **User Create Validation**: Warns if account/wckey not specified, prompts for confirmation
- **Tree View for Associations**: `--tree` option for hierarchical display
  - `--indent` option for custom indentation string
- **Resource-Specific Help**: Context-aware `--help` for action+resource combinations
  - Shows syntax, examples, and available options for each resource type
  - Example: `slurm-cli add coord --help` shows coordinator-specific help
- **Global Dry-Run Mode**: `SLURM_CLI_DRYRUN` env var and `--dry-run`/`--no-dry-run` options
  - Set `SLURM_CLI_DRYRUN=y` to enable dry-run globally
  - Use `--no-dry-run` to override env var
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

### Changed

- **Coordinator Update Disabled**: `update` operation is not supported for coordinators
  - Use `create` to add coordinators and `delete` to remove them
  - Running `slurm-cli update coordinators` now shows an error message

### Fixed

- Fixed `resolve_resource_alias()` not actually resolving aliases
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
