# Associations

Manage Slurm user-account associations.

## Overview

Associations link users to accounts and define their resource limits and QoS access within that account context.

## Show Associations

```bash
# Show all associations
slurm-cli show associations

# Show associations for a user
slurm-cli show associations user=testuser

# Show associations for an account
slurm-cli show associations account=myaccount

# JSON output
slurm-cli show associations --json
```

## Update Associations

### Simple Mode

```bash
# Update fairshare
slurm-cli modify associations user=testuser account=myaccount set fairshare=100

# Update QoS
slurm-cli modify associations user=testuser account=myaccount set qos=high

# Update max jobs
slurm-cli modify associations user=testuser account=myaccount set maxjobs=50
```

### WHERE/SET Mode

```bash
# Update all associations in an account
slurm-cli modify associations account=oldaccount set defaultqos=normal

# Update by user
slurm-cli modify associations user=testuser set fairshare=100
```

## Available Fields

| Field | Description |
|-------|-------------|
| `user` | Username |
| `account` | Account name |
| `cluster` | Cluster name |
| `partition` | Partition name |
| `parent` | Parent account |
| `fairshare` | Fairshare factor |
| `shares` | Share allocation |
| `grp_jobs` | Group job limit |
| `grp_submit` | Group submit limit |
| `grp_tres` | Group TRES limits |
| `grp_wall` | Group wall time limit |
| `max_jobs` | Max running jobs |
| `max_submit` | Max submitted jobs |
| `max_tres_pj` | Max TRES per job |
| `max_tres_pu` | Max TRES per user |
| `max_wall_pj` | Max wall time per job |
| `qos` | Allowed QoS list |
| `default_qos` | Default QoS |

## Examples

### View User's Associations

```bash
slurm-cli show associations user=testuser --profile-str='associations.columns=user,account,fairshare,qos'
```

### Set Resource Limits

```bash
slurm-cli modify associations user=testuser account=myaccount set \
    maxjobs=20 \
    maxsubmit=50 \
    maxtrespj=cpu=64,mem=256G
```

### Update QoS Access

```bash
# Set allowed QoS
slurm-cli modify associations user=testuser account=myaccount set qos=normal,high

# Set default QoS
slurm-cli modify associations user=testuser account=myaccount set defaultqos=normal
```

### Bulk Update

```bash
# Set fairshare for all users in account
slurm-cli modify associations account=myaccount set fairshare=100
```

## Association Hierarchy

```
cluster
└── account (root)
    ├── account (engineering)
    │   ├── user (alice) - association
    │   └── user (bob) - association
    └── account (research)
        └── user (charlie) - association
```

## Related Commands

- [Users](users.md) - User management
- [Accounts](accounts.md) - Account management
- [QoS](qos.md) - QoS settings

