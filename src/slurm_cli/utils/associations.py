"""Utilities for managing associations."""

import json
import subprocess
from typing import Any, Dict, List, Optional

from rich.box import SIMPLE_HEAVY
from rich.table import Table

from .base_resource import BaseSlurmResource
from .profiles import format_with_template, get_profile_config
from .utils import console

# Association filter/select options (used for WHERE clause)
ASSOCIATION_FILTER_OPTIONS: List[str] = [
    "Account",
    "Cluster",
    "Partition",
    "User",
]

# Association SET options (sacctmgr field names for create/update)
ASSOCIATION_SET_OPTIONS: List[str] = [
    "DefaultQOS",
    "Fairshare",
    "Share",
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
    "MaxTRESPJ",
    "MaxTRESPerJob",
    "MaxTRESMins",
    "MaxTRESMinsPJ",
    "MaxTRESMinsPerJob",
    "MaxTRESPN",
    "MaxTRESPerNode",
    "MaxWall",
    "MaxWallDurationPerJob",
    "Priority",
]

# QosLevel supports =, +=, -= operators
ASSOCIATION_QOSLEVEL_OPTIONS: List[str] = [
    "QosLevel=",
    "QosLevel+=",
    "QosLevel-=",
]

# Combined options for backward compatibility
ASSOCIATION_OPTIONS: List[str] = (
    ASSOCIATION_FILTER_OPTIONS + ASSOCIATION_SET_OPTIONS
)


