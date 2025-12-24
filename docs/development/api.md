# API Reference

This page documents the Python API for extending Slurm CLI.

## Base Classes

### BaseSlurmResource

Base class for all Slurm resources.

```python
from slurm_cli.utils.base_resource import BaseSlurmResource

class BaseSlurmResource:
    """Base class for Slurm resource handlers."""
    
    valid_args: Dict[str, Dict[str, str]] = {}
    arg_aliases: Dict[str, str] = {}
    
    @classmethod
    def get_profile_fields(cls) -> dict:
        """Return field names and descriptions for profiles."""
        return {}
    
    @classmethod
    def _check_args(cls, kwargs, set_dict, add_dict, delete_dict) -> bool:
        """Validate and categorize arguments."""
        pass
```

## Resource Classes

### User

```python
from slurm_cli.utils.users import User

# Show users
User.show(name="testuser", style="json")

# Create user
User.create("newuser", account="myaccount", verbose=True)

# Update user
User.update("testuser", adminlevel="admin", verbose=True)

# Bulk update
User.update(
    "",
    where_conditions=["account=test"],
    set_values=["adminlevel=admin"],
)

# Delete user
User.delete("olduser")
```

### Account

```python
from slurm_cli.utils.accounts import Account

# Show accounts
Account.show(name="myaccount", style="pretty")

# Create account
Account.create("newaccount", organization="myorg", parent="root")

# Update account
Account.update("myaccount", description="Updated", verbose=True)

# Delete account
Account.delete("oldaccount")
```

### Qos

```python
from slurm_cli.utils.qos import Qos

# Show QoS
Qos.show(field="normal", style="json")

# Create QoS
Qos.create("highprio", priority=100, maxwall="24:00:00")

# Update QoS
Qos.update("normal", priority=50, preemptmode="SUSPEND")

# Delete QoS
Qos.delete("oldqos")
```

### Reservation

```python
from slurm_cli.utils.reservations import Reservation

# Show reservations
Reservation.show(name="myres")

# Create reservation
Reservation.create(
    "myres",
    starttime="now",
    duration="1-00:00:00",
    nodecnt=4,
    users="testuser",
)

# Update reservation
Reservation.update("myres", endtime="2024-01-20T18:00:00")

# Delete reservation
Reservation.delete("myres")
```

### Node

```python
from slurm_cli.utils.nodes import Node

# Show nodes
Node.show(name="node001", style="json")

# Update node
Node.update("node001", state="DRAIN", reason="Maintenance")
```

### Partition

```python
from slurm_cli.utils.partitions import Partition

# Show partitions
Partition.show(name="gpu", style="pretty")

# Update partition
Partition.update("gpu", state="UP")
```

## Constants

### User Constants

```python
from slurm_cli.utils.users import (
    USER_OPTIONS,              # Available user fields
    USER_UPDATE_SET_OPTIONS,   # SET options for update
    USER_UPDATE_WHERE_OPTIONS, # WHERE options for update
    VALID_ADMIN_LEVELS,        # none, admin, operator
)
```

### QoS Constants

```python
from slurm_cli.utils.qos import (
    QOS_OPTIONS,          # Available QoS fields
    QOS_FLAGS,            # Valid QoS flags
    PREEMPT_MODE_VALUES,  # OFF, CANCEL, GANG, REQUEUE, SUSPEND, WITHIN
)
```

### Account Constants

```python
from slurm_cli.utils.accounts import (
    ACCOUNT_OPTIONS,  # Available account fields
)
```

## Profile Utilities

```python
from slurm_cli.utils.profiles import (
    get_profile_config,     # Load profile configuration
    get_resource_fields,    # Get fields for all resources
    format_with_template,   # Format data with template
    show_profile_help,      # Display profile help
)

# Get profile configuration (returns columns, styles, template, sort_field, sort_ascending)
columns, styles, template, sort_field, sort_asc = get_profile_config(
    profile="default",
    resource_type="users",
    profile_str="users.columns=name+,adminlevel",  # + suffix for ascending sort
)
# sort_field = "name", sort_asc = True

# Get all resource fields
fields = get_resource_fields()
# {"users": {"name": "...", ...}, "accounts": {...}, ...}
```

## CLI Entry Point

```python
from slurm_cli.cli import main

# Run CLI
if __name__ == "__main__":
    main()
```

## Extending

### Custom Resource

```python
from slurm_cli.utils.base_resource import BaseSlurmResource

class MyResource(BaseSlurmResource):
    """Custom resource handler."""
    
    valid_args = {
        "name": {"type": "string", "desc": "Resource name"},
        "value": {"type": "integer", "desc": "Value"},
    }
    
    @classmethod
    def get_profile_fields(cls) -> dict:
        return {
            "name": "Resource name",
            "value": "Resource value",
        }
    
    @classmethod
    def show(cls, name=None, style="pretty", **kwargs):
        """Display resources."""
        # Implementation
        pass
    
    @classmethod
    def create(cls, name, verbose=False, **kwargs):
        """Create resource."""
        # Implementation
        pass
```

### Custom Autocomplete

```python
@classmethod
def generate_autocomplete_options(cls) -> str:
    """Generate bash autocomplete script."""
    return """
_my_resource_autocomplete() {
    local cur="${COMP_WORDS[COMP_CWORD]}"
    COMPREPLY=($(compgen -W "name= value=" -- "$cur"))
}
"""
```

## Utility Functions

```python
from slurm_cli.utils.utils import console

# Rich console for output
console.print("[green]Success![/green]")
console.print("[red]Error:[/red] Something went wrong")

# Tables
from rich.table import Table
table = Table()
table.add_column("Name")
table.add_row("value")
console.print(table)
```

