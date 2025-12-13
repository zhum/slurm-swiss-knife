"""Utilities for managing Slurm events."""

import json
import os
import re
import subprocess
from typing import Any, Dict, List, Optional

from rich.box import SIMPLE_HEAVY
from rich.table import Table

from .base_resource import BaseSlurmResource
from .profiles import get_profile_config
from .utils import console

# Cache file path
CACHE_DIR = "/tmp/"
EVENTS_CACHE_FILE = f"{CACHE_DIR}slurm_cli_events.txt"

# Event filter options
EVENT_FILTER_OPTIONS: List[str] = [
    "Clusters",
    "CondFlags",
    "End",
    "Events",
    "MaxCPUs",
    "MinCPUs",
    "MaxNodes",
    "MinNodes",
    "Nodes",
    "Reason",
    "Start",
    "States",
    "User",
]

# Column mapping from sacctmgr output to our field names
COLUMN_MAPPING = {
    "Cluster": "cluster",
    "Cluster Nodes": "cluster_nodes",
    "Duration": "duration",
    "TimeStart": "start",
    "TimeEnd": "end",
    "Event": "event",
    "EventRaw": "event_raw",
    "NodeName": "node",
    "State": "state",
    "StateRaw": "state_raw",
    "TRES": "tres",
    "User": "user",
    "Reason": "reason",
}


