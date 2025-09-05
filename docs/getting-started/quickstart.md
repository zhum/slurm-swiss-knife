# Quick Start

This guide will help you get started with Slurm CLI in just a few minutes.

## Basic Usage

### Show Resources

The most common operation is viewing resources:

```bash
# Show all partitions
slurm-cli show partitions

# Show all QoS
slurm-cli show qos

# Show all users
slurm-cli show users

# Show all accounts
slurm-cli show accounts
```

### Output Formats

Choose your preferred output format:

```bash
# Pretty table (default)
slurm-cli show partitions

# JSON format
slurm-cli show partitions --json

# CSV format
slurm-cli show partitions --csv

# CSV with custom delimiter
slurm-cli show partitions --csv --delimiter='|'
```

### Filtering

Filter resources by any field:

```bash
# Show specific partition
slurm-cli show partitions gpu

# Show users in an account
slurm-cli show users defaultaccount=general

# Show QoS by priority
slurm-cli show qos priority=100
```

## Creating Resources

### Create a User

```bash
slurm-cli create users newuser account=myaccount defaultaccount=myaccount
```

### Create an Account

```bash
slurm-cli create accounts myaccount organization=myorg parent=root
```

### Create a QoS

```bash
slurm-cli create qos highpriority priority=100 maxwall=24:00:00
```

### Create a Reservation

```bash
slurm-cli create reservations myres starttime=now duration=1-00:00:00 \
    nodecnt=4 users=testuser
```

## Updating Resources

### Simple Update (by name)

```bash
# Update user
slurm-cli modify users testuser set adminlevel=admin

# Update QoS
slurm-cli modify qos normal set priority=50

# Update account
slurm-cli modify accounts myaccount set description="My Account"
```

### Bulk Update (WHERE/SET syntax)

```bash
# Update all users in an account
slurm-cli modify users account=oldaccount set defaultaccount=newaccount

# Update QoS by flag
slurm-cli modify qos flags=NoDecay set priority=100
```

## Deleting Resources

```bash
# Delete user (with confirmation)
slurm-cli delete users testuser

# Delete without confirmation
slurm-cli delete users testuser --yes

# Delete QoS
slurm-cli delete qos oldqos --yes
```

## Command Aliases

Slurm CLI supports short aliases for faster typing:

| Full Command | Aliases |
|--------------|---------|
| `show` | `sh`, `s`, `list`, `get` |
| `create` | `c`, `add`, `new` |
| `update` | `u`, `edit`, `mod`, `modify` |
| `delete` | `d`, `del`, `rm`, `remove` |

Resource aliases:

| Resource | Aliases |
|----------|---------|
| `partitions` | `part`, `parts` |
| `nodes` | `node` |
| `accounts` | `acc`, `account` |
| `users` | `user` |
| `qos` | `q` |
| `reservations` | `res`, `reservation` |
| `associations` | `assoc`, `association` |
| `coordinators` | `coord`, `coordinator` |
| `events` | `event`, `ev` |

Example using aliases:

```bash
# These are equivalent:
slurm-cli show partitions
slurm-cli sh part
slurm-cli s parts
```

## Using Profiles

Customize output with profiles:

```bash
# Use a named profile
slurm-cli show partitions --profile=compact

# Use inline profile string
slurm-cli show users --profile-str='users.columns=name,adminlevel'

# Show all fields
slurm-cli show users --profile-str='*'
```

## Next Steps

- [Set up autocomplete](autocomplete.md) for tab completion
- [Learn about profiles](../user-guide/profiles.md) for custom output
- [Explore all commands](../user-guide/commands.md)

