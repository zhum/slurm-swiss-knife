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
# Add coordinator to account
slurm-cli create coordinators myaccount names=alice

# Add multiple coordinators
slurm-cli create coordinators myaccount names=alice,bob,charlie
```

## Delete Coordinators

```bash
# Remove coordinator from account
slurm-cli delete coordinators myaccount names=alice --yes

# Remove multiple coordinators
slurm-cli delete coordinators myaccount names=alice,bob --yes
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
slurm-cli create coordinators project_x names=lead_user
```

### Transfer Coordination

```bash
# Remove old coordinator
slurm-cli delete coordinators myaccount names=old_lead --yes

# Add new coordinator
slurm-cli create coordinators myaccount names=new_lead
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

