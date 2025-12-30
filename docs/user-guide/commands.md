# Commands Overview

Slurm CLI provides a unified interface for managing Slurm resources through four main commands.

## Command Structure

```
slurm-cli <command> <resource> [name] [options] [key=value ...]
```

## Show Command

Display information about Slurm resources.

**Aliases:** `show`, `sh`, `s`, `list`, `get`

### Syntax

```bash
slurm-cli show <resource> [name] [filters...] [options]
```

### Options

| Option | Description |
|--------|-------------|
| `--json` | Output in JSON format |
| `--csv` | Output in CSV format |
| `--delimiter=CHAR` | CSV delimiter (default: `;`) |
| `--profile=NAME` | Use named output profile |
| `--profile-str=STR` | Inline profile specification |
| `--zebra` | Zebra striping for tables |
| `--tree`, `-T` | Hierarchical tree view (associations only) |
| `--indent=STR` | Indentation string for tree mode (default: two spaces) |
| `--force-cache-update` | Refresh cached data |

### Examples

```bash
# Show all partitions
slurm-cli show partitions

# Show specific partition
slurm-cli show partitions gpu

# Show in JSON format
slurm-cli show qos --json

# Show with filter
slurm-cli show users defaultaccount=myaccount

# Show all fields
slurm-cli show users --profile-str='*'
```

## Create Command

Create new Slurm resources.

**Aliases:** `create`, `c`, `add`, `new`

### Syntax

```bash
slurm-cli create <resource> <name> [key=value ...]
```

### Examples

```bash
# Create user
slurm-cli create users newuser account=myaccount defaultaccount=myaccount

# Create account
slurm-cli create accounts myaccount organization=myorg parent=root

# Create QoS
slurm-cli create qos highprio priority=100 maxwall=24:00:00

# Create reservation
slurm-cli create reservations myres starttime=now duration=1-00:00:00 \
    nodecnt=4 users=testuser

# Create with verbose output
slurm-cli create accounts newaccount --verbose
```

## Update Command

Modify existing Slurm resources.

**Aliases:** `update`, `u`, `edit`, `mod`, `modify`

### Syntax

Two modes are supported:

**Simple Mode (by name):**
```bash
slurm-cli modify <resource> <name> set key=value [key=value ...]
```

**WHERE/SET Mode (bulk update):**
```bash
slurm-cli modify <resource> where_key=value [...] set key=value [...]
```

### Options

| Option | Description |
|--------|-------------|
| `--yes`, `-y` | Skip confirmation prompt |
| `--dry-run` | Show what would be changed |
| `--verbose`, `-v` | Verbose output |

### Examples

```bash
# Simple update by name
slurm-cli modify users testuser set adminlevel=admin

# Update multiple fields
slurm-cli modify qos normal set priority=50 maxwall=48:00:00

# WHERE/SET mode - bulk update
slurm-cli modify users account=oldaccount set defaultaccount=newaccount

# Dry run - see what would change
slurm-cli modify qos priority=100 set priority=200 --dry-run

# Skip confirmation
slurm-cli modify accounts myaccount set description="Updated" --yes
```

## Delete Command

Remove Slurm resources.

**Aliases:** `delete`, `d`, `del`, `rm`, `remove`

### Syntax

```bash
slurm-cli delete <resource> <name> [options]
```

### Options

| Option | Description |
|--------|-------------|
| `--yes`, `-y` | Skip confirmation prompt |
| `--verbose`, `-v` | Verbose output |

### Examples

```bash
# Delete with confirmation
slurm-cli delete users olduser

# Delete without confirmation
slurm-cli delete users olduser --yes

# Short form
slurm-cli del qos oldqos -y
```

## Node Filter Syntax

When specifying nodes in commands (e.g., for partitions or reservations), you can use filter syntax instead of explicit node names:

| Filter | Description |
|--------|-------------|
| `partition=NAME` | All nodes from the specified partition |
| `state=STATE` | All nodes with the specified state (idle, alloc, drain, etc.) |
| `user=USERNAME` | All nodes running jobs by the specified user |
| `reservation=NAME` | All nodes in the specified reservation |

### Examples

```bash
# Update reservation to use all nodes from partition 'cpu'
slurm-cli update reservations maint nodes=partition=cpu

# Update partition to include nodes from another partition
slurm-cli update partitions backup nodes=partition=gpu

# Create reservation with idle nodes
slurm-cli create reservations idle_test nodes=state=idle starttime=now duration=1:00:00

# Show nodes used by a specific user
slurm-cli show nodes user=john
```

