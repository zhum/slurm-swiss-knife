# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **`burstbuffer` command** — Show burst buffer configuration via `scontrol burstbuffer`
- **`daemons` command** — Show running Slurm daemons via `scontrol daemons`
- **`dwstat` command** — Show DataWarp burst buffer status via `scontrol dwstat`
- **`topology` command** — Show network topology via `scontrol topology`
- **`setdebugflags` command** (alias: `sdf`) — Enable/disable slurmctld/slurmd debug flag categories with `+FLAG`/`-FLAG` syntax; supports `nodes=` with node filter expressions
- **`schedloglevel` command** (alias: `sll`) — Set scheduler log verbosity level with autocomplete for valid values
- **`drain=REGEXP` node filter** — Short alias for `drainreason=REGEXP`; filters nodes by drain reason matching a case-insensitive regular expression; supported everywhere node filters are accepted (drain, undrain, reboot, cancel-reboot, setdebug, setdebugflags)
- **Autocomplete: command prefix disambiguation** — When a command name is itself a prefix of another command (e.g., `setdebug` vs `setdebugflags`), typing the exact shorter name now shows both as completions instead of prematurely completing to the shorter one
- **Autocomplete: `nodes=` sub-filter for `drain=`** — Typing `nodes=drain=<TAB>` shows `nodes=drain=REGEXP` as a hint in setdebug/setdebugflags completion

### Fixed

- **Autocomplete cache with `./slurm-cli`** — `_slurm_ensure_cache` now tries `${COMP_WORDS[0]}` (the invoked binary) before falling back to `slurm-cli` in PATH, so cache population works when invoking via a local path

- **User Update Implementation**: Full `User.update()` method with:
  - Simple mode: `modify users NAME set key=value`
  - WHERE/SET mode: `modify users key=value set newkey=newvalue`
  - Admin level validation (none/admin/operator only)
  - `newname` option for renaming users
  
- **QoS Update Implementation**: Full `Qos.update()` method with:
  - Simple mode: `modify qos NAME set key=value`
  - WHERE/SET mode: `modify qos key=value set newkey=newvalue`
  - PreemptMode validation (OFF/CANCEL/GANG/REQUEUE/SUSPEND/WITHIN)

- **QoS Options Constants**: `QOS_OPTIONS`, `QOS_FLAGS`, `PREEMPT_MODE_VALUES` for autocomplete and validation

- **Account Options Constants**: `ACCOUNT_OPTIONS` for autocomplete and validation

- **User Update Constants**: `USER_UPDATE_SET_OPTIONS`, `USER_UPDATE_WHERE_OPTIONS`, `VALID_ADMIN_LEVELS`

- **QoS Autocomplete**: Tab completion for QoS create/update with flags and preempt mode values

- **Account Autocomplete**: Tab completion for account create/update with filter options and `set` keyword

- **User Autocomplete**: Tab completion for user create/update with filter/set options and admin level values

- **Account Update Modes**: Two update scenarios:
  1. Simple: `modify accounts NAME key=value [...]`
  2. WHERE/SET: `modify accounts key=value [...] set newkey=newvalue [...]`

- **Account Filters**: Filter accounts by field (e.g., `show accounts organization=nvidia`)

- **Profile Fields Refactoring**: Moved `RESOURCE_FIELDS` into resource classes via `get_profile_fields()` method

- **Reservation Aliases**: `start=` and `end=` as aliases for `starttime=` and `endtime=`

- **Global Confirmation Skip**: `-y`/`--yes` option for delete/update commands

- **User Filtering**: Filter aliases for user show (`defaultaccount`, `account`, `adminlevel`, `user`)

- **Mock sacctmgr Enhancements**: Support for create, modify, delete commands with flag handling

### Fixed

- Fixed `Qos.create()`, `Account.create()`, `Node.create()`, `User.create()` missing `verbose` parameter
- Fixed autocomplete registration for `./slurm-cli` invocation
- Fixed user filtering with nested JSON fields

## [0.1.0] - 2025-12-15

### Added

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
