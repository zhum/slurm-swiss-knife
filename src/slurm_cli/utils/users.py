"""Utilities for managing users."""

import json
import subprocess
from typing import Any, Dict, List, Optional, Union

from rich.box import SIMPLE_HEAVY
from rich.table import Table

from .base_resource import BaseSlurmResource
from .profiles import get_profile_config, sort_data
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
            Tuple of (columns, styles, template, sort_field, sort_asc)
        """
        (
            columns,
            styles,
            template,
            sort_field,
            sort_asc,
        ) = get_profile_config(profile, "users", profile_str)

        # Use all columns if profile specifies "*"
        if columns == "*":
            columns = cls.ALL_COLUMNS
        # Use default columns if no columns specified
        elif columns is None:
            columns = cls.DEFAULT_COLUMNS

        # Merge with default styles
        merged_styles = dict(cls.DEFAULT_STYLES)
        merged_styles.update(styles)

        return columns, merged_styles, template, sort_field, sort_asc

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
        # Unwrap single-element list fields
        if column == "administrator_level" and isinstance(value, list):
            return value[0] if value else "-"
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
        create_opts = [
            "name",
            "account",
            "adminlevel",
            "cluster",
            "defaultaccount",
            "defaultwckey",
            "partition",
            "rawusage",
        ]
        filter_opts = " ".join(f"{k}=" for k in valid_keys)
        where_options = " ".join(f"{k}=" for k in where_opts)
        set_options = " ".join(f"{k}=" for k in set_opts)
        create_options = " ".join(f"{k}=" for k in create_opts)
        admin_levels = "None Admin Operator"

        script = f"""
