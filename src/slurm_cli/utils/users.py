"""Utilities for managing users."""

import json
import subprocess
from typing import Any, Dict, List, Optional

from rich.box import SIMPLE_HEAVY
from rich.table import Table

from .base_resource import BaseSlurmResource
from .profiles import get_profile_config
from .utils import console

# User configuration options (sacctmgr field names)
USER_OPTIONS: List[str] = [
    "Account",
    "AdminLevel",
    "Cluster",
    "DefaultAccount",
    "DefaultWCKey",
    "Name",
    "Partition",
    "QOS",
]

# Valid options for user update SET clause
USER_UPDATE_SET_OPTIONS: List[str] = [
    "adminlevel",
    "defaultaccount",
    "defaultwckey",
    "newname",
    "partition",
    "fairshare",
]

# Valid options for user update WHERE clause (filters)
USER_UPDATE_WHERE_OPTIONS: List[str] = [
    "account",
    "adminlevel",
    "cluster",
    "defaultaccount",
    "defaultwckey",
    "name",
    "partition",
]

# Valid admin levels
VALID_ADMIN_LEVELS: List[str] = ["none", "admin", "operator"]


class User(BaseSlurmResource):
    # Default column configuration for users
    DEFAULT_COLUMNS = [
        "name",
        "administrator_level",
        "default",
        "coordinators",
        "flags",
    ]
    DEFAULT_STYLES = {
        "name": "cyan",
        "administrator_level": "yellow",
        "default": "green",
        "coordinators": "magenta",
    }

    def __init__(self, name: str, **kwargs: Any):
        self.name = name
        self.kwargs = kwargs

    @classmethod
    def get_profile_fields(cls) -> dict:
        """Return field names and descriptions for profile templates."""
        return {
            "name": "Username",
            "administrator_level": "Admin level (None, Operator, Admin)",
            "default": "Default associations",
            "coordinators": "Coordinator accounts",
            "flags": "User flags",
            "associations": "User associations",
            "wckeys": "Workload characterization keys",
            "old_name": "Previous username (if renamed)",
        }

    # All available columns from sacctmgr users JSON output
    ALL_COLUMNS = [
        "name",
        "administrator_level",
        "default",
        "coordinators",
        "flags",
        "associations",
        "wckeys",
        "old_name",
    ]

    @classmethod
    def _get_column_config(
        cls,
        profile: str = "default",
        profile_str: Optional[str] = None,
    ) -> tuple:
        """Get column configuration from profile.

        Returns:
            Tuple of (columns, styles, template)
        """
        columns, styles, template = get_profile_config(
            profile, "users", profile_str
        )

        # Use all columns if profile specifies "*"
        if columns == "*":
            columns = cls.ALL_COLUMNS
        # Use default columns if no columns specified
        elif columns is None:
            columns = cls.DEFAULT_COLUMNS

        # Merge with default styles
        merged_styles = dict(cls.DEFAULT_STYLES)
        merged_styles.update(styles)

        return columns, merged_styles, template

    # Filter field aliases (user-friendly names -> actual JSON field names)
    FILTER_ALIASES: Dict[str, tuple] = {
        "user": ("name",),
        "username": ("name",),
        "defaultaccount": ("default", "account"),
        "defaultwckey": ("default", "wckey"),
        "account": ("default", "account"),
        "adminlevel": ("administrator_level",),
        "admin": ("administrator_level",),
    }

    @classmethod
    def _match_filter(
        cls, user: Dict[str, Any], key: str, value: str
    ) -> bool:
        """Check if a user matches the given filter.

        Handles field aliases and nested fields.
        """
        key = key.lower()
        value = value.lower()

        # Check if it's an aliased field
        if key in cls.FILTER_ALIASES:
            path = cls.FILTER_ALIASES[key]
            if len(path) == 1:
                # Simple alias (e.g., adminlevel -> administrator_level)
                actual_value = user.get(path[0], "")
            else:
                # Nested field (e.g., defaultaccount -> default.account)
                obj = user
                for part in path:
                    if isinstance(obj, dict):
                        obj = obj.get(part, "")
                    else:
                        obj = ""
                        break
                actual_value = obj
        else:
            # Direct field access
            actual_value = user.get(key, "")

        # Handle nested dict for 'default' field
        if key == "default" and isinstance(actual_value, dict):
            actual_value = actual_value.get("account", "")

        return str(actual_value).lower() == value

    @classmethod
    def _format_value(cls, user: Dict[str, Any], column: str) -> str:
        """Format a value for display."""
        value = user.get(column, "")
        # Handle nested 'default' dict
        if column == "default" and isinstance(value, dict):
            account = value.get("account", "")
            wckey = value.get("wckey", "")
            if account and wckey:
                return f"{account} ({wckey})"
            return account or wckey or "-"
        # Handle array fields
        if column in (
            "coordinators",
            "flags",
            "associations",
            "wckeys",
        ):
            if isinstance(value, list):
                return (
                    ", ".join(str(v) for v in value) if value else "-"
                )
        if value is None or value == "":
            return "-"
        return str(value)

    @classmethod
    def generate_autocomplete_options(cls) -> str:
        """Generate bash autocomplete script for user options."""
        valid_keys = [opt.lower() for opt in USER_OPTIONS]
        where_opts = [opt.lower() for opt in USER_UPDATE_WHERE_OPTIONS]
        set_opts = [opt.lower() for opt in USER_UPDATE_SET_OPTIONS]

        script = f"""
_slurm_cli_users_autocomplete() {{
    local cmd="$1"
    local pos="$2"

    name="${{COMP_WORDS[$pos]}}"
    cur="${{COMP_WORDS[COMP_CWORD]}}"
    prev="${{COMP_WORDS[COMP_CWORD-1]}}"

    # Get cached user names if available (space-separated)
    local cached_users=""
    if [ -f "/tmp/slurm_cli_users.json" ]; then
        cached_users=$(jq -r '.users[].name // .users[].user.name // keys[]' /tmp/slurm_cli_users.json 2>/dev/null | tr '\\n' ' ')
    fi

    # USER_OPTIONS for filtering/updating
    local filter_options="{'= '.join(valid_keys)}="
    local where_options="{'= '.join(where_opts)}="
    local set_options="{'= '.join(set_opts)}="
    local update_options="$cached_users $where_options set"

    # Check if 'set' keyword has been typed (for update command)
    local found_set=0
    for word in "${{COMP_WORDS[@]}}"; do
        if [[ "$word" == "set" ]]; then
            found_set=1
            break
        fi
    done

    # If we're on the name field (right after 'users')
    if [[ $name == users && $prev == users ]]; then
        case "$cmd" in
            show)
                # For show, allow both user names and filter options
                local all_options="$cached_users $filter_options"
                if [[ $cur == '' ]]; then
                    COMPREPLY=($(compgen -W "$all_options"))
                else
                    COMPREPLY=($(compgen -W "$all_options" -- "$cur"))
                fi
                return
                ;;
            delete)
                if [ -n "$cached_users" ]; then
                    COMPREPLY=($(compgen -W "$cached_users" -- "$cur"))
                fi
                return
                ;;
            create)
                # For create, just show options
                if [[ $cur == '' ]]; then
                    COMPREPLY=($(compgen -W "$filter_options"))
                else
                    COMPREPLY=($(compgen -W "$filter_options" -- "$cur"))
                fi
                return
                ;;
            update)
                # For update, show both cached user names and options
                if [[ $cur == '' ]]; then
                    COMPREPLY=($(compgen -W "$update_options"))
                else
                    COMPREPLY=($(compgen -W "$update_options" -- "$cur"))
                fi
                return
                ;;
        esac
    fi

    case "$cmd" in
        delete)
            return
            ;;
        update)
            # After 'set' keyword, show SET options
            if [[ $found_set -eq 1 ]]; then
                if [[ $cur == = || $prev == = ]]; then
                    local key
                    if [[ $cur == = ]]; then
                        key=${{COMP_WORDS[COMP_CWORD-1]}}
                    else
                        key=${{COMP_WORDS[COMP_CWORD-2]}}
                    fi
                    key=${{key,,}}
                    case "$key" in
                        adminlevel)
                            COMPREPLY=($(compgen -W "None Admin Operator" -- "${{cur#*=}}"))
                            ;;
                        newname|name)
                            if [ -n "$cached_users" ]; then
                                COMPREPLY=($(compgen -W "$cached_users" -- "${{cur#*=}}"))
                            fi
                            ;;
                        defaultaccount)
                            if [ -f "/tmp/slurm_cli_accounts.json" ]; then
                                COMPREPLY=($(compgen -W "$(jq -r '.accounts[].name // keys[]' /tmp/slurm_cli_accounts.json 2>/dev/null)" -- "${{cur#*=}}"))
                            fi
                            ;;
                        partition)
                            if [ -f "/tmp/slurm_cli_partitions.json" ]; then
                                COMPREPLY=($(compgen -W "$(jq -r 'keys[]' /tmp/slurm_cli_partitions.json 2>/dev/null)" -- "${{cur#*=}}"))
                            fi
                            ;;
                    esac
                    return
                else
                    if [[ $cur == '' ]]; then
                        COMPREPLY=($(compgen -W "$set_options"))
                    else
                        COMPREPLY=($(compgen -W "$set_options" -- "$cur"))
                    fi
                fi
                return
            fi
            # Before 'set' keyword, show WHERE options and 'set'
            if [[ $cur == = || $prev == = ]]; then
                local key
                if [[ $cur == = ]]; then
                    key=${{COMP_WORDS[COMP_CWORD-1]}}
                else
                    key=${{COMP_WORDS[COMP_CWORD-2]}}
                fi
                key=${{key,,}}
                case "$key" in
                    user|name)
                        if [ -n "$cached_users" ]; then
                            COMPREPLY=($(compgen -W "$cached_users" -- "${{cur#*=}}"))
                        fi
                        ;;
                    account|defaultaccount)
                        if [ -f "/tmp/slurm_cli_accounts.json" ]; then
                            COMPREPLY=($(compgen -W "$(jq -r '.accounts[].name // keys[]' /tmp/slurm_cli_accounts.json 2>/dev/null)" -- "${{cur#*=}}"))
                        fi
                        ;;
                    partition)
                        if [ -f "/tmp/slurm_cli_partitions.json" ]; then
                            COMPREPLY=($(compgen -W "$(jq -r 'keys[]' /tmp/slurm_cli_partitions.json 2>/dev/null)" -- "${{cur#*=}}"))
                        fi
                        ;;
                    adminlevel)
                        COMPREPLY=($(compgen -W "None Admin Operator" -- "${{cur#*=}}"))
                        ;;
                esac
                return
            else
                if [[ $cur == '' ]]; then
                    COMPREPLY=($(compgen -W "$where_options set"))
                else
                    COMPREPLY=($(compgen -W "$where_options set" -- "$cur"))
                fi
            fi
            return
            ;;
        show|create)
            if [[ $cur == = || $prev == = ]]; then
                local key
                if [[ $cur == = ]]; then
                    key=${{COMP_WORDS[COMP_CWORD-1]}}
                else
                    key=${{COMP_WORDS[COMP_CWORD-2]}}
                fi
                key=${{key,,}}

                case "$key" in
                    user|name)
                        if [ -n "$cached_users" ]; then
                            COMPREPLY=($(compgen -W "$cached_users" -- "${{cur#*=}}"))
                        fi
                        ;;
                    account|defaultaccount)
                        if [ -f "/tmp/slurm_cli_accounts.json" ]; then
                            COMPREPLY=($(compgen -W "$(jq -r '.accounts[].name // keys[]' /tmp/slurm_cli_accounts.json 2>/dev/null)" -- "${{cur#*=}}"))
                        fi
                        ;;
                    partition)
                        if [ -f "/tmp/slurm_cli_partitions.json" ]; then
                            COMPREPLY=($(compgen -W "$(jq -r 'keys[]' /tmp/slurm_cli_partitions.json 2>/dev/null)" -- "${{cur#*=}}"))
                        fi
                        ;;
                    qos)
                        if [ -f "/tmp/slurm_cli_qos.json" ]; then
                            COMPREPLY=($(compgen -W "$(jq -r '.qos[].name' /tmp/slurm_cli_qos.json 2>/dev/null)" -- "${{cur#*=}}"))
                        fi
                        ;;
                    adminlevel)
                        COMPREPLY=($(compgen -W "None Operator Admin" -- "${{cur#*=}}"))
                        ;;
                esac
                return
            else
                # Complete option names
                local opts="$filter_options"
                if [[ $cmd == "update" || $cmd == "create" ]]; then
                    opts="$update_options"
                fi
                if [[ $cur == '' ]]; then
                    COMPREPLY=($(compgen -W "$opts"))
                else
                    COMPREPLY=($(compgen -W "$opts" -- "$cur"))
                fi
            fi
            ;;
    esac
}}
"""  # noqa: E501
        return script

    @classmethod
    def create(
        cls, name: str, verbose: bool = False, **kwargs: Any
    ) -> None:
        """Create a new user."""
        console.print(f"Creating user: {name}")
        args = ["sacctmgr", "create", "user", name]
        for key, value in kwargs.items():
            args.append(f"{key}={value}")

        try:
            result = subprocess.run(
                args,
                check=True,
                capture_output=True,
                text=True,
            )
            console.print(
                f"[green]User '{name}' created successfully.[/green]"
            )
            if result.stdout:
                console.print(result.stdout)
        except subprocess.CalledProcessError as e:
            console.print(
                f"[red]Failed to create user '{name}':[/red] {e.stderr or e}"
            )

    @classmethod
    def update(
        cls,
        name: str,
        verbose: bool = False,
        where_conditions: Optional[List[str]] = None,
        set_values: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> None:
        """Update a user.

        Two calling modes:
        1. Simple: update(name, key=value, ...) - updates user by name
        2. Where: update("", where_conditions=[...], set_values=[...])
           - uses WHERE/SET syntax for bulk updates

        Args:
            name: Username to update (for simple mode)
            verbose: Enable verbose output
            where_conditions: List of WHERE conditions (e.g., ["account=test"])
            set_values: List of SET values (e.g., ["adminlevel=admin"])
            **kwargs: SET options as keyword arguments
        """
        # Build the command
        args = ["sacctmgr", "-i", "modify", "user"]

        # Determine mode and build WHERE clause
        if where_conditions:
            # WHERE/SET mode
            args.append("where")
            for cond in where_conditions:
                args.append(cond)
        elif name:
            # Simple mode - update by name
            args.extend(["where", f"name={name}"])
        else:
            console.print(
                "[red]No user name or WHERE conditions specified.[/red]"
            )
            return

        # Build SET clause
        args.append("set")

        # Use set_values if provided, otherwise use kwargs
        if set_values:
            for val in set_values:
                # Validate adminlevel even in WHERE mode
                if "=" in val:
                    k, v = val.split("=", 1)
                    if k.lower() == "adminlevel":
                        if v.lower() not in VALID_ADMIN_LEVELS:
                            console.print(
                                f"[red]Invalid adminlevel '{v}'. "
                                f"Must be one of: "
                                f"{', '.join(VALID_ADMIN_LEVELS)}[/red]"
                            )
                            return
                args.append(val)
        else:
            for key, value in kwargs.items():
                if value is None:
                    continue

                key_lower = key.lower()

                # Handle 'name' -> 'newname' conversion
                if key_lower == "name":
                    key_lower = "newname"

                # Validate adminlevel values
                if key_lower == "adminlevel":
                    if value.lower() not in VALID_ADMIN_LEVELS:
                        console.print(
                            f"[red]Invalid adminlevel '{value}'. "
                            f"Must be one of: {', '.join(VALID_ADMIN_LEVELS)}"
                            "[/red]"
                        )
                        return

                # Validate the option is allowed
                if key_lower not in USER_UPDATE_SET_OPTIONS:
                    console.print(
                        f"[yellow]Warning: '{key}' is not a recognized "
                        f"SET option. Valid options: "
                        f"{', '.join(USER_UPDATE_SET_OPTIONS)}[/yellow]"
                    )

                args.append(f"{key_lower}={value}")

        if verbose:
            console.print(f"Running: {' '.join(args)}")

        try:
            result = subprocess.run(
                args,
                check=True,
                capture_output=True,
                text=True,
            )
            if result.stdout:
                console.print(result.stdout)
            if verbose:
                console.print(
                    f"[green]User '{name}' updated successfully.[/green]"
                )
        except subprocess.CalledProcessError as e:
            console.print(
                f"[red]Failed to update user '{name}':[/red] "
                f"{e.stderr or e}"
            )

    @classmethod
    def delete(cls, name: str) -> None:
        """Delete a user."""
        # TODO: Implement actual user deletion using sacctmgr delete user
        console.print(f"Deleting user: {name}")

    @classmethod
    def show(
        cls,
        name: str = None,
        data: dict = None,
        style: str = "pretty",
        force_cache_update: bool = False,
        delimiter: str = ";",
        zebra: bool = False,
        profile: str = "default",
        profile_str: Optional[str] = None,
    ) -> None:
        """Show user information.

        Args:
            name: Optional username or filter (e.g., administrator_level=Admin)
            data: Pre-loaded data (unused, for API compatibility)
            style: Output style ("pretty", "json", or "csv")
            force_cache_update: Whether to force cache update (unused)
            delimiter: Delimiter for CSV output (default: ";")
            zebra: Use zebra striping for table rows (default: False)
            profile: Profile name to use for output formatting
            profile_str: Inline profile string (overrides profile)
        """
        try:
            # Always get JSON output from sacctmgr for processing
            result = subprocess.run(
                ["sacctmgr", "show", "users", "--json"],
                check=True,
                capture_output=True,
                text=True,
            )

            if not result.stdout:
                console.print("[yellow]No users found.[/yellow]")
                return

            # Parse JSON data
            data = json.loads(result.stdout)
            users = data.get("users", [])

            # Filter by name if specified
            if name:
                # Check if it's a filter (contains '=')
                if "=" in name:
                    key, value = name.split("=", 1)
                    key = key.lower()
                    users = [
                        u
                        for u in users
                        if cls._match_filter(u, key, value)
                    ]
                    if not users:
                        console.print(
                            f"[yellow]No users match filter "
                            f"'{name}'.[/yellow]"
                        )
                        return
                else:
                    # It's a username
                    users = [u for u in users if u.get("name") == name]
                    if not users:
                        console.print(
                            f"[yellow]User '{name}' not found.[/yellow]"
                        )
                        return

            if style == "json":
                # Print filtered JSON
                filtered_data = {"users": users}
                console.print_json(json.dumps(filtered_data, indent=2))
            elif style == "csv":
                # Get column configuration from profile
                columns, _, _ = cls._get_column_config(
                    profile, profile_str
                )

                # Header
                headers = [
                    col.title().replace("_", " ") for col in columns
                ]
                print(delimiter.join(headers))

                # Data rows
                for user in users:
                    row = [
                        cls._format_value(user, col) for col in columns
                    ]
                    print(delimiter.join(row))
            else:  # pretty style
                # Get column configuration from profile
                columns, styles, _ = cls._get_column_config(
                    profile, profile_str
                )

                # Create table
                table = Table(box=SIMPLE_HEAVY, show_header=True)

                # Add columns with styles
                for col in columns:
                    style = styles.get(col, "white")
                    table.add_column(
                        col.title().replace("_", " "), style=style
                    )

                # Add rows
                for i, user in enumerate(users):
                    row = [
                        cls._format_value(user, col) for col in columns
                    ]
                    if zebra and i % 2 == 1:
                        table.add_row(*row, style="dim")
                    else:
                        table.add_row(*row)

                console.print(table)

        except subprocess.CalledProcessError as e:
            console.print(
                f"[red]Failed to show users:[/red] {e.stderr or e}"
            )
