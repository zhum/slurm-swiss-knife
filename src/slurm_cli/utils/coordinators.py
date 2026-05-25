"""Utilities for managing coordinators."""

import json
import subprocess
from typing import Any, Dict, List, Optional, Union

from rich.box import SIMPLE_HEAVY
from rich.table import Table

from .base_resource import BaseSlurmResource
from .profiles import get_profile_config, sort_data
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

    local cur="${COMP_WORDS[COMP_CWORD]}"
    local prev="${COMP_WORDS[COMP_CWORD-1]}"

    local cached_accounts="$(_slurm_cache_accounts)"
    local cached_users="$(_slurm_cache_users)"
    local options="account= user= name="

    # Handle key=value completion for current word
    if _slurm_parse_keyval "$cur" "$prev"; then
        case "$_key" in
            account) _slurm_complete_value "$cached_accounts" "$_key" "$_val" "$cur" ;;
            name|user) _slurm_complete_value "$cached_users" "$_key" "$_val" "$cur" ;;
        esac
        [[ ${#COMPREPLY[@]} -gt 0 ]] && return
    fi

    # For create, check what's already been specified
    if [[ "$cmd" == "create" ]]; then
        local has_account=false
        local has_user=false
        local has_positional_user=false

        # Scan previous words to see what's already specified
        for ((i=pos+1; i<COMP_CWORD; i++)); do
            local word="${COMP_WORDS[$i]}"
            if [[ "$word" == account=* ]]; then
                has_account=true
            elif [[ "$word" == name=* || "$word" == user=* ]]; then
                has_user=true
            elif [[ "$word" != *=* && "$word" != -* ]]; then
                # Positional argument (user)
                has_positional_user=true
            fi
        done

        # First arg after coordinators: show options + users
        if [[ $prev == coordinators || $prev == coord ]]; then
            _slurm_complete "$options $cached_users" "$cur"
            return
        fi

        # After user= or positional user: suggest account=
        if $has_user || $has_positional_user; then
            if ! $has_account; then
                _slurm_complete "$options" "$cur"
                return
            fi
        fi

        # After account=: suggest user= with users
        if $has_account; then
            if ! $has_user && ! $has_positional_user; then
                _slurm_complete "$options $cached_users" "$cur"
                return
            fi
        fi

        # Default: show all options
        _slurm_complete "$options $cached_users" "$cur"
        return
    fi

    # For show/delete
    if [[ $prev == coordinators || $prev == coord ]]; then
        _slurm_complete "$options $cached_accounts $cached_users" "$cur"
    else
        _slurm_complete "$options" "$cur"
    fi
}
"""  # noqa: E501
        return script

    @classmethod
    def create(
        cls,
        user_name: Union[str, None] = None,
        verbose: bool = False,
        account: Union[str, None] = None,
        **kwargs,
    ) -> None:
        """Create a new coordinator.

        Args:
            user_name: User name (from positional arg or name= option)
            verbose: Enable verbose output
            account: Account name (from account= option)
            **kwargs: Additional options
        """
        if not account:
            console.print(
                "[red]Coordinator creation failed:[/] "
                "account= is required.\n"
                "Usage: slurm-cli create coordinators USER account=ACCOUNT"
            )
            return

        if not user_name:
            console.print(
                "[red]Coordinator creation failed:[/] "
                "User name is required.\n"
                "Usage: slurm-cli create coordinators USER account=ACCOUNT"
            )
            return

        args = [
            "sacctmgr",
            "-i",
            "add",
            "coordinator",
            f"accounts={account}",
            f"names={user_name}",
        ]

        if verbose:
            console.print(f"[dim]Running: {' '.join(args)}[/dim]")

        try:
            result = subprocess.run(
                args,
                check=True,
                capture_output=True,
                text=True,
            )
            console.print(
                f"[green]Coordinator '{user_name}' added to account "
                f"'{account}' successfully.[/green]"
            )
            if result.stdout:
                console.print(result.stdout)
        except subprocess.CalledProcessError as e:
            console.print(
                f"[red]Failed to create coordinator '{user_name}' "
                f"for account '{account}':[/] {e.stderr or e}"
            )

    @classmethod
    def update(
        cls,
        account: Union[str, None] = None,
        verbose: bool = False,
        where_conditions: Union[List[str], None] = None,
        set_values: Union[List[str], None] = None,
        **kwargs: Any,
    ) -> None:
        """Update operation is not supported for coordinators.

        Coordinators can only be added (create) or removed (delete).
        """
        console.print(
            "[red]Update operation is not supported for coordinators.[/red]\n"
            "Use 'slurm-cli create coordinators' to add coordinators or "
            "'slurm-cli delete coordinators' to remove them."
        )

    @classmethod
    def delete(
        cls,
        account: Union[str, None] = None,
        names: Union[List[str], None] = None,
        verbose: bool = False,
    ) -> None:
        """Delete coordinators from an account.

        Args:
            account: Account name to remove coordinators from
            names: List of coordinator names to remove
            verbose: Enable verbose output
        """
        if not names:
            console.print("[red]No coordinator names specified for deletion.[/red]")
            return

        for name in names:
            args = [
                "sacctmgr",
                "-i",
                "delete",
                "coordinator",
                f"account={account}",
                f"name={name}",
            ]

            if verbose:
                console.print(f"[dim]Running: {' '.join(args)}[/dim]")

            try:
                result = subprocess.run(
                    args,
                    check=True,
                    capture_output=True,
                    text=True,
                )
                console.print(
                    f"[green]Removed coordinator '{name}' "
                    f"from account '{account}'[/green]"
                )
                if result.stdout:
                    console.print(result.stdout)
            except subprocess.CalledProcessError as e:
                console.print(
                    f"[red]Failed to delete coordinator '{name}':[/red] "
                    f"{e.stderr or e}"
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
                        "direct": "Yes" if coord.get("direct") else "No",
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
        field: Union[str, None] = None,
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
        (
            columns,
            styles,
            template,
            sort_field,
            sort_asc,
        ) = get_profile_config(profile, "coordinators", profile_str)

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

            # Apply sorting
            if sort_field:
                coordinators = sort_data(coordinators, sort_field, sort_asc)

            # Output based on style
            if style == "json":
                console.print_json(json.dumps(coordinators, indent=2))
            elif style == "csv":
                # CSV header
                print(delimiter.join(columns))
                for coord in coordinators:
                    row = [cls._format_value(coord, col) for col in columns]
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
                    row = [cls._format_value(coord, col) for col in columns]
                    table.add_row(*row, style=row_style)

                console.print(table)

        except subprocess.CalledProcessError as e:
            console.print(f"[red]Failed to show coordinators:[/red] {e.stderr or e}")
