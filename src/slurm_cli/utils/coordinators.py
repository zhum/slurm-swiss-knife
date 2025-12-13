"""Utilities for managing coordinators."""

import json
import subprocess
from typing import Any, Dict, List, Optional

from rich.box import SIMPLE_HEAVY
from rich.table import Table

from .base_resource import BaseSlurmResource
from .profiles import get_profile_config
from .utils import console


class Coordinator(BaseSlurmResource):
    def __init__(self, name: str, **kwargs: Any):
        self.name = name
        self.kwargs = kwargs

    @classmethod
    def get_profile_fields(cls) -> dict:
        """Return field names and descriptions for profile templates."""
        return {
            "account": "Account name",
            "name": "Coordinator username",
            "direct": "Whether coordinator is directly assigned",
        }

    # Default column configuration for coordinators
    DEFAULT_COLUMNS = ["name", "account", "direct"]
    DEFAULT_STYLES = {
        "name": "cyan",
        "account": "green",
        "direct": "yellow",
    }

    # Coordinator options for autocomplete
    COORDINATOR_OPTIONS = ["account", "name"]

    @classmethod
    def generate_autocomplete_options(cls) -> str:
        """Generate bash autocomplete script for coordinator options."""
        script = """
_slurm_cli_coordinators_autocomplete() {
    local cmd="$1"
    local pos="$2"

    name="${COMP_WORDS[$pos]}"
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"

    # Get cached account names if available
    local cached_accounts=""
    if [ -f "/tmp/slurm_cli_accounts.json" ]; then
        cached_accounts=$(jq -r '.accounts[].name' /tmp/slurm_cli_accounts.json 2>/dev/null | tr '\\n' ' ')
    fi

    # Get cached user names if available
    local cached_users=""
    if [ -f "/tmp/slurm_cli_users.json" ]; then
        cached_users=$(jq -r '.users[].name' /tmp/slurm_cli_users.json 2>/dev/null | tr '\\n' ' ')
    fi

    # Options for coordinators
    local filter_options="account= name="
    local update_options="account= name= name+= name-="

    # Check if we're completing a value after key= or key+= or key-=
    local key=""
    local val_prefix=""

    if [[ $cur == *[-+]=* ]] || [[ $cur == *=* ]]; then
        key=${cur%%[-+]*=*}
        key=${key%%=*}
        val_prefix=${cur#*=}
    elif [[ $prev == "=" ]] || [[ $prev == "+=" ]] || [[ $prev == "-=" ]]; then
        key="${COMP_WORDS[COMP_CWORD-2]}"
        val_prefix="$cur"
    elif [[ $prev == *[-+]= ]] || [[ $prev == *= ]]; then
        key=${prev%%[-+]*=}
        key=${key%%=}
        val_prefix="$cur"
    fi

    if [ -n "$key" ]; then
        key=${key,,}
        case "$key" in
            account)
                if [ -n "$cached_accounts" ]; then
                    COMPREPLY=($(compgen -W "$cached_accounts" -- "$val_prefix"))
                fi
                ;;
            name)
                if [ -n "$cached_users" ]; then
                    COMPREPLY=($(compgen -W "$cached_users" -- "$val_prefix"))
                fi
                ;;
        esac
        if [ ${#COMPREPLY[@]} -gt 0 ]; then
            return
        fi
    fi

    # Position-based completion
    if [[ $name == coordinators && $prev == coordinators ]] || [[ $name == coord && $prev == coord ]]; then
        case "$cmd" in
            show)
                local all_options="$cached_accounts $filter_options"
                if [[ $cur == '' ]]; then
                    COMPREPLY=($(compgen -W "$all_options"))
                else
                    COMPREPLY=($(compgen -W "$all_options" -- "$cur"))
                fi
                return
                ;;
            create|update)
                if [[ $cur == '' ]]; then
                    COMPREPLY=($(compgen -W "$update_options"))
                else
                    COMPREPLY=($(compgen -W "$update_options" -- "$cur"))
                fi
                return
                ;;
            delete)
                if [[ $cur == '' ]]; then
                    COMPREPLY=($(compgen -W "$filter_options"))
                else
                    COMPREPLY=($(compgen -W "$filter_options" -- "$cur"))
                fi
                return
                ;;
        esac
    fi

    # Default completion for subsequent arguments
    case "$cmd" in
        create|update)
            if [[ $cur == '' ]]; then
                COMPREPLY=($(compgen -W "$update_options"))
            else
                COMPREPLY=($(compgen -W "$update_options" -- "$cur"))
            fi
            ;;
        show|delete)
            if [[ $cur == '' ]]; then
                COMPREPLY=($(compgen -W "$filter_options"))
            else
                COMPREPLY=($(compgen -W "$filter_options" -- "$cur"))
            fi
            ;;
    esac
}
"""  # noqa: E501
        return script

    @classmethod
    def create(
        cls,
        name: str,
        verbose: bool = False,
        value: str = None,
        names: tuple = None,
    ) -> None:
        """Create a new coordinator."""
        if not value and not names:
            console.print(
                f"[red]Coordinator '{name}' creation failed:[/]"
                f"Use slurm-cli create coordinator <account(s)> <user(s)>"
            )
            return
        args = [
            "sacctmgr",
            "-i",
            "add",
            "coordinator",
            f"accounts={name}",
            f"names={value}",
        ]

        try:
            result = subprocess.run(
                args,
                check=True,
                capture_output=True,
                text=True,
            )
            console.print(
                f"[green]Coordinator '{name}' created successfully.[/green]"
            )
            if result.stdout:
                console.print(result.stdout)
        except subprocess.CalledProcessError as e:
            console.print(
                f"[red]Failed to create coordinator '{name}':[/]"
                f"{e.stderr or e}"
            )

    @classmethod
    def update(
        cls,
        account: str,
        verbose: bool = False,
        where_conditions: List[str] = None,
        set_values: List[str] = None,
        **kwargs: Any,
    ) -> None:
        """Update coordinators for an account.

        Supports two modes:
        1. Simple: update(account, name="user1,user2") or
            name+=... or name-=...
        2. WHERE/SET: update("", where_conditions=["account=ACC"],
                             set_values=["name=..."])

        Args:
            account: Account name to update coordinators for
            verbose: Enable verbose output
            where_conditions: List of WHERE conditions
            set_values: List of SET values (name=, name+=, name-=)
            **kwargs: Additional options like name=, name+=, name-=
        """
        # Build sacctmgr command
        args = ["sacctmgr", "-i", "add", "coordinator"]

        if where_conditions is not None:
            # WHERE/SET mode - extract account from conditions
            for cond in where_conditions:
                args.append(cond)
            if set_values:
                for val in set_values:
                    args.append(val)
            where_str = " ".join(where_conditions)
            set_str = " ".join(set_values) if set_values else ""
            console.print(
                f"Updating coordinators: {where_str} {set_str}"
            )
        else:
            # Simple mode - update by account name
            args.append(f"account={account}")
            for key, value in kwargs.items():
                if value is not None:
                    # Handle name, name+, name- keys
                    if key == "name_add":
                        args.append(f"name+={value}")
                    elif key == "name_remove":
                        args.append(f"name-={value}")
                    else:
                        args.append(f"{key}={value}")
            console.print(
                f"Updating coordinators for account: {account}"
            )

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
                    "[green]Coordinators updated successfully.[/green]"
                )
        except subprocess.CalledProcessError as e:
            console.print(
                f"[red]Failed to update coordinators:[/red] {e.stderr or e}"
            )

    @classmethod
    def delete(
        cls,
        account: str,
        names: List[str] = None,
        verbose: bool = False,
    ) -> None:
        """Delete coordinators from an account.

        Args:
            account: Account name to remove coordinators from
            names: List of coordinator names to remove
            verbose: Enable verbose output
        """
        if not names:
            console.print(
                "[red]No coordinator names specified for deletion.[/red]"
            )
            return

        # Use sacctmgr add coordinator with name-= to remove
        args = [
            "sacctmgr",
            "-i",
            "add",
            "coordinator",
            f"account={account}",
            f"name-={','.join(names)}",
        ]

        try:
            result = subprocess.run(
                args,
                check=True,
                capture_output=True,
                text=True,
            )
            console.print(
                f"[green]Removed coordinators {', '.join(names)} "
                f"from account {account}[/green]"
            )
            if result.stdout:
                console.print(result.stdout)
        except subprocess.CalledProcessError as e:
            console.print(
                f"[red]Failed to delete coordinators:[/red] {e.stderr or e}"
            )

    @classmethod
    def _extract_coordinators(
        cls, accounts: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Extract coordinators from accounts data.

        Returns a list of coordinator records with account info.
        """
        coordinators = []
        for account in accounts:
            account_name = account.get("name", "")
            for coord in account.get("coordinators", []):
                coordinators.append(
                    {
                        "name": coord.get("name", ""),
                        "account": account_name,
                        "direct": "Yes"
                        if coord.get("direct")
                        else "No",
                    }
                )
        return coordinators

    @classmethod
    def _format_value(cls, coord: Dict[str, Any], column: str) -> str:
        """Format a value for display."""
        value = coord.get(column, "")
        if value is None or value == "":
            return "-"
        return str(value)

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
        """Show coordinator information.

        Args:
            field: Optional filter (user name or account=name)
            style: Output style ("pretty", "json", or "csv")
            force_cache_update: Whether to force cache update (unused)
            delimiter: Delimiter for CSV output (default: ";")
            zebra: Use zebra striping for table rows
            profile: Profile name to use for output formatting
            profile_str: Inline profile string (overrides profile)
        """
        # Get profile configuration
        columns, styles, template = get_profile_config(
            profile, "coordinators", profile_str
        )

        # Use default columns if not specified
        if columns == "*" or columns is None:
            columns = cls.DEFAULT_COLUMNS

        # Merge with default styles
        merged_styles = dict(cls.DEFAULT_STYLES)
        if styles:
            merged_styles.update(styles)

        try:
            result = subprocess.run(
                [
                    "sacctmgr",
                    "show",
                    "accounts",
                    "withcoord",
                    "--json",
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            if not result.stdout:
                console.print("[yellow]No coordinators found.[/yellow]")
                return

            # Parse JSON data
            data = json.loads(result.stdout)
            accounts = data.get("accounts", [])

            # Extract coordinators from accounts
            coordinators = cls._extract_coordinators(accounts)

            if not coordinators:
                console.print("[yellow]No coordinators found.[/yellow]")
                return

            # Filter if field is specified
            if field:
                if "=" in field:
                    # Filter like account=nvidia
                    key, value = field.split("=", 1)
                    key = key.lower()
                    coordinators = [
                        c
                        for c in coordinators
                        if str(c.get(key, "")).lower() == value.lower()
                    ]
                else:
                    # Filter by coordinator name
                    coordinators = [
                        c
                        for c in coordinators
                        if c.get("name", "").lower() == field.lower()
                    ]

                if not coordinators:
                    console.print(
                        f"[yellow]No coordinators matching "
                        f"'{field}' found.[/yellow]"
                    )
                    return

            # Output based on style
            if style == "json":
                console.print_json(json.dumps(coordinators, indent=2))
            elif style == "csv":
                # CSV header
                print(delimiter.join(columns))
                for coord in coordinators:
                    row = [
                        cls._format_value(coord, col) for col in columns
                    ]
                    print(delimiter.join(row))
            else:
                # Pretty table output
                table = Table(
                    title="Coordinators",
                    box=SIMPLE_HEAVY,
                    show_header=True,
                    header_style="bold",
                )

                # Add columns
                for col in columns:
                    style = merged_styles.get(col, "white")
                    table.add_column(col.title(), style=style)

                # Add rows
                for i, coord in enumerate(coordinators):
                    row_style = None
                    if zebra and i % 2 == 1:
                        row_style = "on grey15"
                    row = [
                        cls._format_value(coord, col) for col in columns
                    ]
                    table.add_row(*row, style=row_style)

                console.print(table)

        except subprocess.CalledProcessError as e:
            console.print(
                f"[red]Failed to show coordinators:[/red] {e.stderr or e}"
            )
