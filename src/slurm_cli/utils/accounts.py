"""Utilities for managing accounts."""

import json
import subprocess
from typing import Any, Dict, List, Optional, Union

from rich.box import SIMPLE_HEAVY
from rich.table import Table

from .base_resource import BaseSlurmResource
from .profiles import (
    format_with_template,
    get_profile_config,
    sort_data,
    sort_hierarchical_data,
)
from .utils import console

# Account configuration options (sacctmgr field names)
# Note: Flags is read-only (shows status like "Deleted"), not settable
ACCOUNT_OPTIONS: List[str] = [
    "Cluster",
    # "DefaultQOS",
    "Description",
    "Name",
    # "Fairshare",
    # "GrpJobs",
    # "GrpJobsAccrue",
    # "GrpSubmit",
    # "GrpSubmitJobs",
    # "GrpTRES",
    # "GrpTRESMins",
    # "GrpTRESRunMins",
    # "GrpWall",
    # "MaxJobs",
    # "MaxJobsAccrue",
    # "MaxSubmit",
    # "MaxSubmitJobs",
    # "MaxTRES",
    # "MaxTRESMins",
    # "MaxWall",
    "Organization",
    "Parent",
    "RawUsage",
]


class Account(BaseSlurmResource):
    def __init__(self, name: str, **kwargs: Any):
        self.name = name
        self.kwargs = kwargs

    @classmethod
    def get_profile_fields(cls) -> dict:
        """Return field names and descriptions for profile templates."""
        return {
            "name": "Account name",
            "description": "Account description",
            "organization": "Organization name",
            "coordinators": "List of coordinator usernames",
        }

    @classmethod
    def generate_autocomplete_options(cls) -> str:
        """Generate bash autocomplete script for account options."""
        valid_keys = [opt.lower() for opt in ACCOUNT_OPTIONS]
        filter_opts = " ".join(f"{k}=" for k in valid_keys)

        script = f"""
_slurm_cli_accounts_autocomplete() {{
    local cmd="$1"
    local pos="$2"

    local cur="${{COMP_WORDS[COMP_CWORD]}}"
    local prev="${{COMP_WORDS[COMP_CWORD-1]}}"
    local name="${{COMP_WORDS[$pos]}}"

    local cached_accounts="$(_slurm_cache_accounts)"
    local filter_options="{filter_opts}"
    local update_options="$filter_options set"

    # First argument after 'accounts' (not completing a value)
    if [[ $name == accounts && $prev == accounts && $cur != *=* ]]; then
        case "$cmd" in
            show|delete) _slurm_complete "$filter_options $cached_accounts" "$cur" ;;
            update)      _slurm_complete "$update_options $cached_accounts" "$cur" ;;
        esac
        return
    fi

    # Handle key=value completion
    if _slurm_parse_keyval "$cur" "$prev"; then
        case "$_key" in
            defaultqos)
                _slurm_complete_value "$(_slurm_cache_qos)" "$_key" "$_val" "$cur" ;;
            parent|organization|name)
                _slurm_complete_value "$cached_accounts" "$_key" "$_val" "$cur" ;;
        esac
        return
    fi

    # Complete option names
    case "$cmd" in
        show|delete) _slurm_complete "$filter_options" "$cur" ;;
        create|update) _slurm_complete "$update_options" "$cur" ;;
    esac
}}
"""  # noqa: E501
        return script

    @classmethod
    def create(
        cls, name: str, verbose: bool = False, **kwargs: Any
    ) -> None:
        """Create a new account."""
        console.print(f"Creating account: {name}")
        args = ["sacctmgr", "create", "account", f"name={name}"]
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
                f"[green]Account '{name}' created successfully.[/green]"
            )
            if result.stdout:
                console.print(result.stdout)
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr or e
            console.print(
                f"[red]Failed to create account '{name}':[/red] {error_msg}"
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
        """Update an account.

        Two calling modes:
        1. Simple: update(name, key=value, ...) - updates account by name
        2. Where: update(name, where_conditions=[...], set_values=[...])
           - uses WHERE/SET syntax for bulk updates

        Args:
            name: Account name (simple mode) or ignored (where mode)
            verbose: Enable verbose output
            dry_run: If True, print command without executing
            where_conditions: List of WHERE conditions (e.g., ["cluster=test"])
            set_values: List of SET values (e.g., ["description=foo"])
            **kwargs: Additional SET values (simple mode only)
        """
        # Build sacctmgr command
        args = ["sacctmgr", "-i", "modify", "account"]

        if where_conditions is not None:
            # WHERE/SET mode
            args.append("where")
            args.extend(where_conditions)
            args.append("set")
            if set_values:
                args.extend(set_values)
            where_str = " ".join(where_conditions)
            set_str = " ".join(set_values) if set_values else ""
            if not dry_run:
                console.print(
                    f"Updating accounts where {where_str} set {set_str}"
                )
        else:
            # Simple mode - update by name
            args.append("where")
            args.append(f"name={name}")
            args.append("set")
            for key, value in kwargs.items():
                if value is not None:
                    args.append(f"{key}={value}")
                else:
                    args.append(key)
            if not dry_run:
                console.print(f"Updating account: {name}")

        if dry_run:
            console.print(f"[yellow]DRY RUN:[/yellow] {' '.join(args)}")
            return

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
                    "[green]Account updated successfully.[/green]"
                )
        except subprocess.CalledProcessError as e:
            console.print(
                f"[red]Failed to update account:[/red] {e.stderr or e}"
            )

    @classmethod
    def delete(cls, name: str) -> None:
        """Delete an account."""
        # TODO: Implement actual account deletion using sacctmgr delete account
        console.print(f"Deleting account: {name}")

    # Default column configuration for accounts
    DEFAULT_COLUMNS = [
        "name",
        "description",
        "organization",
        "coordinators",
        "flags",
        "associations",
    ]
    DEFAULT_STYLES = {
        "name": "cyan",
        "description": "white",
        "organization": "green",
        "coordinators": "yellow",
        "flags": "magenta",
        "associations": "blue",
    }

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
        ) = get_profile_config(profile, "accounts", profile_str)

        # Use default columns if profile specifies "*" or no columns
        if columns == "*" or columns is None:
            columns = cls.DEFAULT_COLUMNS

        # Merge with default styles
        merged_styles = dict(cls.DEFAULT_STYLES)
        merged_styles.update(styles)

        return columns, merged_styles, template, sort_field, sort_asc

    @classmethod
    def _format_value(cls, account: Dict[str, Any], column: str) -> str:
        """Format a value for display."""
        value = account.get(column, "")
        # Handle array fields
        if column in ("coordinators", "flags", "associations"):
            if isinstance(value, list):
                return (
                    ", ".join(str(v) for v in value) if value else "-"
                )
        if value is None or value == "":
            return "-"
        return str(value)

    @classmethod
    def _parse_filter(cls, filter_str: str) -> Optional[tuple]:
        """Parse a filter string like 'organization=nvidia'.

        Returns:
            Tuple of (key, value) if valid filter, None otherwise.
        """
        if "=" in filter_str:
            key, value = filter_str.split("=", 1)
            return (key.lower(), value)
        return None

    @classmethod
    def _apply_filters(
        cls, accounts: List[Dict[str, Any]], filters: List[tuple]
    ) -> List[Dict[str, Any]]:
        """Apply filters to account list.

        Args:
            accounts: List of account dictionaries
            filters: List of (key, value) tuples to filter by

        Returns:
            Filtered list of accounts
        """
        for key, value in filters:
            accounts = [
                acc
                for acc in accounts
                if str(acc.get(key, "")).lower() == value.lower()
            ]
        return accounts

    @classmethod
    def _sort_hierarchically(
        cls,
        accounts: List[Dict[str, Any]],
        indent: str = "  ",
    ) -> List[Dict[str, Any]]:
        """Sort accounts hierarchically and add depth/indent info.

        Args:
            accounts: List of account dictionaries
            indent: Indentation string per level (default: two spaces)

        Returns:
            Sorted list with '_depth' and '_indent' keys added
        """
        # Build parent-child relationships
        account_map = {}  # name -> account_data
        children_map: Dict[
            str, List[str]
        ] = {}  # parent_name -> [child_names]

        for acc in accounts:
            name = acc.get("name", "")
            parent = acc.get("parent", "") or acc.get(
                "parent_account", ""
            )
            account_map[name] = acc

            if parent not in children_map:
                children_map[parent] = []
            children_map[parent].append(name)

        # Find root accounts (no parent or parent not in map)
        root_accounts = []
        for name, acc in account_map.items():
            parent = acc.get("parent", "") or acc.get(
                "parent_account", ""
            )
            if not parent or parent not in account_map:
                root_accounts.append(name)

        root_accounts.sort()

        # Build sorted list with depth
        result: List[Dict[str, Any]] = []

        def add_account(account_name: str, depth: int):
            acc = account_map.get(account_name, {})
            acc_copy = acc.copy()
            acc_copy["_depth"] = depth
            acc_copy["_indent"] = indent * depth
            acc_copy["_is_account"] = True
            result.append(acc_copy)

            # Add children (sorted)
            children = sorted(children_map.get(account_name, []))
            for child in children:
                add_account(child, depth + 1)

        for root in root_accounts:
            add_account(root, 0)

        return result

    @classmethod
    def show(
        cls,
        field: Union[str, None] = None,
        style: str = "pretty",
        force_cache_update: bool = False,
        delimiter: str = ";",
        zebra: bool = False,
        profile: str = "default",
        profile_str: Optional[str] = None,
        tree: bool = False,
    ) -> None:
        """Show account information.

        Args:
            field: Optional account name or filter (e.g., organization=nvidia)
            style: Output style ("pretty", "json", or "csv")
            force_cache_update: Whether to force cache update (unused)
            delimiter: Delimiter for CSV output (default: ";")
            zebra: Use zebra striping for table rows (default: False)
            profile: Profile name to use for output formatting
            profile_str: Inline profile string (overrides profile)
            tree: Show accounts in hierarchical tree format
        """
        try:
            # Always get JSON output from sacctmgr
            result = subprocess.run(
                ["sacctmgr", "show", "accounts", "--json"],
                check=True,
                capture_output=True,
                text=True,
            )

            if not result.stdout:
                console.print("[yellow]No accounts found.[/yellow]")
                return

            # Parse JSON data
            data = json.loads(result.stdout)
            accounts = data.get("accounts", [])

            # Filter by field if specified
            if field:
                # Check if field is a filter (contains '=') or a name
                parsed_filter = cls._parse_filter(field)
                if parsed_filter:
                    # It's a filter like organization=nvidia
                    accounts = cls._apply_filters(
                        accounts, [parsed_filter]
                    )
                    if not accounts:
                        console.print(
                            f"[yellow]No accounts match filter "
                            f"'{field}'.[/yellow]"
                        )
                        return
                else:
                    # It's an account name
                    accounts = [
                        acc
                        for acc in accounts
                        if acc.get("name") == field
                    ]
                    if not accounts:
                        console.print(
                            f"[yellow]Account '{field}' not found.[/yellow]"
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

            # Tree mode or flat sorting
            if tree and style == "pretty":
                # Hierarchical mode - add depth/indent info
                accounts = cls._sort_hierarchically(accounts)
                # Apply hierarchical sorting if specified
                if sort_field:
                    accounts = sort_hierarchical_data(
                        accounts,
                        sort_field,
                        sort_asc,
                        depth_key="_depth",
                        parent_key="parent",
                        id_key="name",
                    )
            elif sort_field:
                # Flat mode sorting
                accounts = sort_data(accounts, sort_field, sort_asc)

            if style == "json":
                # Print filtered JSON
                filtered_data = {"accounts": accounts}
                console.print_json(json.dumps(filtered_data, indent=2))
            elif style == "csv":
                # Header
                headers = [col.title() for col in columns]
                print(delimiter.join(headers))

                # Data rows
                for account in accounts:
                    row = [
                        cls._format_value(account, col)
                        for col in columns
                    ]
                    # Replace "-" with empty for CSV
                    row = ["" if v == "-" else v for v in row]
                    print(delimiter.join(row))
            else:  # pretty style
                # If template is specified, use template-based output
                if template:
                    for account in accounts:
                        output = format_with_template(
                            template, account, resource="accounts"
                        )
                        console.print(output)
                else:
                    # Create a rich table
                    row_styles = (
                        ["", "on rgb(30,40,60)"] if zebra else None
                    )
                    table = Table(
                        title="Accounts",
                        box=SIMPLE_HEAVY,
                        pad_edge=False,
                        padding=(0, 0),
                        row_styles=row_styles,
                    )

                    # Add columns based on profile
                    for col in columns:
                        table.add_column(
                            col.title(),
                            style=styles.get(col, ""),
                            no_wrap=(col == "name"),
                        )

                    # Add rows
                    for account in accounts:
                        row = []
                        indent = account.get("_indent", "")
                        for col in columns:
                            value = cls._format_value(account, col)
                            # Prepend indent to name column in tree mode
                            if col == "name" and indent:
                                value = indent + value
                            row.append(value)
                        table.add_row(*row)

                    console.print(table)

        except subprocess.CalledProcessError as e:
            error_msg = e.stderr or e
            console.print(
                f"[red]Failed to show accounts:[/red] {error_msg}"
            )
        except json.JSONDecodeError as e:
            console.print(
                f"[red]Failed to parse JSON output:[/red] {e}"
            )
