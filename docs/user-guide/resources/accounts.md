# Accounts

Manage Slurm account hierarchy.

## Show Accounts

```bash
# Show all accounts
slurm-cli show accounts

# Show specific account
slurm-cli show accounts myaccount

# Filter by organization
slurm-cli show accounts organization=nvidia

# JSON output
slurm-cli show accounts --json
```

## Create Accounts

```bash
# Basic account creation
slurm-cli create accounts newaccount organization=myorg

# With parent account
slurm-cli create accounts subaccount parent=myaccount organization=myorg

# With description
slurm-cli create accounts myaccount \
    organization=myorg \
    description="My account description"
```

## Update Accounts

### Simple Mode (by name)

```bash
# Update description
slurm-cli modify accounts myaccount set description="Updated description"

# Update organization
slurm-cli modify accounts myaccount set organization=neworg

# Multiple fields
slurm-cli modify accounts myaccount set description="New desc" fairshare=100
```

### WHERE/SET Mode (bulk update)

```bash
# Update all accounts in an organization
slurm-cli modify accounts organization=oldorg set organization=neworg

# Update by parent
slurm-cli modify accounts parent=root set fairshare=100
```

## Delete Accounts

```bash
# Delete with confirmation
slurm-cli delete accounts oldaccount

# Delete without confirmation
slurm-cli delete accounts oldaccount --yes
```

## Available Fields

| Field | Description |
|-------|-------------|
| `name` | Account name |
| `description` | Account description |
| `organization` | Organization name |
| `coordinators` | List of coordinators |
| `parent` | Parent account |
| `cluster` | Cluster name |
| `defaultqos` | Default QoS |
| `fairshare` | Fairshare factor |
| `grptres` | Group TRES limits |
| `maxjobs` | Max running jobs |
| `maxsubmitjobs` | Max submitted jobs |
| `maxwall` | Max wall time |

## Update Options

### SET Options

| Option | Description |
|--------|-------------|
| `description` | Account description |
| `organization` | Organization name |
| `parent` | Parent account |
| `defaultqos` | Default QoS |
| `fairshare` | Fairshare value |
| `grptres` | Group TRES limits |
| `maxjobs` | Max running jobs |
| `maxsubmitjobs` | Max submitted jobs |
| `maxwall` | Max wall time |

## Account Hierarchy

Slurm accounts form a tree structure:

```
root
├── engineering
│   ├── team_a
│   └── team_b
└── research
    ├── project_x
    └── project_y
```

### Create Hierarchy

```bash
# Create parent accounts
slurm-cli create accounts engineering organization=myorg parent=root
slurm-cli create accounts research organization=myorg parent=root

# Create child accounts
slurm-cli create accounts team_a organization=myorg parent=engineering
slurm-cli create accounts project_x organization=myorg parent=research
```

## Examples

### List All Accounts with Details

```bash
slurm-cli show accounts --profile-str='accounts.columns=name,organization,parent,coordinators'
```

### Find Accounts by Organization

```bash
slurm-cli show accounts organization=nvidia
```

### Export Account Structure

```bash
slurm-cli show accounts --json | jq '.accounts[] | {name, parent, organization}'
```

### Set Account Limits

```bash
slurm-cli modify accounts myaccount set \
    maxjobs=100 \
    maxsubmitjobs=500 \
    grptres=cpu=1000,mem=4000G
```

## Related Commands

- [Users](users.md) - Manage users in accounts
- [Associations](associations.md) - User-account associations
- [Coordinators](coordinators.md) - Account coordinators
- [QoS](qos.md) - Quality of Service settings