class Event(BaseSlurmResource):
    """Slurm event resource handler."""

    def __init__(self, **kwargs: Any):
        self.kwargs = kwargs

    @classmethod
    def get_profile_fields(cls) -> dict:
        """Return field names and descriptions for profile templates."""
        return {
            "cluster": "Cluster name",
            "cluster_nodes": "Nodes in cluster at time of event",
            "duration": "Event duration",
            "start": "Event start time",
            "end": "Event end time",
            "event": "Event type (Cluster or Node)",
            "event_raw": "Raw event code",
            "node": "Node name affected",
            "state": "Node state",
            "state_raw": "Raw state code",
            "tres": "Trackable resources",
            "user": "User who triggered event",
            "reason": "Event reason",
        }

    # All available columns
    ALL_COLUMNS = [
        "cluster",
        "cluster_nodes",
        "duration",
        "start",
        "end",
        "event",
        "event_raw",
        "node",
        "state",
        "state_raw",
        "tres",
        "user",
        "reason",
    ]

    # Default column configuration for events
    DEFAULT_COLUMNS = [
        "node",
        "state",
        "start",
        "end",
        "duration",
        "user",
        "reason",
    ]
    DEFAULT_STYLES = {
        "cluster": "cyan",
        "cluster_nodes": "dim",
        "duration": "yellow",
        "start": "green",
        "end": "green",
        "event": "magenta",
        "event_raw": "dim",
        "node": "cyan bold",
        "state": "yellow",
        "state_raw": "dim",
        "tres": "dim",
        "user": "blue",
        "reason": "white",
    }

    @classmethod
    def _parse_events(cls, data: str) -> List[Dict[str, Any]]:
        """Parse pipe-delimited event data into list of dicts."""
        events = []
        lines = data.strip().split("\n")

        if not lines:
            return events

        # First line is header
        header = lines[0].split("|")
        # Map header names to our field names
        field_names = []
        for col in header:
            col = col.strip()
            field_names.append(COLUMN_MAPPING.get(col, col.lower()))

        # Parse data lines
        for line in lines[1:]:
            if not line.strip():
                continue
            values = line.split("|")
            event = {}
            for i, value in enumerate(values):
                if i < len(field_names):
                    event[field_names[i]] = value.strip()
            if event:
                events.append(event)

        return events

    @classmethod
    def _extract_cpus(cls, tres: str) -> int:
        """Extract CPU count from TRES string."""
        if not tres:
            return 0
        match = re.search(r"cpu=(\d+)", tres)
        return int(match.group(1)) if match else 0

    @classmethod
    def _extract_nodes(cls, tres: str) -> int:
        """Extract node count from TRES string."""
        if not tres:
            return 0
        match = re.search(r"node=(\d+)", tres)
        return int(match.group(1)) if match else 0

    @classmethod
    def _apply_filters(
        cls,
        events: List[Dict[str, Any]],
        filters: Dict[str, str],
    ) -> List[Dict[str, Any]]:
        """Apply filters to event list."""
        result = events

        for key, value in filters.items():
            key_lower = key.lower()

            if key_lower == "clusters":
                result = [
                    e
                    for e in result
                    if e.get("cluster", "").lower() == value.lower()
                ]
            elif key_lower == "events":
                result = [
                    e
                    for e in result
                    if e.get("event", "").lower() == value.lower()
                ]
            elif key_lower == "nodes":
                result = [
                    e
                    for e in result
                    if value.lower() in e.get("node", "").lower()
                ]
            elif key_lower == "states":
                result = [
                    e
                    for e in result
                    if value.lower() in e.get("state", "").lower()
                ]
            elif key_lower == "user":
                result = [
                    e
                    for e in result
                    if value.lower() in e.get("user", "").lower()
                ]
            elif key_lower == "reason":
                result = [
                    e
                    for e in result
                    if value.lower() in e.get("reason", "").lower()
                ]
            elif key_lower == "mincpus":
                min_cpus = int(value)
                result = [
                    e
                    for e in result
                    if cls._extract_cpus(e.get("tres", "")) >= min_cpus
                ]
            elif key_lower == "maxcpus":
                max_cpus = int(value)
                result = [
                    e
                    for e in result
                    if cls._extract_cpus(e.get("tres", "")) <= max_cpus
                ]
            elif key_lower == "minnodes":
                min_nodes = int(value)
                result = [
                    e
                    for e in result
                    if cls._extract_nodes(e.get("tres", ""))
                    >= min_nodes
                ]
            elif key_lower == "maxnodes":
                max_nodes = int(value)
                result = [
                    e
                    for e in result
                    if cls._extract_nodes(e.get("tres", ""))
                    <= max_nodes
                ]
            # Start and End filters would need date parsing - simplified here
            elif key_lower == "start":
                result = [
                    e for e in result if value in e.get("start", "")
                ]
            elif key_lower == "end":
                result = [
                    e for e in result if value in e.get("end", "")
                ]

        return result

    @classmethod
    def _format_value(
        cls, event: Dict[str, Any], column: str, truncate: bool = True
    ) -> str:
        """Format a value for display.

        Args:
            event: Event dictionary
            column: Column name
            truncate: Whether to truncate long values (for pretty output)
        """
        value = event.get(column, "")
        if value is None or value == "":
            return "-"
        # Truncate long values only for pretty output
        if truncate:
            if column == "reason" and len(str(value)) > 60:
                return str(value)[:57] + "..."
            if column == "cluster_nodes" and len(str(value)) > 40:
                return str(value)[:37] + "..."
            if column == "tres" and len(str(value)) > 50:
                return str(value)[:47] + "..."
        return str(value)

    @classmethod
    def _get_sacctmgr_command(
        cls, filters: Dict[str, str] = None
    ) -> List[str]:
        """Build sacctmgr command with filters."""
        cmd = [
            "sacctmgr",
            "list",
            "event",
            "format=Cluster,ClusterNodes,Duration,Start,End,"
            "Event,EventRaw,NodeName,State,StateRaw,TRES,User,Reason",
            "-p",
        ]

        if filters:
            for key, value in filters.items():
                # These are sacctmgr-level filters
                if key.lower() in [
                    "clusters",
                    "condflags",
                    "end",
                    "events",
                    "nodes",
                    "reason",
                    "start",
                    "states",
                    "user",
                ]:
                    cmd.append(f"{key}={value}")

        return cmd

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
        """Show event information.

        Args:
            field: Optional filter (e.g., Nodes=h100-pool0-0290)
            style: Output style ("pretty", "json", or "csv")
            force_cache_update: Whether to force cache update
            delimiter: Delimiter for CSV output (default: ";")
            zebra: Use zebra striping for table rows
            profile: Profile name to use for output formatting
            profile_str: Inline profile string (overrides profile)
        """
        # Get profile configuration
        columns, styles, template = get_profile_config(
            profile, "events", profile_str
        )

        # Use default columns if not specified, or all columns if "*"
        if columns == "*":
            columns = cls.ALL_COLUMNS
        elif columns is None:
            columns = cls.DEFAULT_COLUMNS

        # Merge with default styles
        merged_styles = dict(cls.DEFAULT_STYLES)
        if styles:
            merged_styles.update(styles)

        # Parse filters from field argument
        filters: Dict[str, str] = {}
        if field:
            # Parse multiple filters like "Nodes=x States=DRAIN"
            parts = field.split()
            for part in parts:
                if "=" in part:
                    key, value = part.split("=", 1)
                    filters[key] = value

        # Check if CondFlags=Open - if so, always run live
        use_cache = True
        if filters.get("CondFlags", "").lower() == "open":
            use_cache = False

        try:
            data = ""

            # Try to use cache if allowed
            if use_cache and not force_cache_update:
                if os.path.exists(EVENTS_CACHE_FILE):
                    with open(EVENTS_CACHE_FILE, "r") as f:
                        data = f.read()

            # If no cache or forced update, run command
            if not data or force_cache_update or not use_cache:
                # Build command with sacctmgr-level filters
                sacctmgr_filters = {
                    k: v
                    for k, v in filters.items()
                    if k.lower()
                    in [
                        "clusters",
                        "condflags",
                        "end",
                        "events",
                        "nodes",
                        "reason",
                        "start",
                        "states",
                        "user",
                    ]
                }
                cmd = cls._get_sacctmgr_command(sacctmgr_filters)

                result = subprocess.run(
                    cmd,
                    check=True,
                    capture_output=True,
                    text=True,
                )
                data = result.stdout

                # Save to cache only if not using CondFlags=Open
                if use_cache and data:
                    with open(EVENTS_CACHE_FILE, "w") as f:
                        f.write(data)

            if not data:
                console.print("[yellow]No events found.[/yellow]")
                return

            # Parse events
            events = cls._parse_events(data)

            if not events:
                console.print("[yellow]No events found.[/yellow]")
                return

            # Apply client-side filters (all filters that need post-processing)
            # This handles cases where sacctmgr mock doesn't filter
            if filters:
                events = cls._apply_filters(events, filters)

            if not events:
                console.print(
                    f"[yellow]No events matching filters found.[/yellow]"
                )
                return

            # Output based on style
            if style == "json":
                console.print_json(json.dumps(events, indent=2))
            elif style == "csv":
                # CSV header
                print(delimiter.join(columns))
                for event in events:
                    row = [
                        cls._format_value(event, col, truncate=False)
                        for col in columns
                    ]
                    print(delimiter.join(row))
            else:
                # Pretty table output
                table = Table(
                    title="Slurm Events",
                    box=SIMPLE_HEAVY,
                    show_header=True,
                    header_style="bold",
                )

                # Add columns
                for col in columns:
                    col_style = merged_styles.get(col, "white")
                    table.add_column(col.title(), style=col_style)

                # Add rows
                for i, event in enumerate(events):
                    row_style = None
                    if zebra and i % 2 == 1:
                        row_style = "on grey15"
                    row = [
                        cls._format_value(event, col) for col in columns
                    ]
                    table.add_row(*row, style=row_style)

                console.print(table)

        except subprocess.CalledProcessError as e:
            console.print(
                f"[red]Failed to show events:[/red] {e.stderr or e}"
            )

    @classmethod
    def create(cls, *args, **kwargs) -> None:
        """Events cannot be created."""
        console.print("[red]Events cannot be created manually.[/red]")

    @classmethod
    def update(cls, *args, **kwargs) -> None:
        """Events cannot be updated."""
        console.print("[red]Events cannot be updated manually.[/red]")

    @classmethod
    def delete(cls, *args, **kwargs) -> None:
        """Events cannot be deleted."""
        console.print("[red]Events cannot be deleted manually.[/red]")

    @classmethod
    def generate_autocomplete_options(cls) -> str:
        """Generate bash autocomplete script for event options."""
        filter_opts = " ".join(
            [f"{opt}=" for opt in EVENT_FILTER_OPTIONS]
        )

        script = f"""
_slurm_cli_events_autocomplete() {{
    local cmd="$1"
    local pos="$2"

    name="${{COMP_WORDS[$pos]}}"
    cur="${{COMP_WORDS[COMP_CWORD]}}"
    prev="${{COMP_WORDS[COMP_CWORD-1]}}"

    # Event filter options
    local filter_options="{filter_opts}"

    # Check if we're completing a value after key=
    local key=""
    local val_prefix=""

    if [[ $cur == *=* ]]; then
        key=${{cur%%=*}}
        val_prefix=${{cur#*=}}
    elif [[ $prev == "=" ]]; then
        key="${{COMP_WORDS[COMP_CWORD-2]}}"
        val_prefix="$cur"
    elif [[ $prev == *= ]]; then
        key=${{prev%%=}}
        val_prefix="$cur"
    fi

    if [ -n "$key" ]; then
        key=${{key,,}}
        case "$key" in
            condflags)
                COMPREPLY=($(compgen -W "Open" -- "$val_prefix"))
                ;;
            states)
                COMPREPLY=($(compgen -W "DOWN DRAIN FAIL FUTR IDLE MAINT POWER REBOOT" -- "$val_prefix"))
                ;;
            events)
                COMPREPLY=($(compgen -W "Cluster Node" -- "$val_prefix"))
                ;;
        esac
        if [ ${{#COMPREPLY[@]}} -gt 0 ]; then
            return
        fi
    fi

    # Default: show filter options
    case "$cmd" in
        show)
            if [[ $cur == '' ]]; then
                COMPREPLY=($(compgen -W "$filter_options"))
            else
                COMPREPLY=($(compgen -W "$filter_options" -- "$cur"))
            fi
            ;;
    esac
}}
"""  # noqa: E501
        return script
