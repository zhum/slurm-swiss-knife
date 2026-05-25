"""Utilities for managing nodes."""

import json
import subprocess
from typing import Any, Dict, List, Optional, Union

from rich.box import SIMPLE_HEAVY
from rich.markup import escape
from rich.table import Table

from .base_resource import BaseSlurmResource
from .profiles import format_with_template, get_profile_config, sort_data
from .utils import console


class Node(BaseSlurmResource):
    _WIDTH = None

    # Node options for autocomplete
    NODE_SHOW_OPTIONS = [
        "name",
        "state",
        "partition",
        "features",
        "gres",
    ]
    NODE_UPDATE_OPTIONS = [
        "nodename",  # Sets NEW node name (for renaming)
        "activefeatures",
        "availablefeatures",
        "comment",
        "cpubind",
        "extra",
        "gres",
        "instanceid",
        "instancetype",
        "nodeaddr",
        "nodehostname",
        "reason",
        "resumeafter",
        "state",
        "weight",
    ]
    # Valid states for node update
    NODE_UPDATE_STATES = [
        "cancel_reboot",
        "down",
        "drain",
        "fail",
        "future",
        "idle",
        "noresp",
        "resume",
        "undrain",
    ]
    # Valid values for CpuBind option
    NODE_CPUBIND_VALUES = [
        "none",
        "socket",
        "ldom",
        "core",
        "thread",
        "off",
    ]
    # States shown in show command (informational)
    NODE_STATES = [
        "idle",
        "alloc",
        "drain",
        "down",
        "resume",
        "undrain",
        "fail",
        "power_down",
        "power_up",
    ]
    # Only future and cloud states allowed for node creation
    NODE_CREATE_STATES = ["future", "cloud"]
    NODE_CREATE_OPTIONS = [
        "state",
        "cpus",
        "features",
        "gres",
        "reason",
        "weight",
    ]

    # Default columns for table output
    DEFAULT_COLUMNS = [
        "name",
        "state",
        "cpus",
        "alloc_cpus",
        "real_memory",
        "alloc_memory",
        "gres",
    ]

    # Default styles for table columns
    DEFAULT_STYLES = {
        "name": "cyan",
        "state": "green",
        "cpus": "yellow",
        "alloc_cpus": "yellow",
        "real_memory": "blue",
        "alloc_memory": "blue",
        "gres": "magenta",
    }

    def __init__(self, name: str, **kwargs: Any):
        self.name = name
        self.kwargs = kwargs

    # Node filter options for selecting nodes (first argument)
    NODE_FILTER_OPTIONS = [
        "ALL",
        "partition",
        "state",
        "user",
        "reservation",
        "drainreason",
    ]

    @classmethod
    def generate_autocomplete_options(cls) -> str:
        """Generate bash autocomplete script for node options."""
        show_opts = " ".join(f"{opt}=" for opt in cls.NODE_SHOW_OPTIONS)
        update_opts = " ".join(f"{opt}=" for opt in cls.NODE_UPDATE_OPTIONS)
        # Add node filter options for selecting nodes
        filter_opts = " ".join(
            f"{opt}=" if opt != "ALL" else opt for opt in cls.NODE_FILTER_OPTIONS
        )
        # Add negation filter options (not:filter=)
        neg_filter_opts = " ".join(
            f"not:{opt}=" for opt in cls.NODE_FILTER_OPTIONS if opt != "ALL"
        )
        create_opts = " ".join(f"{opt}=" for opt in cls.NODE_CREATE_OPTIONS)
        states = " ".join(cls.NODE_STATES)
        create_states = " ".join(cls.NODE_CREATE_STATES)
        update_states = " ".join(cls.NODE_UPDATE_STATES)
        cpubind_values = " ".join(cls.NODE_CPUBIND_VALUES)

        script = f"""
_slurm_cli_nodes_autocomplete() {{
    local cmd="$1"
    local pos="$2"

    local cur="${{COMP_WORDS[COMP_CWORD]}}"
    local prev="${{COMP_WORDS[COMP_CWORD-1]}}"

    local cached_nodes="$(_slurm_cache_nodes)"
    local cached_partitions="$(_slurm_cache_partitions)"
    local show_options="{show_opts}"
    local update_options="{update_opts}"
    local filter_options="{filter_opts}"
    local neg_filter_options="{neg_filter_opts}"
    local create_options="{create_opts}"

    # Handle key=value completion
    if _slurm_parse_keyval "$cur" "$prev"; then
        case "$_key" in
            state)
                # Different states for create vs update
                if [[ "$cmd" == "create" ]]; then
                    _slurm_complete_value "{create_states}" "$_key" "$_val" "$cur"
                elif [[ "$cmd" == "update" ]]; then
                    _slurm_complete_value "{update_states}" "$_key" "$_val" "$cur"
                else
                    _slurm_complete_value "{states}" "$_key" "$_val" "$cur"
                fi
                ;;
            cpubind)
                _slurm_complete_value "{cpubind_values}" "$_key" "$_val" "$cur" ;;
            partition)
                _slurm_complete_value "$cached_partitions" "$_key" "$_val" "$cur" ;;
            name|nodename)
                _slurm_complete_value "$cached_nodes" "$_key" "$_val" "$cur" ;;
            user)
                # Node filter: show users for selecting nodes by user's jobs
                _slurm_complete_value "$(_slurm_cache_users)" "$_key" "$_val" "$cur" ;;
            reservation)
                # Node filter: show reservations for selecting nodes
                _slurm_complete_value "$(_slurm_cache_reservations)" "$_key" "$_val" "$cur" ;;
        esac
        [[ ${{#COMPREPLY[@]}} -gt 0 ]] && return
    fi

    # For show command: filter options, show options, then node names
    if [[ "$cmd" == "show" ]]; then
        _slurm_complete "$filter_options $neg_filter_options $show_options $cached_nodes" "$cur"
        return
    fi

    # For create command: show create options (name is positional)
    if [[ "$cmd" == "create" ]]; then
        _slurm_complete "$create_options" "$cur"
        return
    fi

    # For update command: filter options, update options, then node names
    if [[ "$cmd" == "update" ]]; then
        _slurm_complete "$filter_options $update_options $cached_nodes" "$cur"
        return
    fi

    # Default: show node names
    _slurm_complete "$cached_nodes" "$cur"
}}
"""  # noqa: E501
        return script

    @classmethod
    def get_profile_fields(cls) -> dict:
        """Return field names and descriptions for profile templates."""
        return {
            "name": "Node name",
            "state": "Node state",
            "cpus": "Number of CPUs",
            "real_memory": "Real memory (MB)",
            "tmp_disk": "Tmp disk space",
            "features": "Node features",
            "gres": "Generic resources",
            "partitions": "Partitions this node belongs to",
            "reason": "State reason (if down/drained)",
            "comment": "Node comment",
        }

    @classmethod
    def max_width(cls) -> int:
        """Get the maximum width of the console."""
        if cls._WIDTH is None:
            cls._WIDTH = console.width
        return cls._WIDTH

    @classmethod
    def create(cls, name: str, verbose: bool = False, **kwargs: Any) -> None:
        """Create a new node.

        Both NodeName and state are required.
        Only 'future' and 'cloud' states are allowed for node creation.
        Command format: scontrol create NodeName=NAME state=STATE [OPTIONS]
        """
        # State is required
        state = kwargs.get("state", "").lower()
        if not state:
            console.print("[red]Node creation requires state= parameter.[/red]")
            console.print(f"Allowed states: {', '.join(cls.NODE_CREATE_STATES)}")
            console.print("Usage: slurm-cli create nodes NODENAME state=future|cloud")
            return

        # Validate state value
        if state not in cls.NODE_CREATE_STATES:
            console.print(f"[red]Invalid state '{state}' for node creation.[/red]")
            console.print(f"Allowed states: {', '.join(cls.NODE_CREATE_STATES)}")
            return

        # Build scontrol command
        args = ["scontrol", "create", f"NodeName={name}"]
        for key, value in kwargs.items():
            if value is not None:
                args.append(f"{key}={value}")

        if verbose:
            console.print(f"[dim]Running: {' '.join(args)}[/dim]")

        try:
            result = subprocess.run(
                args,
                check=True,
                capture_output=True,
                text=True,
            )
            console.print(f"[green]Node '{name}' created successfully.[/green]")
            if result.stdout:
                console.print(result.stdout)
        except subprocess.CalledProcessError as e:
            console.print(f"[red]Failed to create node '{name}':[/red] {e.stderr or e}")

    @classmethod
    def update(
        cls,
        name: str,
        verbose: bool = False,
        dry_run: bool = False,
        **kwargs: Any,
    ) -> None:
        """Update a node.

        Command format: scontrol update NodeName=NAME [OPTIONS]

        Valid options:
            ActiveFeatures, AvailableFeatures, Comment, CpuBind, Extra,
            Gres, InstanceId, InstanceType, NodeAddr, NodeHostname,
            Reason, ResumeAfter, State, Weight

        Valid states: CANCEL_REBOOT, DOWN, DRAIN, FAIL, FUTURE, IDLE,
                      NoResp, RESUME, UNDRAIN
        Valid CpuBind: none, socket, ldom, core, thread, off
        """
        if not name:
            console.print("[red]Node name is required for update.[/red]")
            console.print("Usage: slurm-cli update nodes NODENAME KEY=VALUE...")
            return

        # Validate state if provided
        state = kwargs.get("state", "")
        if state and state.lower() not in cls.NODE_UPDATE_STATES:
            console.print(f"[red]Invalid state '{state}' for node update.[/red]")
            console.print(f"Valid states: {', '.join(cls.NODE_UPDATE_STATES)}")
            return

        # Validate cpubind if provided
        cpubind = kwargs.get("cpubind", "")
        if cpubind and cpubind.lower() not in cls.NODE_CPUBIND_VALUES:
            console.print(f"[red]Invalid cpubind '{cpubind}'.[/red]")
            console.print(f"Valid values: {', '.join(cls.NODE_CPUBIND_VALUES)}")
            return

        # Build scontrol command
        args = ["scontrol", "update", f"NodeName={name}"]
        for key, value in kwargs.items():
            if value is not None:
                args.append(f"{key}={value}")

        if dry_run:
            console.print(f"[yellow]DRY RUN:[/yellow] {' '.join(args)}")
            return

        if verbose:
            console.print(f"[dim]Running: {' '.join(args)}[/dim]")

        try:
            result = subprocess.run(
                args,
                check=True,
                capture_output=True,
                text=True,
            )
            console.print(f"[green]Node '{name}' updated successfully.[/green]")
            if result.stdout:
                console.print(result.stdout)
        except subprocess.CalledProcessError as e:
            console.print(f"[red]Failed to update node '{name}':[/red] {e.stderr or e}")

    @classmethod
    def delete(cls, name: str, verbose: bool = False) -> None:
        """Delete a node.

        Command format: scontrol delete nodename=NODES
        """
        if not name:
            console.print("[red]Node name is required for deletion.[/red]")
            console.print("Usage: slurm-cli delete nodes NODENAME")
            return

        args = ["scontrol", "delete", f"nodename={name}"]

        if verbose:
            console.print(f"[dim]Running: {' '.join(args)}[/dim]")

        try:
            result = subprocess.run(
                args,
                check=True,
                capture_output=True,
                text=True,
            )
            console.print(f"[green]Node '{name}' deleted successfully.[/green]")
            if result.stdout:
                console.print(result.stdout)
        except subprocess.CalledProcessError as e:
            console.print(f"[red]Failed to delete node '{name}':[/red] {e.stderr or e}")

    @classmethod
    def show(
        cls,
        name: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        style: str = "pretty",
        verbose: bool = False,
        force_cache_update: bool = False,
        delimiter: str = ";",
        zebra: bool = False,
        profile: str = "default",
        profile_str: Optional[str] = None,
    ) -> None:
        """Show node information."""
        # Get profile configuration
        (
            columns_cfg,
            styles_cfg,
            template_cfg,
            sort_field,
            sort_asc,
        ) = get_profile_config(profile, "nodes", profile_str)
        if not data:
            console.print("[red]No data available.[/red]")
            return

        # Convert dict to sorted list if sorting is needed
        if sort_field and data and not name:
            items = [{"name": k, **v} for k, v in data.items()]
            items = sort_data(items, sort_field, sort_asc)
            data = {item["name"]: item for item in items}

        try:
            if style == "json":
                if name:
                    console.print_json(json.dumps(data[name], indent=4))
                else:
                    console.print_json(json.dumps(data, indent=4))
            elif style == "csv":
                cls.show_csv(
                    name, data, delimiter, verbose, columns_cfg  # type: ignore
                )
            elif template_cfg and style == "pretty":
                # Use template-based output (e.g., oneline profile)
                nodes_to_show = {name: data[name]} if name and name in data else data
                for node_name, node_data in sorted(nodes_to_show.items()):
                    # Prepare data with name included
                    prepared = {"name": node_name, **node_data}
                    output = format_with_template(
                        template_cfg, prepared, resource="nodes"
                    )
                    console.print(output)
            elif columns_cfg and columns_cfg != "*" and style == "pretty":
                # Use column-based table output (e.g., compact, minimal)
                cls.show_columns(
                    name, data, columns_cfg, styles_cfg, zebra  # type: ignore
                )
            else:  # Default pretty style
                if name:
                    cls.show_one_pretty(name, data[name], verbose)
                else:
                    for node in data.keys():
                        cls.show_one_pretty(node, data[node], verbose)
        except subprocess.CalledProcessError as e:
            console.print(f"[red]Failed to show node(s):[/red] {e.stderr or e}")

    @classmethod
    def show_columns(
        cls,
        name: Optional[str] = None,
        nodes: Optional[Dict[str, Any]] = None,
        columns: Optional[List[str]] = None,
        styles: Optional[Dict[str, str]] = None,
        zebra: bool = False,
    ) -> None:
        """Show nodes in a column-based table."""
        if not nodes:
            console.print("[red]No nodes found.[/red]")
            return

        nodes_to_show = {name: nodes[name]} if name and name in nodes else nodes

        # Create table
        row_styles = ["", "dim"] if zebra else None
        table = Table(
            title="Nodes",
            box=SIMPLE_HEAVY,
            pad_edge=False,
            row_styles=row_styles,
        )

        # Use default columns if not specified
        if not columns:
            columns = cls.DEFAULT_COLUMNS

        # Merge with default styles
        merged_styles = dict(cls.DEFAULT_STYLES)
        if styles:
            merged_styles.update(styles)

        # Add columns to table
        for col in columns:
            style = merged_styles.get(col.lower(), "white")
            table.add_column(col.title(), style=style)

        # Add rows
        for node_name in sorted(nodes_to_show.keys()):
            node_data = nodes_to_show[node_name]
            row = []
            for col in columns:
                col_lower = col.lower()
                if col_lower == "name":
                    row.append(node_name)
                elif col_lower == "state":
                    # State can be a list
                    state = node_data.get("state", [])
                    if isinstance(state, list):
                        row.append(",".join(state))
                    else:
                        row.append(str(state))
                else:
                    value = node_data.get(col_lower, node_data.get(col, ""))
                    if isinstance(value, list):
                        row.append(",".join(str(v) for v in value))
                    else:
                        row.append(str(value) if value else "")
            table.add_row(*row)

        console.print(table)

    @classmethod
    def show_csv(
        cls,
        name: Optional[str] = None,
        nodes: Optional[Dict[str, Any]] = None,
        delimiter: str = ";",
        verbose: bool = False,
        columns: Optional[List[str]] = None,
    ) -> None:
        """Show node information in CSV format."""
        if not nodes:
            console.print("[red]No nodes found.[/red]")
            return

        # Helper to flatten complex values
        def flatten_value(value):
            """Convert complex values to strings."""
            if isinstance(value, dict):
                # Handle set/number structures
                if "set" in value and "number" in value:
                    return str(value.get("number", "")) if value.get("set") else ""
                # Handle other dicts as JSON
                return json.dumps(value)
            elif isinstance(value, list):
                # Join list items
                return ",".join(str(v) for v in value)
            else:
                return str(value) if value is not None else ""

        # Determine nodes to show
        nodes_to_show = {name: nodes[name]} if name and name in nodes else nodes

        # If specific columns specified in profile, use those
        if columns and columns != "*":
            headers = ["NodeName"] + [c for c in columns if c != "name"]
            print(delimiter.join(headers))
            for node_name in sorted(nodes_to_show.keys()):
                node_data = nodes_to_show[node_name]
                row = [node_name]
                for col in columns:
                    if col.lower() == "name":
                        continue
                    value = node_data.get(col.lower(), node_data.get(col, ""))
                    row.append(flatten_value(value))
                print(delimiter.join(row))
            return

        # Find all unique fields across all nodes
        all_fields = set()
        for node_data in nodes_to_show.values():
            all_fields.update(node_data.keys())

        # Priority fields (most important ones first)
        priority_fields = [
            "state",
            "cpus",
            "alloc_cpus",
            "real_memory",
            "alloc_memory",
            "gres",
            "gres_used",
            "tres",
            "tres_used",
        ]

        # Fields to skip in non-verbose mode
        skip_fields = set()
        if not verbose:
            skip_fields = {
                "cpu_load",
                "architecture",
                "boards",
                "boot_time",
                "cluster_name",
                "cores",
                "specialized_cores",
                "cpu_binding",
                "free_mem",
                "effective_cpus",
                "specialized_cpus",
                "energy",
                "external_sensors",
                "power",
                "gres_drained",
                "next_state_after_reboot",
                "address",
                "operating_system",
                "owner",
                "port",
                "reason_changed_at",
                "resume_after",
                "specialized_memory",
                "last_busy",
                "alloc_idle_cpus",
                "tres_weighted",
                "slurmd_start_time",
                "sockets",
                "threads",
                "temporary_disk",
                "weight",
                "version",
            }

        # Filter fields based on verbose mode
        if not verbose:
            all_fields = all_fields - skip_fields

        # Sort fields: priority first, then alphabetically
        sorted_fields = [f for f in priority_fields if f in all_fields] + sorted(
            [f for f in all_fields if f not in priority_fields]
        )

        # Print CSV header
        headers = ["NodeName"] + sorted_fields
        print(delimiter.join(headers))

        # Print data rows
        for node_name in sorted(nodes_to_show.keys()):
            node_data = nodes_to_show[node_name]
            row = [node_name] + [
                flatten_value(node_data.get(field, "")) for field in sorted_fields
            ]
            print(delimiter.join(row))

    @classmethod
    def show_one_pretty(
        cls,
        name: str,
        data: dict,
        verbose: bool = False,
    ) -> None:
        """Show one node information."""
        console.print("=============================================")
        # console.print_json(json.dumps(data, indent=4))
        console.print(
            f"[label]Node[/]: [object]{escape(name)}[/] " f"{','.join(data['state'])}"
        )
        console.print(
            f"[label]CPUs[/]: [b]{data['cpus']}/"
            f"{data['alloc_cpus']}[/] "
            f"[label]Mem[/]: [b]{data['real_memory']}/"
            f"{data['alloc_memory']}[/]"
        )
        console.print(
            f"[label]GRES[/]: [b]{data['gres']} "
            f"[label]Used[/]: {data['gres_used']}[/]"
        )
        console.print(
            f"[label]TRES[/]: [b]{data['tres']} "
            f"[label]Used[/]: {data['tres_used']}[/]"
        )
        for k in [
            "state",
            "cpus",
            "alloc_cpus",
            "real_memory",
            "alloc_memory",
            "gres",
            "gres_used",
            "tres",
            "tres_used",
        ]:
            data.pop(k)
        if not verbose:
            for k in [
                "cpu_load",
                "architecture",
                "boards",
                "boot_time",
                "cluster_name",
                "cores",
                "specialized_cores",
                "cpu_binding",
                "free_mem",
                "effective_cpus",
                "specialized_cpus",
                "energy",
                "external_sensors",
                "power",
                "gres_drained",
                "next_state_after_reboot",
                "address",
                "operating_system",
                "owner",
                "port",
                "reason_changed_at",
                "resume_after",
                "specialized_memory",
                "last_busy",
                "alloc_idle_cpus",
                "tres_weighted",
                "slurmd_start_time",
                "sockets",
                "threads",
                "temporary_disk",
                "weight",
                "version",
            ]:
                data.pop(k)
            cls.print_dict_pretty(data)
