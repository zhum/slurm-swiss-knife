"""Utilities for managing associations."""

import io
import json
import subprocess
from typing import Any, Dict, List, Optional, Union

from rich.box import SIMPLE_HEAVY
from rich.console import Console
from rich.table import Table

from .base_resource import BaseSlurmResource
from .profiles import (
    format_with_template,
    get_profile_config,
    sort_data,
    sort_hierarchical_data,
)
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
ASSOCIATION_OPTIONS: List[str] = ASSOCIATION_FILTER_OPTIONS + ASSOCIATION_SET_OPTIONS


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
            # SET options
            "default_qos": "Default QOS for association",
            "fairshare": "Fairshare value",
            "grp_jobs": "Group jobs limit",
            "grp_jobs_accrue": "Group jobs accrue limit",
            "grp_submit": "Group submit limit",
            "grp_submit_jobs": "Group submit jobs limit",
            "grp_tres": "Group TRES limits",
            "grp_tres_mins": "Group TRES minutes limit",
            "grp_tres_run_mins": "Group TRES running minutes limit",
            "grp_wall": "Group wall time limit",
            "max_jobs": "Maximum jobs limit",
            "max_jobs_accrue": "Maximum jobs accrue limit",
            "max_submit": "Maximum submit limit",
            "max_submit_jobs": "Maximum submit jobs limit",
            "max_tres": "Maximum TRES limits",
            "max_tres_pj": "Maximum TRES per job",
            "max_tres_mins": "Maximum TRES minutes",
            "max_tres_mins_pj": "Maximum TRES minutes per job",
            "max_tres_pn": "Maximum TRES per node",
            "max_wall": "Maximum wall time limit",
            "max_wall_pj": "Maximum wall time per job",
        }

    @classmethod
    def generate_autocomplete_options(cls) -> str:
        """Generate bash autocomplete script for association options."""
        filter_keys = [opt.lower() for opt in ASSOCIATION_FILTER_OPTIONS]
        set_keys = [opt.lower() for opt in ASSOCIATION_SET_OPTIONS]
        qoslevel_opts = " ".join(opt.lower() for opt in ASSOCIATION_QOSLEVEL_OPTIONS)
        filter_opts = " ".join(f"{k}=" for k in filter_keys)
        set_opts = " ".join(f"{k}=" for k in set_keys)

        script = f"""
_slurm_cli_associations_autocomplete() {{
    local cmd="$1"
    local pos="$2"

    local cur="${{COMP_WORDS[COMP_CWORD]}}"
    local prev="${{COMP_WORDS[COMP_CWORD-1]}}"
    local name="${{COMP_WORDS[$pos]}}"

    local cached_accounts="$(_slurm_cache_accounts)"
    local cached_users="$(_slurm_cache_users)"
    local filter_options="{filter_opts}"
    local set_options="{set_opts} {qoslevel_opts}"
    local update_options="$filter_options $set_options set"
    local create_options="$filter_options $set_options"

    # Handle key=value, key+=value, or key-=value completion
    if _slurm_parse_keyval_ext "$cur" "$prev"; then
        case "$_key" in
            account)
                _slurm_complete_value "$cached_accounts" "$_key" "$_val" "$cur" ;;
            user)
                _slurm_complete_value "$cached_users" "$_key" "$_val" "$cur" ;;
            defaultqos|qos|qoslevel)
                _slurm_complete_value "$(_slurm_cache_qos)" "$_key" "$_val" "$cur" ;;
            partition)
                _slurm_complete_value "$(_slurm_cache_partitions)" "$_key" "$_val" "$cur" ;;
        esac
        [[ ${{#COMPREPLY[@]}} -gt 0 ]] && return
    fi

    # First argument after 'associations'
    if [[ $name == associations && $prev == associations ]]; then
        case "$cmd" in
            show|delete) _slurm_complete "$filter_options $cached_accounts" "$cur" ;;
            create)      _slurm_complete "$create_options" "$cur" ;;
            update)      _slurm_complete "$update_options $cached_accounts" "$cur" ;;
        esac
        return
    fi

    # Default completion for subsequent arguments
    case "$cmd" in
        show|delete) _slurm_complete "$filter_options" "$cur" ;;
        create)      _slurm_complete "$create_options" "$cur" ;;
        update)      _slurm_complete "$update_options" "$cur" ;;
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
    # All available columns from Slurm JSON output
    ALL_COLUMNS = [
        "account",
        "user",
        "cluster",
        "partition",
        "shares_raw",
        "priority",
        "qos",
        "is_default",
        "lineage",
        "parent_account",
        "id",
        "comment",
        "flags",
        "default",
        "max",
        "min",
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
            Tuple of (columns, styles, template, sort_field, sort_asc)
        """
        (
            columns,
            styles,
            template,
            sort_field,
            sort_asc,
        ) = get_profile_config(profile, "associations", profile_str)

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

    @classmethod
    def _format_value(cls, assoc: Dict[str, Any], column: str) -> str:
        """Format a value for display."""
        value = assoc.get(column, "")
        # Handle array fields
        if column in ("qos", "flags", "accounting"):
            if isinstance(value, list):
                return ",".join(str(v) for v in value) if value else "-"
        # Handle nested id field
        if column == "id" and isinstance(value, dict):
            return str(value.get("id", "-"))
        # Handle priority field (may be a dict with set/number)
        if column == "priority" and isinstance(value, dict):
            if value.get("set"):
                return str(value.get("number", 0))
            return "-"
        # Handle nested 'default' field (contains qos)
        if column == "default" and isinstance(value, dict):
            qos = value.get("qos", "")
            return qos if qos else "-"
        # Handle nested 'max' and 'min' fields (complex limit structures)
        if column in ("max", "min") and isinstance(value, dict):
            # Summarize the nested structure
            parts = []
            if "jobs" in value:
                jobs = value["jobs"]
                if isinstance(jobs, dict):
                    active = jobs.get("active", {})
                    if isinstance(active, dict) and active.get("set"):
                        parts.append(f"jobs={active.get('number', 0)}")
            if "tres" in value:
                tres = value["tres"]
                if isinstance(tres, dict):
                    for tres_type in ("per", "minutes"):
                        if tres_type in tres and isinstance(tres[tres_type], dict):
                            for k, v in tres[tres_type].items():
                                if isinstance(v, dict) and v.get("set"):
                                    parts.append(f"{k}={v.get('number', 0)}")
            return ", ".join(parts) if parts else "-"
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
    def _sort_hierarchically(
        cls, associations: List[Dict[str, Any]], indent: str = "  "
    ) -> List[Dict[str, Any]]:
        """Sort associations hierarchically and add depth/indent info.

        Args:
            associations: List of association dictionaries
            indent: Indentation string per level (default: two spaces)

        Returns:
            Sorted list with '_depth' and '_indent' keys added
        """
        # Build account hierarchy
        accounts = {}  # account -> {parent, users, children, assocs}
        for assoc in associations:
            account = assoc.get("account", "")
            parent = assoc.get("parent_account", "")
            user = assoc.get("user", "")

            if account not in accounts:
                accounts[account] = {
                    "parent": parent,
                    "users": [],
                    "children": [],
                    "account_assoc": None,
                }

            if user:
                accounts[account]["users"].append(assoc)
            else:
                accounts[account]["account_assoc"] = assoc

        # Build parent-child relationships
        for account, info in accounts.items():
            parent = info["parent"]
            if parent and parent in accounts:
                if account not in accounts[parent]["children"]:
                    accounts[parent]["children"].append(account)

        # Find root accounts
        root_accounts = [
            acc
            for acc, info in accounts.items()
            if not info["parent"] or info["parent"] not in accounts
        ]
        root_accounts.sort()

        # Traverse tree and build sorted list with depth
        result = []

        def add_account(account_name: str, depth: int):
            info = accounts.get(account_name, {})

            # Add account-level association
            if info.get("account_assoc"):
                assoc = info["account_assoc"].copy()
                assoc["_depth"] = depth
                assoc["_indent"] = indent * depth
                assoc["_is_account"] = True  # Flag for sorting
                result.append(assoc)

            # Add users (sorted)
            users = sorted(info.get("users", []), key=lambda u: u.get("user", ""))
            for user_assoc in users:
                assoc = user_assoc.copy()
                assoc["_depth"] = depth + 1
                assoc["_indent"] = indent * (depth + 1)
                assoc["_parent_id"] = account_name  # For hierarchical sorting
                assoc["_is_account"] = False
                result.append(assoc)

            # Add child accounts (sorted)
            children = sorted(info.get("children", []))
            for child in children:
                add_account(child, depth + 1)

        for root in root_accounts:
            add_account(root, 0)

        return result

    @classmethod
    def _show_tree(cls, associations: List[Dict[str, Any]]) -> None:
        """Display associations in a hierarchical tree format.

        Groups associations by account hierarchy and shows users under
        their respective accounts with proper indentation.

        Args:
            associations: List of association dictionaries
        """
        from rich.tree import Tree

        # Build account hierarchy
        # First, find all unique accounts and their parent relationships
        accounts = {}  # account -> {parent, users, children}
        for assoc in associations:
            account = assoc.get("account", "")
            parent = assoc.get("parent_account", "")
            user = assoc.get("user", "")
            partition = assoc.get("partition", "")
            qos = assoc.get("qos", [])
            if isinstance(qos, list):
                qos = ",".join(qos) if qos else ""

            if account not in accounts:
                accounts[account] = {
                    "parent": parent,
                    "users": [],
                    "children": [],
                    "partition": partition,
                    "qos": qos,
                }

            # If this is a user association, add to users list
            if user:
                accounts[account]["users"].append(
                    {"user": user, "partition": partition, "qos": qos}
                )

        # Build parent-child relationships
        for account, info in accounts.items():
            parent = info["parent"]
            if parent and parent in accounts:
                if account not in accounts[parent]["children"]:
                    accounts[parent]["children"].append(account)

        # Find root accounts (no parent or parent not in list)
        root_accounts = [
            acc
            for acc, info in accounts.items()
            if not info["parent"] or info["parent"] not in accounts
        ]

        # Sort root accounts
        root_accounts.sort()

        def add_children_to_node(parent_node, account_name: str, info: dict):
            """Add users and child accounts to a node."""
            # Add users under this account
            users = info.get("users", [])
            users.sort(key=lambda u: u["user"])
            for user_info in users:
                user = user_info["user"]
                u_qos = user_info.get("qos", "")
                u_part = user_info.get("partition", "")
                u_qos_str = f" [dim]qos={u_qos}[/dim]" if u_qos else ""
                u_part_str = f" [dim]partition={u_part}[/dim]" if u_part else ""
                parent_node.add(f"[green]{user}[/green]{u_part_str}{u_qos_str}")

            # Add child accounts
            children = info.get("children", [])
            children.sort()
            for child in children:
                child_info = accounts.get(child, {})
                qos_str = (
                    f" [dim]qos={child_info.get('qos', '')}[/dim]"
                    if child_info.get("qos")
                    else ""
                )
                part_str = (
                    f" [dim]partition={child_info.get('partition', '')}[/dim]"
                    if child_info.get("partition")
                    else ""
                )
                child_node = parent_node.add(
                    f"[bold yellow]{child}[/bold yellow]{part_str}{qos_str}"
                )
                add_children_to_node(child_node, child, child_info)

        # Build and print tree for each root account
        for root in root_accounts:
            info = accounts.get(root, {})
            qos_str = (
                f" [dim]qos={info.get('qos', '')}[/dim]" if info.get("qos") else ""
            )
            part_str = (
                f" [dim]partition={info.get('partition', '')}[/dim]"
                if info.get("partition")
                else ""
            )
            tree = Tree(f"[bold yellow]{root}[/bold yellow]{part_str}{qos_str}")
            add_children_to_node(tree, root, info)
            console.print(tree)

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
        indent: str = "  ",
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
            indent: Indentation string for tree mode (default: two spaces)
            tree: Show associations in hierarchical tree format
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
                    associations = cls._apply_filters(associations, [parsed_filter])
                    if not associations:
                        console.print(
                            f"[yellow]No associations match filter "
                            f"'{field}'.[/yellow]"
                        )
                        return
                else:
                    # Treat as account name filter
                    associations = [
                        assoc for assoc in associations if assoc.get("account") == field
                    ]
                    if not associations:
                        console.print(
                            f"[yellow]No associations for account "
                            f"'{field}'.[/yellow]"
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

            if tree:
                # Tree mode - sort hierarchically and add indent
                associations = cls._sort_hierarchically(associations, indent)
                # Apply hierarchical sorting if specified
                if sort_field:
                    associations = sort_hierarchical_data(
                        associations,
                        sort_field,
                        sort_asc,
                        depth_key="_depth",
                        parent_key="parent_account",
                        id_key="account",
                    )
            elif sort_field:
                # Flat mode sorting
                associations = sort_data(associations, sort_field, sort_asc)

            if style == "json":
                # Print filtered JSON
                filtered_data = {"associations": associations}
                console.print_json(json.dumps(filtered_data, indent=2))
            elif style == "csv":
                # Header
                headers = [col.title() for col in columns]
                print(delimiter.join(headers))

                # Data rows
                for assoc in associations:
                    row = []
                    for i, col in enumerate(columns):
                        value = cls._format_value(assoc, col)
                        # Add indent to first column in tree mode
                        if i == 0 and tree and "_indent" in assoc:
                            value = assoc["_indent"] + value
                        row.append(value)
                    # Replace "-" with empty for CSV
                    row = ["" if v == "-" else v for v in row]
                    print(delimiter.join(row))
            else:  # pretty style
                # If template is specified, use template-based output
                if template:
                    for assoc in associations:
                        output = format_with_template(
                            template, assoc, resource="associations"
                        )
                        console.print(output)
                else:
                    # Create a rich table
                    row_styles = ["", "on rgb(30,40,60)"] if zebra else None
                    table = Table(
                        title="Associations",
                        box=SIMPLE_HEAVY,
                        pad_edge=False,
                        padding=(0, 0),
                        row_styles=row_styles,
                        expand=False,
                    )

                    # Add columns based on profile
                    for col in columns:
                        table.add_column(
                            col.title(),
                            style=styles.get(col, ""),
                            no_wrap=True,
                            overflow="ignore",
                        )

                    # Add rows
                    for assoc in associations:
                        row = []
                        for i, col in enumerate(columns):
                            value = cls._format_value(assoc, col)
                            # Add indent to first column in tree mode
                            if i == 0 and tree and "_indent" in assoc:
                                value = assoc["_indent"] + value
                            row.append(value)
                        table.add_row(*row)

                    # Use buffer-based console to prevent column truncation
                    buf = io.StringIO()
                    wide_console = Console(file=buf, width=500, force_terminal=True)
                    wide_console.print(table)
                    output = buf.getvalue()
                    print(output, end="")

        except subprocess.CalledProcessError as e:
            error_msg = e.stderr or e
            console.print(f"[red]Failed to show associations:[/red] {error_msg}")
        except json.JSONDecodeError as e:
            console.print(f"[red]Failed to parse JSON output:[/red] {e}")

    @classmethod
    def create(cls, name: str, verbose: bool = False, **kwargs: Any) -> None:
        """Create a new association.

        Uses 'sacctmgr create user' command which creates user associations.

        Args:
            name: Username for the association
            verbose: Enable verbose output
            **kwargs: Additional options (account, partition, qos, etc.)
        """
        console.print(f"Creating association for user: {name}")
        args = [
            "sacctmgr",
            "-i",
            "create",
            "user",
            f"name={name}",
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
                f"[green]Association for user '{name}' created "
                f"successfully.[/green]"
            )
            if result.stdout:
                console.print(result.stdout)
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr or e
            console.print(
                f"[red]Failed to create association for user "
                f"'{name}':[/red] {error_msg}"
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
        """Update an association.

        Uses 'sacctmgr modify user' command.

        Args:
            name: Username for the association
            verbose: Enable verbose output
            dry_run: If True, print command without executing
            where_conditions: List of WHERE conditions
            set_values: List of SET values
            **kwargs: Additional SET values
        """
        args = ["sacctmgr", "-i", "modify", "user"]

        if where_conditions is not None:
            args.append("where")
            args.extend(where_conditions)
            args.append("set")
            if set_values:
                args.extend(set_values)
            if not dry_run:
                console.print(
                    f"Updating user associations where " f"{' '.join(where_conditions)}"
                )
        else:
            args.append("where")
            args.append(f"name={name}")
            args.append("set")
            for key, value in kwargs.items():
                if value is not None:
                    args.append(f"{key}={value}")
            if not dry_run:
                console.print(f"Updating association for user: {name}")

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
                console.print("[green]Association updated successfully.[/green]")
        except subprocess.CalledProcessError as e:
            console.print(f"[red]Failed to update association:[/red] {e.stderr or e}")

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
            console.print("[red]No conditions specified for delete[/red]")
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
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            console.print(f"[green]Deleted associations where {where_clause}[/green]")
            if result.stdout:
                console.print(result.stdout)
        except subprocess.CalledProcessError as e:
            console.print(f"[red]Failed to delete associations:[/red] {e.stderr or e}")
