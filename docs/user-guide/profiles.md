# Output Profiles

Output profiles allow you to customize how slurm-cli displays resource information.

## Profile Basics

Profiles control:

- Which columns are displayed
- Column order
- Value formatting and styling
- Template-based custom output

## Using Profiles

### Named Profiles

Use predefined profiles with `--profile`:

```bash
slurm-cli show partitions --profile=compact
slurm-cli show users --profile=detailed
```

### Inline Profiles

Specify profile options inline with `--profile-str`:

```bash
# Show specific columns
slurm-cli show users --profile-str='users.columns=name,adminlevel'

# Show all columns
slurm-cli show qos --profile-str='*'

# Custom template
slurm-cli show accounts --profile-str='accounts.template=[cyan]{name}[/] - {description}'
```

## Profile Configuration Files

Profiles are loaded from:

1. `/etc/slurm/cli.profiles` (system-wide)
2. `~/.config/slurm-cli.profiles` (user-specific)

### Configuration Syntax

```ini
# Profile name in brackets
[compact]
# Resource-specific settings
partitions.columns=name,state,nodes
qos.columns=name,priority
users.columns=name,adminlevel

[detailed]
partitions.columns=name,state,nodes,cpus,memory,timelimit
users.columns=name,adminlevel,default.account,associations

[oneline]
partitions.template=[cyan]{name}[/]: {state} ({nodes} nodes)
```

## Profile Options

### Columns

Specify which columns to display:

```bash
# Comma-separated column names
--profile-str='users.columns=name,adminlevel,default.account'

# All columns
--profile-str='*'
```

### Templates

Use Rich markup for formatted output:

```bash
# Basic template
--profile-str='users.template={name} - {adminlevel}'

# With colors
--profile-str='users.template=[cyan]{name}[/] ([yellow]{adminlevel}[/])'

# Multi-line
--profile-str='users.template={name}\n  Admin: {adminlevel}\n  Account: {default.account}'
```

### Styles

Apply Rich styles to columns:

```bash
--profile-str='users.styles.name=cyan bold,users.styles.adminlevel=yellow'
```

### Sorting

Add `+` or `-` suffix to a column name to sort by that column:

```bash
# Sort by name ascending
slurm-cli show accounts --profile-str='name+,description'

# Sort by priority descending
slurm-cli show qos --profile-str='priority-,name'

# Sort jobs by job_id descending
slurm-cli show jobs --profile-str='job_id-,user_name,job_state'
```

Only the first column with a sort marker is used for sorting.

In configuration files:

```ini
[sorted]
accounts.columns=name+,description,organization
qos.columns=priority-,name,flags
jobs.columns=job_id-,user_name,partition,job_state
```

**Note:** For hierarchical resources (like associations in tree mode), sorting is applied within each hierarchy level independently.

## Available Fields by Resource

### Users

| Field | Description |
|-------|-------------|
| `name` | Username |
| `adminlevel` / `administrator_level` | Admin level (None/Admin/Operator) |
| `default.account` | Default account |
| `default.wckey` | Default WCKey |
| `associations` | User associations |

### Accounts

| Field | Description |
|-------|-------------|
| `name` | Account name |
| `description` | Account description |
| `organization` | Organization name |
| `coordinators` | Account coordinators |
| `parent` | Parent account |

### QoS

| Field | Description |
|-------|-------------|
| `name` | QoS name |
| `id` | QoS ID |
| `priority` | Priority value |
| `usage_factor` | Usage factor |
| `flags` | QoS flags |
| `preempt_mode` | Preemption mode |
| `max_wall` | Max wall time |
| `max_jobs_per_user` | Max jobs per user |
| `max_tres_per_job` | Max TRES per job |

### Partitions

| Field | Description |
|-------|-------------|
| `name` | Partition name |
| `state` | Partition state |
| `nodes` | Number of nodes |
| `cpus` | Total CPUs |
| `memory` | Total memory |
| `timelimit` | Default time limit |
| `maxtime` | Maximum time limit |

### Nodes

| Field | Description |
|-------|-------------|
| `name` | Node name |
| `state` | Node state |
| `cpus` | Number of CPUs |
| `memory` | Memory (MB) |
| `partitions` | Assigned partitions |
| `reason` | State reason |

### Reservations

| Field | Description |
|-------|-------------|
| `name` | Reservation name |
| `state` | Reservation state |
| `starttime` | Start time |
| `endtime` | End time |
| `duration` | Duration |
| `nodes` | Reserved nodes |
| `users` | Allowed users |

## Rich Markup Reference

Templates support Rich markup:

### Colors

```
[red]text[/]
[green]text[/]
[blue]text[/]
[cyan]text[/]
[yellow]text[/]
[magenta]text[/]
```

### Styles

```
[bold]text[/]
[italic]text[/]
[underline]text[/]
[strike]text[/]
```

### Combined

```
[bold cyan]text[/]
[red on white]text[/]
```

## Example Profiles

### Compact Admin View

```ini
[admin]
users.columns=name,adminlevel,default.account
users.styles.adminlevel=yellow
accounts.columns=name,organization,parent
qos.columns=name,priority,max_wall
```

### Detailed Output

```ini
[detailed]
partitions.template=[bold cyan]{name}[/]\n  State: {state}\n  Nodes: {nodes}\n  CPUs: {cpus}\n  Memory: {memory}
```

### CSV-Friendly

```ini
[export]
users.columns=name,adminlevel,default.account,associations
```

## Help Command

View available fields for any resource:

```bash
# List fields for a specific resource
slurm-cli --list-fields=users
slurm-cli --list-fields=jobs
slurm-cli --list-fields=partitions

# List fields for all resources
slurm-cli --list-fields

# Alternative: use --profile-str=help with show command
slurm-cli show partitions --profile-str=help
slurm-cli show users --profile-str=help
```

