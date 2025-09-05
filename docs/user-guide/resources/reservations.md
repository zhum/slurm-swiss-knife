# Reservations

Manage Slurm resource reservations.

## Show Reservations

```bash
# Show all reservations
slurm-cli show reservations

# Show specific reservation
slurm-cli show reservations myres

# JSON output
slurm-cli show reservations --json
```

## Create Reservations

```bash
# Reserve nodes for user
slurm-cli create reservations myres \
    starttime=now \
    duration=1-00:00:00 \
    nodecnt=4 \
    users=testuser

# Reserve specific nodes
slurm-cli create reservations gpures \
    starttime=2024-01-15T09:00:00 \
    endtime=2024-01-15T17:00:00 \
    nodes=gpu[001-004] \
    users=researcher

# Reserve for account
slurm-cli create reservations teamres \
    start=now \
    duration=4:00:00 \
    nodecnt=10 \
    accounts=engineering
```

## Update Reservations

```bash
# Extend duration
slurm-cli update reservations myres duration=2-00:00:00

# Add users
slurm-cli update reservations myres users+=newuser

# Change end time
slurm-cli update reservations myres endtime=2024-01-20T18:00:00

# Add nodes to reservation
slurm-cli update reservations myres nodes+=node005,node006

# Remove nodes from reservation
slurm-cli update reservations myres nodes-=node001

# Add nodes using filter
slurm-cli update reservations myres nodes+=state=idle

# Add nodes from a partition
slurm-cli update reservations myres nodes+=partition=gpu
```

## Delete Reservations

```bash
# Delete with confirmation
slurm-cli delete reservations myres

# Delete without confirmation
slurm-cli delete reservations myres --yes
```

## Available Fields

| Field | Description |
|-------|-------------|
| `name` | Reservation name |
| `state` | Reservation state |
| `starttime` | Start time |
| `endtime` | End time |
| `duration` | Duration |
| `nodes` | Reserved nodes |
| `nodecnt` | Node count |
| `corecnt` | Core count |
| `users` | Allowed users |
| `accounts` | Allowed accounts |
| `features` | Required features |
| `flags` | Reservation flags |
| `partition` | Target partition |
| `tres` | TRES specification |

## Time Aliases

For convenience, these aliases are supported:

| Alias | Actual Field |
|-------|--------------|
| `start` | `starttime` |
| `end` | `endtime` |

```bash
# These are equivalent:
slurm-cli create reservations myres start=now duration=1:00:00 ...
slurm-cli create reservations myres starttime=now duration=1:00:00 ...
```

## Time Formats

Supported time formats:

| Format | Example | Description |
|--------|---------|-------------|
| `now` | `now` | Current time |
| `HH:MM:SS` | `14:30:00` | Today at time |
| `YYYY-MM-DD` | `2024-01-15` | Date at midnight |
| `YYYY-MM-DDTHH:MM:SS` | `2024-01-15T14:30:00` | Full datetime |

Duration formats:

| Format | Example | Description |
|--------|---------|-------------|
| `D-HH:MM:SS` | `1-12:00:00` | 1 day, 12 hours |
| `HH:MM:SS` | `04:00:00` | 4 hours |
| `minutes` | `120` | 120 minutes |

## Reservation Flags

| Flag | Description |
|------|-------------|
| `MAINT` | Maintenance reservation |
| `OVERLAP` | Allow overlapping reservations |
| `IGNORE_JOBS` | Don't move running jobs |
| `DAILY` | Daily recurring |
| `WEEKLY` | Weekly recurring |
| `STATIC_ALLOC` | Static node allocation |
| `REPLACE` | Replace existing reservation |
| `PART_NODES` | Use partition nodes |
| `FLEX` | Flexible timing |
| `NO_HOLD_JOBS_AFTER_END` | Don't hold jobs at end |

## Examples

### Maintenance Window

```bash
slurm-cli create reservations maintenance \
    starttime=2024-01-20T00:00:00 \
    duration=8:00:00 \
    nodes=ALL \
    flags=MAINT \
    users=root
```

### GPU Reservation

```bash
slurm-cli create reservations gpures \
    start=now \
    duration=4:00:00 \
    partition=gpu \
    nodecnt=2 \
    features=v100 \
    users=researcher
```

### Recurring Weekly

```bash
slurm-cli create reservations weekly_backup \
    starttime=2024-01-15T02:00:00 \
    duration=2:00:00 \
    nodecnt=1 \
    flags=WEEKLY \
    users=backup
```

### Team Reservation

```bash
slurm-cli create reservations team_sprint \
    start=now \
    end=2024-01-19T18:00:00 \
    nodecnt=20 \
    accounts=engineering \
    flags=FLEX
```

### View Active Reservations

```bash
slurm-cli show reservations --profile-str='reservations.columns=name,state,starttime,endtime,nodes,users'
```

## Node Filter Syntax

Instead of specifying explicit node names, you can use filter syntax:

```bash
# Reserve all nodes from a partition
slurm-cli create reservations maint \
    nodes=partition=gpu \
    starttime=now duration=2:00:00 users=admin

# Update reservation to use nodes from another partition
slurm-cli update reservations maint nodes=partition=cpu

# Reserve currently idle nodes
slurm-cli create reservations idle_test \
    nodes=state=idle \
    starttime=now duration=1:00:00 users=test
```

Available filters:

| Filter | Example | Description |
|--------|---------|-------------|
| `partition=` | `nodes=partition=gpu` | All nodes from partition |
| `state=` | `nodes=state=idle` | Nodes with specific state |
| `user=` | `nodes=user=john` | Nodes running user's jobs |
| `reservation=` | `nodes=reservation=other` | Nodes from another reservation |

## Related Commands

- [Nodes](nodes.md) - View available nodes
- [Partitions](partitions.md) - Partition information

