# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **Control Commands**: Added scontrol commands with shortest unique prefix support
  - `reconfigure` (aliases: reconf, rec) - Force slurmctld to re-read configuration
  - `ping` (alias: pi) - Check if slurmctld is responding
  - `takeover` (alias: tak) - Cause backup slurmctld to take over as primary
  - `version` (alias: ver) - Show slurm-cli and Slurm version
  - `token` (alias: tok) - Generate JWT authentication token with lifespan/username options
    - Supports time formats: `1h`, `30m`, `1:30:00`, `1-12:00:00`, `infinite`
  - `drain` (alias: dr) - Drain nodes with optional reason
  - `undrain` (aliases: undr, resume) - Undrain/resume nodes
  - `reboot` (alias: reb) - Reboot nodes with optional asap, nextstate, and reason
  - `cancel_reboot` (alias: cancel_reb) - Cancel pending reboot on nodes
- **Job Control Commands**: Added commands to manage job execution state
  - `hold` (alias: hol) - Hold jobs with optional reason (-r, --reason, or reason=)
  - `release` (alias: rel) - Release held jobs
  - `top` - Move jobs to top of queue
  - `requeue` (alias: req) - Requeue jobs (restart from beginning)
  - `suspend` (alias: sus) - Suspend running jobs
  - All job control commands support job filters: user=, account=, partition=, state=, name=
- **Node Filter Exclusions**: Prefix filters with `not:` to exclude nodes
  - `not:partition=gpu` - exclude nodes from GPU partition
  - `not:state=drain` - exclude drained nodes
  - `not:user=admin` - exclude nodes running admin's jobs
  - `not:reservation=maint` - exclude nodes in maintenance reservation
  - Example: `slurm-cli drain partition=gpu not:reservation=maint` drains GPU nodes except reserved ones
  - Note: Uses `not:` prefix to avoid conflicts with CLI option parsing (`-`) and bash tilde expansion (`~`)
- **Format Option Alias**: Added `-o`/`--format` as alias for `--profile-str`
  - Autocomplete now shows available fields for each resource type
- **Account Tree View**: Added tree mode for accounts with `-T`/`--tree`
  - `slurm-cli show accounts -T` - display accounts in hierarchical tree format
  - Shows account names, descriptions, organizations, and coordinators
- **Profile Field Listing**: New `--list-fields` option to show available profile fields
  - `slurm-cli --list-fields` - list fields for all resources
  - `slurm-cli --list-fields=users` - list fields for a specific resource
  - Shows field names, descriptions, and syntax help
- **Profile Sorting**: Sort output by any column with `+` or `-` suffix
  - `name+` - sort ascending by name
  - `priority-` - sort descending by priority
  - Example: `slurm-cli show accounts --profile-str='name+,description'`
  - Example: `slurm-cli show jobs --profile-str='job_id-,user_name,job_state'`
  - First sort marker wins if multiple are specified
  - Hierarchical resources (associations with `--tree`) sort within each level
- **Jobs Resource**: New `jobs` resource for viewing and managing Slurm jobs
  - `slurm-cli show jobs` - list jobs with filters (user=, state=, partition=, account=, nodes=, reservation=)
  - `slurm-cli update jobs JOBID key=value` - update job properties
  - `slurm-cli delete jobs JOBID [JOBID...]` - cancel jobs (supports multiple IDs)
  - `slurm-cli delete jobs user=NAME` - cancel all jobs for a user (uses `scancel -u`)
  - Mixed deletion: `slurm-cli delete jobs 12345 user=john state=pending` - combines IDs and filters
  - Supports all output styles (pretty, json, csv) and profiles
  - Profile fields: job_id, user_name, partition, job_state, start_time, endlimit, node_count, gres, reason
  - `endlimit` shows end_time if known, otherwise time_limit
  - Aliases: `job`, `j`
- **Partition/Reservation Node Modification**: Add or remove nodes incrementally
  - `nodes+=` - add nodes to partition/reservation
  - `nodes-=` - remove nodes from partition/reservation
  - Example: `slurm-cli update partitions gpu nodes+=node001,node002`
  - Supports node filters: `slurm-cli update partitions gpu nodes+=state=idle`
- **Partition Options**: Complete set of partition update options with autocomplete
  - All options in lowercase: `state`, `maxtime`, `allowaccounts`, `denyqos`, etc.
  - Account/QoS options autocomplete with actual values
  - Resource limits: `maxnodes`, `minnodes`, `maxcpuspernode`, `maxmempercpu`, etc.
  - Access control: `allowaccounts`, `denyaccounts`, `allowqos`, `denyqos`, `allowgroups`
  - Priority: `prioritytier`, `priorityjobfactor`, `preemptmode`, `gracetime`
  - Flags: `hidden`, `lln`, `oversubscribe`, `reqresv`, `rootonly`, etc.
- **Job Filter Syntax**: Select jobs by filter for delete and update operations
  - `user=<name>` - jobs by a specific user
  - `account=<name>` - jobs charged to a specific account
  - `partition=<name>` - jobs in a specific partition
  - `state=<state>` - jobs with a specific state (pending, running, etc.)
  - `name=<pattern>` - jobs matching a name pattern
  - `nodes=<nodelist>` - jobs running on specific nodes
  - `reservation=<name>` - jobs using a specific reservation
  - Example: `slurm-cli delete jobs user=john state=pending`
  - Example: `slurm-cli update jobs partition=gpu priority=100`
- **Autocomplete Cache Auto-Update**: Cache is automatically refreshed when missing or outdated
  - Set `SLURM_CLI_NO_CACHE_UPDATE=1` to disable automatic updates
  - Cache timeout: 60 seconds
- **Single-Key Confirmations**: All confirmation prompts (y/N) respond immediately without requiring Enter
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
