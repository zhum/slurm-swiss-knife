"""Utilities for managing accounts."""

import json
import subprocess
from typing import Any, Dict, List, Optional

from rich.box import SIMPLE_HEAVY
from rich.table import Table

from .base_resource import BaseSlurmResource
from .profiles import format_with_template, get_profile_config
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

        script = f"""
_slurm_cli_accounts_autocomplete() {{
    local cmd="$1"
    local pos="$2"

    name="${{COMP_WORDS[$pos]}}"
    cur="${{COMP_WORDS[COMP_CWORD]}}"
    prev="${{COMP_WORDS[COMP_CWORD-1]}}"

    # Get cached account names if available (space-separated)
    local cached_accounts=""
    if [ -f "/tmp/slurm_cli_accounts.json" ]; then
        cached_accounts=$(jq -r '.accounts[].name' /tmp/slurm_cli_accounts.json 2>/dev/null | tr '\\n' ' ')
    fi

    # ACCOUNT_OPTIONS for filtering/updating
    local filter_options="{'= '.join(valid_keys)}="
    local update_options="$filter_options set"

    # If we're on the name field (right after 'accounts') and not completing a value
    if [[ $name == accounts && $prev == accounts && $cur != *=* ]]; then
        case "$cmd" in
            show)
                # For show, allow both account names and filter options
                local all_options="$cached_accounts $filter_options"
                if [[ $cur == '' ]]; then
                    COMPREPLY=($(compgen -W "$all_options"))
                else
                    COMPREPLY=($(compgen -W "$all_options" -- "$cur"))
                fi
                return
                ;;
            delete)
                if [ -n "$cached_accounts" ]; then
                    COMPREPLY=($(compgen -W "$cached_accounts" -- "$cur"))
                fi
                return
                ;;
            update)
                # For update, show both cached account names and ACCOUNT_OPTIONS
                local all_options="$cached_accounts $update_options"
                if [[ $cur == '' ]]; then
                    COMPREPLY=($(compgen -W "$all_options"))
                else
                    COMPREPLY=($(compgen -W "$all_options" -- "$cur"))
                fi
                return
                ;;
        esac
    fi

    case "$cmd" in
        delete)
            return
            ;;
        show|create|update)
            # Handle case where = is a separate word
            if [[ $cur == = ]]; then
                local key="${{COMP_WORDS[COMP_CWORD-1]}}"
                key=${{key,,}}
                case "$key" in
                    defaultqos)
                        if [ -f "/tmp/slurm_cli_qos.json" ]; then
                            COMPREPLY=($(compgen -W "$(jq -r '.qos[].name' /tmp/slurm_cli_qos.json 2>/dev/null)"))
                        fi
                        ;;
                    parent|organization)
                        if [ -n "$cached_accounts" ]; then
                            COMPREPLY=($(compgen -W "$cached_accounts"))
                        fi
                        ;;
                esac
                return
            # Handle case where key=value is a single word (including key=)
            elif [[ $cur == *=* ]]; then
                local key="${{cur%%=*}}"
                local val="${{cur#*=}}"
                key=${{key,,}}
                case "$key" in
                    defaultqos)
                        if [ -f "/tmp/slurm_cli_qos.json" ]; then
                            COMPREPLY=($(compgen -W "$(jq -r '.qos[].name' /tmp/slurm_cli_qos.json 2>/dev/null)" -- "$val"))
                        fi
                        ;;
                    parent|organization)
                        if [ -n "$cached_accounts" ]; then
                            COMPREPLY=($(compgen -W "$cached_accounts" -- "$val"))
                        fi
                        ;;
                esac
                # Add key= prefix back
                if [[ ${{#COMPREPLY[@]}} -gt 0 ]]; then
                    COMPREPLY=("${{COMPREPLY[@]/#/$key=}}")
                fi
                return
            # Handle case where = is a separate word and we're after it
            elif [[ $prev == = ]]; then
                local key="${{COMP_WORDS[COMP_CWORD-2]}}"
                key=${{key,,}}
                case "$key" in
                    defaultqos)
                        if [ -f "/tmp/slurm_cli_qos.json" ]; then
                            COMPREPLY=($(compgen -W "$(jq -r '.qos[].name' /tmp/slurm_cli_qos.json 2>/dev/null)" -- "$cur"))
                        fi
                        ;;
                    parent|organization)
                        if [ -n "$cached_accounts" ]; then
                            COMPREPLY=($(compgen -W "$cached_accounts" -- "$cur"))
                        fi
                        ;;
                esac
                return
            else
                # For show: filter options only; for update/create: include 'set' keyword
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
            console.print(f"Updating account: {name}")

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
            Tuple of (columns, styles, template)
        """
        columns, styles, template = get_profile_config(
            profile, "accounts", profile_str
        )

        # Use default columns if profile specifies "*" or no columns
        if columns == "*" or columns is None:
            columns = cls.DEFAULT_COLUMNS

        # Merge with default styles
        merged_styles = dict(cls.DEFAULT_STYLES)
        merged_styles.update(styles)

        return columns, merged_styles, template

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
    def show(
        cls,
        field: str = None,
        style: str = "pretty",
        force_cache_update: bool = False,
        delimiter: str = ";",
        zebra: bool = False,
        profile: str = "default",
        profile_str: Optional[str] = None,
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

            if style == "json":
                # Print filtered JSON
                filtered_data = {"accounts": accounts}
                console.print_json(json.dumps(filtered_data, indent=2))
            elif style == "csv":
                # Get column configuration from profile
                columns, _, _ = cls._get_column_config(
                    profile, profile_str
                )

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
                # Get column configuration from profile
                columns, styles, template = cls._get_column_config(
                    profile, profile_str
                )

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
                        row = [
                            cls._format_value(account, col)
                            for col in columns
                        ]
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