class Association(BaseSlurmResource):
    def __init__(self, account: str, **kwargs: Any):
        self.account = account
        self.kwargs = kwargs

    @classmethod
    def get_profile_fields(cls) -> dict:
        """Return field names and descriptions for profile templates."""
        return {
            "account": "Account name",
            "user": "User name (empty for account associations)",
            "cluster": "Cluster name",
            "partition": "Partition name",
            "shares_raw": "Raw shares value",
            "priority": "Priority value",
            "qos": "List of allowed QOS",
            "is_default": "Whether this is the default association",
            "lineage": "Account lineage path",
            "parent_account": "Parent account name",
        }

    @classmethod
    def generate_autocomplete_options(cls) -> str:
        """Generate bash autocomplete script for association options."""
        filter_keys = [
            opt.lower() for opt in ASSOCIATION_FILTER_OPTIONS
        ]
        set_keys = [opt.lower() for opt in ASSOCIATION_SET_OPTIONS]
        qoslevel_opts = " ".join(
            [opt.lower() for opt in ASSOCIATION_QOSLEVEL_OPTIONS]
        )

        script = f"""
_slurm_cli_associations_autocomplete() {{
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

    # Get cached user names if available
    local cached_users=""
    if [ -f "/tmp/slurm_cli_users.json" ]; then
        cached_users=$(jq -r '.users[].name' /tmp/slurm_cli_users.json 2>/dev/null | tr '\\n' ' ')
    fi

    # Filter options (for WHERE clause: account, cluster, partition, user)
    local filter_options="{'= '.join(filter_keys)}="
    # SET options (for modifying values)
    local set_options="{'= '.join(set_keys)}= {qoslevel_opts}"
    # All options for show/filter
    local all_filter_options="$filter_options"
    # All options for update (filter + set + 'set' keyword)
    local update_options="$filter_options $set_options set"
    # Options for create (filter for specifying target + set for values)
    local create_options="$filter_options $set_options"

    # First, check if we're completing a value after key= or key+= or key-=
    # This takes priority over position-based completion
    # Match: "key=", "key=val", "key+=", "key+=val", "key-=", "key-=val"
    # Also handle COMP_WORDBREAKS splitting: when = is in COMP_WORDBREAKS,
    # "user=" becomes words: "user", "=", "" so prev="=" and cur=""
    local key=""
    local val_prefix=""
    
    if [[ $cur == *[-+]=* ]] || [[ $cur == *=* ]]; then
        # cur contains "=" (e.g., "key=", "key=val", "key+=val"), extract key
        key=${{cur%%[-+]*=*}}
        key=${{key%%=*}}
        val_prefix=${{cur#*=}}
    elif [[ $prev == "=" ]] || [[ $prev == "+=" ]] || [[ $prev == "-=" ]]; then
        # COMP_WORDBREAKS split: prev is "=" or "+=" or "-=", key is before that
        key="${{COMP_WORDS[COMP_CWORD-2]}}"
        val_prefix="$cur"
    elif [[ $prev == *[-+]= ]] || [[ $prev == *= ]]; then
        # prev is "key=" or "key+=", cur is the value
        key=${{prev%%[-+]*=}}
        key=${{key%%=}}
        val_prefix="$cur"
    fi
    
    if [ -n "$key" ]; then
        key=${{key,,}}

        case "$key" in
            account)
                if [ -n "$cached_accounts" ]; then
                    COMPREPLY=($(compgen -W "$cached_accounts" -- "$val_prefix"))
                fi
                ;;
            user)
                if [ -n "$cached_users" ]; then
                    COMPREPLY=($(compgen -W "$cached_users" -- "$val_prefix"))
                fi
                ;;
            defaultqos|qos|qoslevel)
                if [ -f "/tmp/slurm_cli_qos.json" ]; then
                    COMPREPLY=($(compgen -W "$(jq -r '.qos[].name' /tmp/slurm_cli_qos.json 2>/dev/null)" -- "$val_prefix"))
                fi
                ;;
            partition)
                if [ -f "/tmp/slurm_cli_partitions.json" ]; then
                    COMPREPLY=($(compgen -W "$(jq -r 'keys[]' /tmp/slurm_cli_partitions.json 2>/dev/null)" -- "$val_prefix"))
                fi
                ;;
            cluster)
                # No cache for clusters typically, but could add if needed
                ;;
        esac
        if [ ${{#COMPREPLY[@]}} -gt 0 ]; then
            return
        fi
    fi

    # If we're on the name field (right after 'associations')
    if [[ $name == associations && $prev == associations ]]; then
        case "$cmd" in
            show)
                # For show, allow filter options and account names
                local all_options="$cached_accounts $all_filter_options"
                if [[ $cur == '' ]]; then
                    COMPREPLY=($(compgen -W "$all_options"))
                else
                    COMPREPLY=($(compgen -W "$all_options" -- "$cur"))
                fi
                return
                ;;
            delete)
                # For delete, allow filter options and account names
                local all_options="$cached_accounts $all_filter_options"
                if [[ $cur == '' ]]; then
                    COMPREPLY=($(compgen -W "$all_options"))
                else
                    COMPREPLY=($(compgen -W "$all_options" -- "$cur"))
                fi
                return
                ;;
            create)
                # For create, show filter + set options
                if [[ $cur == '' ]]; then
                    COMPREPLY=($(compgen -W "$create_options"))
                else
                    COMPREPLY=($(compgen -W "$create_options" -- "$cur"))
                fi
                return
                ;;
            update)
                # For update, show filter options, set options, and 'set' keyword
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
            # For subsequent args in delete, show filter options
            if [[ $cur == '' ]]; then
                COMPREPLY=($(compgen -W "$all_filter_options"))
            else
                COMPREPLY=($(compgen -W "$all_filter_options" -- "$cur"))
            fi
            ;;
        show)
            # For show: filter options only
            if [[ $cur == '' ]]; then
                COMPREPLY=($(compgen -W "$all_filter_options"))
            else
                COMPREPLY=($(compgen -W "$all_filter_options" -- "$cur"))
            fi
            ;;
        create)
            # For create: filter + set options
            if [[ $cur == '' ]]; then
                COMPREPLY=($(compgen -W "$create_options"))
            else
                COMPREPLY=($(compgen -W "$create_options" -- "$cur"))
            fi
            ;;
        update)
            # For update: filter + set options + 'set' keyword
            if [[ $cur == '' ]]; then
                COMPREPLY=($(compgen -W "$update_options"))
            else
                COMPREPLY=($(compgen -W "$update_options" -- "$cur"))
            fi
            ;;
    esac
}}
"""  # noqa: E501
        return script

    # Default column configuration for associations
    DEFAULT_COLUMNS = [
        "account",
        "user",
        "cluster",
        "partition",
        "shares_raw",
        "qos",
    ]
    DEFAULT_STYLES = {
        "account": "cyan",
        "user": "green",
        "cluster": "yellow",
        "partition": "magenta",
        "shares_raw": "white",
        "qos": "blue",
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
            profile, "associations", profile_str
        )

        # Use default columns if profile specifies "*" or no columns
        if columns == "*" or columns is None:
            columns = cls.DEFAULT_COLUMNS

        # Merge with default styles
        merged_styles = dict(cls.DEFAULT_STYLES)
        merged_styles.update(styles)

        return columns, merged_styles, template

    @classmethod
    def _format_value(cls, assoc: Dict[str, Any], column: str) -> str:
        """Format a value for display."""
        value = assoc.get(column, "")
        # Handle array fields
        if column in ("qos", "flags", "accounting"):
            if isinstance(value, list):
                return (
                    ", ".join(str(v) for v in value) if value else "-"
                )
        # Handle nested id field
        if column == "id" and isinstance(value, dict):
            return str(value.get("id", "-"))
        if value is None or value == "":
            return "-"
        return str(value)

    @classmethod
    def _parse_filter(cls, filter_str: str) -> Optional[tuple]:
        """Parse a filter string like 'account=nvidia'.

        Returns:
            Tuple of (key, value) if valid filter, None otherwise.
        """
        if "=" in filter_str:
            key, value = filter_str.split("=", 1)
            return (key.lower(), value)
        return None

    @classmethod
    def _apply_filters(
        cls, associations: List[Dict[str, Any]], filters: List[tuple]
    ) -> List[Dict[str, Any]]:
        """Apply filters to association list.

        Args:
            associations: List of association dictionaries
            filters: List of (key, value) tuples to filter by

        Returns:
            Filtered list of associations
        """
        for key, value in filters:
            associations = [
                assoc
                for assoc in associations
                if str(assoc.get(key, "")).lower() == value.lower()
            ]
        return associations

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
        """Show association information.

        Args:
            field: Optional filter (e.g., account=nvidia or user=john)
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
                ["sacctmgr", "show", "associations", "--json"],
                check=True,
                capture_output=True,
                text=True,
            )

            if not result.stdout:
                console.print("[yellow]No associations found.[/yellow]")
                return

            # Parse JSON data
            data = json.loads(result.stdout)
            associations = data.get("associations", [])

            # Filter by field if specified
            if field:
                # Check if field is a filter (contains '=') or a name
                parsed_filter = cls._parse_filter(field)
                if parsed_filter:
                    # It's a filter like account=nvidia
                    associations = cls._apply_filters(
                        associations, [parsed_filter]
                    )
                    if not associations:
                        console.print(
                            f"[yellow]No associations match filter "
                            f"'{field}'.[/yellow]"
                        )
                        return
                else:
                    # Treat as account name filter
                    associations = [
                        assoc
                        for assoc in associations
                        if assoc.get("account") == field
                    ]
                    if not associations:
                        console.print(
                            f"[yellow]No associations for account "
                            f"'{field}'.[/yellow]"
                        )
                        return

            if style == "json":
                # Print filtered JSON
                filtered_data = {"associations": associations}
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
                for assoc in associations:
                    row = [
                        cls._format_value(assoc, col) for col in columns
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
                    for assoc in associations:
                        output = format_with_template(
                            template, assoc, resource="associations"
                        )
                        console.print(output)
                else:
                    # Create a rich table
                    row_styles = (
                        ["", "on rgb(30,40,60)"] if zebra else None
                    )
                    table = Table(
                        title="Associations",
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
                            no_wrap=(
                                col in ("account", "user", "cluster")
                            ),
                        )

                    # Add rows
                    for assoc in associations:
                        row = [
                            cls._format_value(assoc, col)
                            for col in columns
                        ]
                        table.add_row(*row)

                    console.print(table)

        except subprocess.CalledProcessError as e:
            error_msg = e.stderr or e
            console.print(
                f"[red]Failed to show associations:[/red] {error_msg}"
            )
        except json.JSONDecodeError as e:
            console.print(
                f"[red]Failed to parse JSON output:[/red] {e}"
            )

    @classmethod
    def create(
        cls, account: str, verbose: bool = False, **kwargs: Any
    ) -> None:
        """Create a new association."""
        console.print(f"Creating association for account: {account}")
        args = [
            "sacctmgr",
            "-i",
            "create",
            "association",
            f"account={account}",
        ]
        for key, value in kwargs.items():
            if value is not None:
                args.append(f"{key}={value}")

        try:
            result = subprocess.run(
                args,
                check=True,
                capture_output=True,
                text=True,
            )
            console.print(
                f"[green]Association for '{account}' created "
                f"successfully.[/green]"
            )
            if result.stdout:
                console.print(result.stdout)
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr or e
            console.print(
                f"[red]Failed to create association for "
                f"'{account}':[/red] {error_msg}"
            )

    @classmethod
    def update(
        cls,
        account: str,
        verbose: bool = False,
        where_conditions: Optional[List[str]] = None,
        set_values: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> None:
        """Update an association.

        Args:
            account: Account name
            verbose: Enable verbose output
            where_conditions: List of WHERE conditions
            set_values: List of SET values
            **kwargs: Additional SET values
        """
        args = ["sacctmgr", "-i", "modify", "association"]

        if where_conditions is not None:
            args.append("where")
            args.extend(where_conditions)
            args.append("set")
            if set_values:
                args.extend(set_values)
            console.print(
                f"Updating associations where {' '.join(where_conditions)}"
            )
        else:
            args.append("where")
            args.append(f"account={account}")
            args.append("set")
            for key, value in kwargs.items():
                if value is not None:
                    args.append(f"{key}={value}")
            console.print(
                f"Updating association for account: {account}"
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
                    "[green]Association updated successfully.[/green]"
                )
        except subprocess.CalledProcessError as e:
            console.print(
                f"[red]Failed to update association:[/red] {e.stderr or e}"
            )

    @classmethod
    def delete(
        cls,
        conditions: List[str],
        dry_run: bool = False,
        force: bool = False,
    ) -> None:
        """Delete associations matching the given conditions.

        Args:
            conditions: List of filter conditions
            (e.g., ["user=john", "partition=batch"])
            dry_run: If True, only show what would be deleted
            force: If True, skip confirmation
        """
        if not conditions:
            console.print(
                "[red]No conditions specified for delete[/red]"
            )
            return

        # Build the WHERE clause
        where_clause = " ".join(conditions)

        if dry_run:
            console.print(
                f"[yellow]DRY RUN:[/yellow] Would delete associations "
                f"where {where_clause}"
            )
            return

        # Build and execute the command
        cmd = ["sacctmgr", "-i", "delete", "association", "where"]
        cmd.extend(conditions)

        try:
            result = subprocess.run(
                cmd, check=True, capture_output=True, text=True
            )
            console.print(
                f"[green]Deleted associations where {where_clause}[/green]"
            )
            if result.stdout:
                console.print(result.stdout)
        except subprocess.CalledProcessError as e:
            console.print(
                f"[red]Failed to delete associations:[/red] {e.stderr or e}"
            )