_slurm_cli_users_autocomplete() {{
    local cmd="$1"
    local pos="$2"

    local cur="${{COMP_WORDS[COMP_CWORD]}}"
    local prev="${{COMP_WORDS[COMP_CWORD-1]}}"
    local name="${{COMP_WORDS[$pos]}}"

    local cached_users="$(_slurm_cache_users)"
    local filter_options="{filter_opts}"
    local where_options="{where_options}"
    local set_options="{set_options}"
    local create_options="{create_options}"
    local update_options="$cached_users $where_options set"

    # Check if 'set' keyword has been typed
    local found_set=0
    for word in "${{COMP_WORDS[@]}}"; do
        [[ "$word" == "set" ]] && found_set=1 && break
    done

    # First argument after 'users'
    if [[ $name == users && $prev == users ]]; then
        case "$cmd" in
            show|delete) _slurm_complete "$filter_options $cached_users" "$cur" ;;
            create)      _slurm_complete "$create_options" "$cur" ;;
            update)      _slurm_complete "$update_options $cached_users" "$cur" ;;
        esac
        return
    fi

    case "$cmd" in
        delete)
            if _slurm_parse_keyval "$cur" "$prev"; then
                case "$_key" in
                    user|name)
                        _slurm_complete_value "$cached_users" "$_key" "$_val" "$cur" ;;
                    account|defaultaccount)
                        _slurm_complete_value "$(_slurm_cache_accounts)" "$_key" "$_val" "$cur" ;;
                    partition)
                        _slurm_complete_value "$(_slurm_cache_partitions)" "$_key" "$_val" "$cur" ;;
                    adminlevel)
                        _slurm_complete_value "{admin_levels}" "$_key" "$_val" "$cur" ;;
                esac
                return
            fi
            _slurm_complete "$filter_options" "$cur"
            return
            ;;
        update)
            # After 'set' keyword, show SET options
            if [[ $found_set -eq 1 ]]; then
                if _slurm_parse_keyval "$cur" "$prev"; then
                    case "$_key" in
                        adminlevel)
                            _slurm_complete_value "{admin_levels}" "$_key" "$_val" "$cur" ;;
                        newname|name)
                            _slurm_complete_value "$cached_users" "$_key" "$_val" "$cur" ;;
                        defaultaccount)
                            _slurm_complete_value "$(_slurm_cache_accounts)" "$_key" "$_val" "$cur" ;;
                        partition)
                            _slurm_complete_value "$(_slurm_cache_partitions)" "$_key" "$_val" "$cur" ;;
                    esac
                    return
                fi
                _slurm_complete "$set_options" "$cur"
                return
            fi
            # Before 'set' keyword, show WHERE options and 'set'
            if _slurm_parse_keyval "$cur" "$prev"; then
                case "$_key" in
                    user|name)
                        _slurm_complete_value "$cached_users" "$_key" "$_val" "$cur" ;;
                    account|defaultaccount)
                        _slurm_complete_value "$(_slurm_cache_accounts)" "$_key" "$_val" "$cur" ;;
                    partition)
                        _slurm_complete_value "$(_slurm_cache_partitions)" "$_key" "$_val" "$cur" ;;
                    adminlevel)
                        _slurm_complete_value "{admin_levels}" "$_key" "$_val" "$cur" ;;
                esac
                return
            fi
            _slurm_complete "$where_options set" "$cur"
            return
            ;;
        show)
            if _slurm_parse_keyval "$cur" "$prev"; then
                case "$_key" in
                    user|name)
                        _slurm_complete_value "$cached_users" "$_key" "$_val" "$cur" ;;
                    account|defaultaccount)
                        _slurm_complete_value "$(_slurm_cache_accounts)" "$_key" "$_val" "$cur" ;;
                    partition)
                        _slurm_complete_value "$(_slurm_cache_partitions)" "$_key" "$_val" "$cur" ;;
                    qos)
                        _slurm_complete_value "$(_slurm_cache_qos)" "$_key" "$_val" "$cur" ;;
                    adminlevel)
                        _slurm_complete_value "{admin_levels}" "$_key" "$_val" "$cur" ;;
                esac
                return
            fi
            _slurm_complete "$filter_options" "$cur"
            ;;
        create)
            if _slurm_parse_keyval "$cur" "$prev"; then
                case "$_key" in
                    name)
                        _slurm_complete_value "$cached_users" "$_key" "$_val" "$cur" ;;
                    account|defaultaccount)
                        _slurm_complete_value "$(_slurm_cache_accounts)" "$_key" "$_val" "$cur" ;;
                    partition)
                        _slurm_complete_value "$(_slurm_cache_partitions)" "$_key" "$_val" "$cur" ;;
                    adminlevel)
                        _slurm_complete_value "{admin_levels}" "$_key" "$_val" "$cur" ;;
                esac
                return
            fi
            _slurm_complete "$create_options" "$cur"
            ;;
    esac
}}
"""
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
        dry_run: bool = False,
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
            dry_run: If True, print command without executing
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

        if dry_run:
            console.print(f"[yellow]DRY RUN:[/yellow] {' '.join(args)}")
            return

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
    def delete(cls, name: str, verbose: bool = False) -> None:
        """Delete a user.

        Args:
            name: Username to delete
            verbose: Enable verbose output
        """
        console.print(f"Deleting user: {name}")
        args = ["sacctmgr", "-i", "delete", "user", f"name={name}"]

        try:
            result = subprocess.run(
                args,
                check=True,
                capture_output=True,
                text=True,
            )
            console.print(
                f"[green]User '{name}' deleted successfully.[/green]"
            )
            if result.stdout:
                console.print(result.stdout)
        except subprocess.CalledProcessError as e:
            console.print(
                f"[red]Failed to delete user '{name}':[/red] {e.stderr or e}"
            )

    @classmethod
    def show(
        cls,
        name: Union[None, str] = None,
        data: dict = {},
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

            # Get column configuration from profile (once)
            (
                columns,
                styles,
                template,
                sort_field,
                sort_asc,
            ) = cls._get_column_config(profile, profile_str)

            # Apply sorting
            if sort_field:
                users = sort_data(users, sort_field, sort_asc)

            if style == "json":
                # Print filtered JSON
                filtered_data = {"users": users}
                console.print_json(json.dumps(filtered_data, indent=2))
            elif style == "csv":
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