The node filter is resolved at command execution time, so it always uses the current state of the cluster.

## Global Options

These options work with any command:

| Option | Description |
|--------|-------------|
| `--help`, `-h` | Show help message |
| `--version` | Show version |
| `--yes`, `-y` | Skip confirmations (delete/update) |
| `--dry-run` | Show what would be done without making changes |
| `--no-dry-run` | Override `SLURM_CLI_DRYRUN` env var |

## Environment Variables

| Variable | Description |
|----------|-------------|
| `SLURM_CLI_DRYRUN` | Set to `y`, `yes`, `1`, or `true` to enable dry-run mode globally |

### Dry-Run Mode

Dry-run mode shows what would be done without making actual changes. It can be enabled in three ways:

1. **Environment variable**: `SLURM_CLI_DRYRUN=y`
1. **Global option**: `slurm-cli --dry-run ...`
1. **Command option**: `slurm-cli delete ... --dry-run`

The `--no-dry-run` option overrides the environment variable:

```bash
# Enable dry-run via env var
export SLURM_CLI_DRYRUN=y
slurm-cli delete users testuser  # Shows dry-run output

# Override to actually execute
slurm-cli --no-dry-run delete users testuser  # Actually deletes
```

## Command Aliases Reference

### Verb Aliases

| Command | Aliases |
|---------|---------|
| `show` | `sh`, `s`, `list`, `get` |
| `create` | `c`, `add`, `new` |
| `update` | `u`, `edit`, `mod`, `modify` |
| `delete` | `d`, `del`, `rm`, `remove` |

### Resource Aliases

| Resource | Aliases |
|----------|---------|
| `partitions` | `part`, `parts` |
| `nodes` | `node` |
| `users` | `user` |
| `accounts` | `acc`, `account` |
| `qos` | `q` |
| `reservations` | `res`, `reservation` |
| `associations` | `assoc`, `association` |
| `coordinators` | `coord`, `coordinator` |
| `events` | `event`, `ev` |

## Control Commands

These commands directly interact with the Slurm controller (slurmctld).

### Version

Show slurm-cli and Slurm version information.

**Aliases:** `version`, `ver`, `v`

```bash
slurm-cli version
slurm-cli ver
```

### Reconfigure

Force slurmctld to re-read its configuration file.

**Aliases:** `reconfigure`, `reconf`, `rec`

```bash
slurm-cli reconfigure
slurm-cli reconf
slurm-cli rec -v  # verbose output
```

### Ping

Check if the Slurm controller is responding.

**Aliases:** `ping`, `pi`

```bash
slurm-cli ping
slurm-cli pi
```

### Takeover

Cause the backup slurmctld to take over as the primary controller.

**Aliases:** `takeover`, `tak`, `ta`

```bash
slurm-cli takeover
slurm-cli tak -v  # verbose output
```

**Note:** This command should only be run on a backup controller.

### Token

Generate a JWT authentication token.

**Aliases:** `token`, `tok`, `to`

```bash
# Generate token with default lifespan
slurm-cli token

# Generate token with 1 hour lifespan
slurm-cli token lifespan=1h

# Generate token with specific time format
slurm-cli token lifespan=1:30:00    # 1 hour 30 minutes
slurm-cli token lifespan=30m        # 30 minutes
slurm-cli token lifespan=2d         # 2 days

# Generate token for another user (requires admin)
slurm-cli token username=john

# Combine options
slurm-cli token lifespan=2h username=admin

# Generate token with unlimited lifespan
slurm-cli token lifespan=infinite
```

**Lifespan formats:**
| Format | Example | Description |
|--------|---------|-------------|
| Seconds | `3600` | Direct seconds |
| HH:MM:SS | `1:30:00` | Hours:minutes:seconds |
| MM:SS | `30:00` | Minutes:seconds |
| D-HH:MM:SS | `1-12:00:00` | Days-hours:minutes:seconds |
| Nh/Nm/Ns/Nd | `1h`, `30m`, `45s`, `2d` | Hours, minutes, seconds, days |
| infinite | `infinite`, `inf` | No expiration (if allowed) |

## Special Commands

### Autocomplete

Generate bash completion script:

```bash
slurm-cli autocomplete
```

### Help

Show help for any command:

```bash
slurm-cli --help
slurm-cli show --help
slurm-cli show partitions --help
```

