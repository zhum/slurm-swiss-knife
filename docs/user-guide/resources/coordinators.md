# Coordinators

Manage Slurm account coordinators.

## Overview

Coordinators are users who can manage other users within their designated accounts. They can:

- Add/remove users from their accounts
- Modify user associations
- Manage sub-accounts

## Show Coordinators

```bash
# Show all coordinators
slurm-cli show coordinators

# Show coordinators for an account
slurm-cli show coordinators account=myaccount

# JSON output
slurm-cli show coordinators --json
```

## Create Coordinators

```bash
# Add coordinator to account (positional syntax)
slurm-cli create coordinators myaccount alice

# Using key=value syntax
slurm-cli create coordinators account=myaccount name=alice

# Add multiple coordinators
slurm-cli create coordinators myaccount name+=alice name+=bob

# Add/remove coordinators with += and -=
slurm-cli create coordinators myaccount name+=newuser name-=olduser
```

## Delete Coordinators

```bash
# Remove coordinator from account
slurm-cli delete coordinators alice account=myaccount --yes

# Remove by account filter
slurm-cli delete coordinators account=myaccount name=alice --yes
```

## Available Fields

| Field | Description |
|-------|-------------|
| `name` | Coordinator username |
| `account` | Account being coordinated |
| `cluster` | Cluster name |

## Examples

### List Account Coordinators

```bash
slurm-cli show coordinators account=engineering
```

### Add Project Lead as Coordinator

```bash
slurm-cli create coordinators project_x lead_user
```

### Transfer Coordination

```bash
# Remove old coordinator and add new one in single command
slurm-cli create coordinators myaccount name-=old_lead name+=new_lead

# Or separate commands
slurm-cli delete coordinators old_lead account=myaccount --yes
slurm-cli create coordinators myaccount new_lead
```

## Coordinator Permissions

Coordinators can:

| Action | Scope |
|--------|-------|
| Add users | Their accounts and sub-accounts |
| Remove users | Their accounts and sub-accounts |
| Modify associations | Their accounts and sub-accounts |
| View usage | Their accounts and sub-accounts |

Coordinators cannot:

- Create new accounts
- Modify account limits
- Access other accounts
- Modify their own coordinator status

## Related Commands

- [Accounts](accounts.md) - Account management
- [Users](users.md) - User management
- [Associations](associations.md) - User-account associations

