# Users

Manage Slurm user accounts.

## Show Users

```bash
# Show all users
slurm-cli show users

# Show specific user
slurm-cli show users testuser

# Filter by account
slurm-cli show users defaultaccount=myaccount

# Filter by admin level
slurm-cli show users adminlevel=Admin

# JSON output
slurm-cli show users --json
```

## Create Users

```bash
# Basic user creation
slurm-cli create users newuser account=myaccount defaultaccount=myaccount

# With additional options
slurm-cli create users newuser \
    account=myaccount \
    defaultaccount=myaccount \
    adminlevel=None \
    partition=batch
```

## Update Users

### Simple Mode (by name)

```bash
# Update admin level
slurm-cli modify users testuser set adminlevel=admin

# Update default account
slurm-cli modify users testuser set defaultaccount=newaccount

# Rename user
slurm-cli modify users olduser set newname=newuser

# Multiple fields
slurm-cli modify users testuser set adminlevel=operator defaultaccount=admin
```

### WHERE/SET Mode (bulk update)

```bash
# Update all users in an account
slurm-cli modify users account=oldaccount set defaultaccount=newaccount

# Update by admin level
slurm-cli modify users adminlevel=None set partition=batch

# Multiple conditions
slurm-cli modify users cluster=main account=test set defaultaccount=prod
```

## Delete Users

```bash
# Delete with confirmation
slurm-cli delete users olduser

# Delete without confirmation
slurm-cli delete users olduser --yes
```

## Available Fields

| Field | Description |
|-------|-------------|
| `name` | Username |
| `administrator_level` | Admin level (None/Admin/Operator) |
| `default.account` | Default account |
| `default.wckey` | Default WCKey |
| `associations` | User associations |

## Filter Aliases

| Alias | Actual Field |
|-------|--------------|
| `user` | `name` |
| `username` | `name` |
| `account` | `default.account` |
| `defaultaccount` | `default.account` |
| `admin` | `administrator_level` |
| `adminlevel` | `administrator_level` |

## Admin Levels

| Level | Description |
|-------|-------------|
| `None` | Regular user |
| `Operator` | Can manage jobs/nodes |
| `Admin` | Full administrative access |

## Update Options

### SET Options

| Option | Description |
|--------|-------------|
| `adminlevel` | Admin level (none/admin/operator) |
| `defaultaccount` | Default account |
| `defaultwckey` | Default WCKey |
| `newname` | Rename user |
| `partition` | Default partition |
| `fairshare` | Fairshare value |

### WHERE Options

| Option | Description |
|--------|-------------|
| `account` | Filter by account |
| `adminlevel` | Filter by admin level |
| `cluster` | Filter by cluster |
| `defaultaccount` | Filter by default account |
| `defaultwckey` | Filter by WCKey |
| `name` | Filter by name |
| `partition` | Filter by partition |

## Examples

### List All Admins

```bash
slurm-cli show users adminlevel=Admin
```

### Export User List

```bash
slurm-cli show users --csv > users.csv
```

### Bulk Update Users

```bash
# Move all users from old account to new
slurm-cli modify users defaultaccount=oldaccount set defaultaccount=newaccount
```

### Create Service User

```bash
slurm-cli create users serviceuser \
    account=service \
    defaultaccount=service \
    adminlevel=None
```

## Related Commands

- [Accounts](accounts.md) - Manage user accounts hierarchy
- [Associations](associations.md) - User-account associations
- [Coordinators](coordinators.md) - Account coordinators

