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
ACCOUNT_OPTIONS: List[str] = [
    "Cluster",
    "DefaultQOS",
    "Description",
    "Fairshare",
    "GrpJobs",
    "GrpJobsAccrue",
    "GrpSubmit",
    "GrpSubmitJobs",
    "GrpTRES",
    "GrpTRESMins",
    "GrpTRESRunMins",
    "GrpWall",
    "MaxJobs",
    "MaxJobsAccrue",
    "MaxSubmit",
    "MaxSubmitJobs",
    "MaxTRES",
    "MaxTRESMins",
    "MaxWall",
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

    # If we're on the name field (right after 'accounts')
    if [[ $name == accounts && $prev == accounts ]]; then
        if [ -f "/tmp/slurm_cli_accounts.json" ]; then
            COMPREPLY=($(compgen -W "$(jq -r 'keys[]' /tmp/slurm_cli_accounts.json)" -- "$cur"))
        fi
        return
    fi

    case "$cmd" in
        show|delete)
            return
            ;;
        create|update)
            if [[ $cur == = || $prev == = ]]; then
                local key
                if [[ $cur == = ]]; then
                    key=${{COMP_WORDS[COMP_CWORD-1]}}
                else
                    key=${{COMP_WORDS[COMP_CWORD-2]}}
                fi
                key=${{key,,}}

                case "$key" in
                    defaultqos)
                        if [ -f "/tmp/slurm_cli_qos.json" ]; then
                            COMPREPLY=($(compgen -W "$(jq -r 'keys[]' /tmp/slurm_cli_qos.json)" -- "${{cur#*=}}"))
                        fi
                        ;;
                    parent)
                        if [ -f "/tmp/slurm_cli_accounts.json" ]; then
                            COMPREPLY=($(compgen -W "$(jq -r 'keys[]' /tmp/slurm_cli_accounts.json)" -- "${{cur#*=}}"))
                        fi
                        ;;
                esac
                return
            else
                local -a valid_keys=({'= '.join(valid_keys)}=)
                if [[ $cur == '' ]]; then
                    COMPREPLY=(${{valid_keys[@]}})
                else
                    COMPREPLY=($(compgen -W "${{valid_keys[*]}}" "$cur"))
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
        args = ["sacctmgr", "create", "account", name]
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
    def update(cls, name: str, **kwargs: Any) -> None:
        """Update an account."""
        console.print(f"Updating account: {name}")

    @classmethod
    def delete(cls, name: str) -> None:
        """Delete an account."""
        console.print(f"Deleting account: {name}")

    # Default column configuration for accounts
    DEFAULT_COLUMNS = [
        "name",
        "description",
        "organization",
        "coordinators",
    ]
    DEFAULT_STYLES = {
        "name": "cyan",
        "description": "white",
        "organization": "green",
        "coordinators": "yellow",
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
        if column == "coordinators":
            if isinstance(value, list):
                return ", ".join(value) if value else "-"
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
        """Show account information.

        Args:
            field: Optional account name to filter by
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

            # Filter by field (account name) if specified
            if field:
                accounts = [
                    acc for acc in accounts if acc.get("name") == field
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
