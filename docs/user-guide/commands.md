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

## Global Options

These options work with any command:

| Option | Description |
|--------|-------------|
| `--help`, `-h` | Show help message |
| `--version` | Show version |
| `--yes`, `-y` | Skip confirmations (delete/update) |

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

