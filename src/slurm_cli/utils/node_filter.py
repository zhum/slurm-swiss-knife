"""Node filter utilities for selecting nodes by various criteria.

Supports filtering nodes by:
- partition=<name> - nodes from a specific partition
- state=<state> - nodes with a specific state
- user=<username> - nodes running jobs by a specific user
- reservation=<name> - nodes in a specific reservation

Prefix with 'not:' to exclude nodes matching the filter:
- not:partition=<name> - exclude nodes from a specific partition
- not:state=<state> - exclude nodes with a specific state
- not:user=<username> - exclude nodes running jobs by a specific user
- not:reservation=<name> - exclude nodes in a specific reservation

Filter syntax can be used anywhere node names are expected, e.g.:
- slurm-cli update reservations test nodes=partition=cpu
- slurm-cli update nodes state=drain partition=gpu
- slurm-cli drain partition=gpu not:reservation=maint
"""

import json
import re
import subprocess
from typing import List, Optional, Set, Tuple

from .utils import console

# Filter prefixes that indicate a node filter expression
NODE_FILTER_PREFIXES = [
    "partition=",
    "state=",
    "user=",
    "reservation=",
]

# Available node states for completion
NODE_STATES = [
    "idle",
    "alloc",
    "drain",
    "down",
    "mixed",
    "comp",
]


def is_node_filter(value: str) -> bool:
    """Check if a value is a node filter expression or special keyword.

    Recognizes both positive filters (partition=gpu) and negative/exclusion
    filters (not:partition=gpu). Uses 'not:' prefix to avoid conflicts with
    CLI option parsing (-) and bash tilde expansion (~).
    """
    if not value:
        return False
    value_lower = value.lower()
    # Check for ALL keyword
    if value_lower == "all":
        return True
    # Handle negative filter prefix (not:)
    if value_lower.startswith("not:"):
        value_lower = value_lower[4:]
    return any(value_lower.startswith(p) for p in NODE_FILTER_PREFIXES)


def resolve_node_filter(
    filter_expr: str, verbose: bool = False
) -> Optional[str]:
    """Resolve a node filter expression to a comma-separated list of nodes.

    Args:
        filter_expr: Filter expression like "partition=cpu", "state=idle",
                     or "ALL" for all nodes
        verbose: Print debug information

    Returns:
        Comma-separated list of node names, or None if no nodes match
    """
    if not filter_expr:
        return None

    filter_lower = filter_expr.lower()

    # Handle ALL keyword - return "ALL" as-is (Slurm understands it)
    if filter_lower == "all":
        if verbose:
            console.print("[dim]Using ALL nodes[/dim]")
        return "ALL"

    # Parse filter type and value
    if filter_lower.startswith("partition="):
        return _get_nodes_by_partition(filter_expr[10:], verbose)
    elif filter_lower.startswith("state="):
        return _get_nodes_by_state(filter_expr[6:], verbose)
    elif filter_lower.startswith("user="):
        return _get_nodes_by_user(filter_expr[5:], verbose)
    elif filter_lower.startswith("reservation="):
        return _get_nodes_by_reservation(filter_expr[12:], verbose)
    else:
        # Not a filter, return as-is
        return filter_expr


def _get_nodes_by_partition(
    partition: str, verbose: bool = False
) -> str:
    """Get nodes belonging to a specific partition."""
    try:
        result = subprocess.run(
            ["scontrol", "show", "partition", partition, "--json"],
            capture_output=True,
            text=True,
            check=True,
        )
        data = json.loads(result.stdout)
        partitions = data.get("partitions", [])
        if not partitions:
            if verbose:
                console.print(
                    f"[yellow]No partition '{partition}' found[/yellow]"
                )
            return ""

        # Get nodes from partition
        nodes = partitions[0].get("nodes", {})
        if isinstance(nodes, dict):
            # Handle structured node format
            node_list = nodes.get("nodes", "")
        else:
            node_list = nodes

        if verbose:
            console.print(
                f"[dim]Nodes from partition '{partition}': {node_list}[/dim]"
            )
        return node_list
    except subprocess.CalledProcessError as e:
        if verbose:
            console.print(
                f"[red]Failed to get nodes from partition: {e.stderr}[/red]"
            )
        return ""
    except json.JSONDecodeError:
        # Try non-JSON fallback
        return _get_nodes_by_partition_text(partition, verbose)


def _get_nodes_by_partition_text(
    partition: str, verbose: bool = False
) -> str:
    """Get nodes from partition using text output (fallback)."""
    try:
        result = subprocess.run(
            ["sinfo", "-p", partition, "-h", "-o", "%N"],
            capture_output=True,
            text=True,
            check=True,
        )
        nodes = result.stdout.strip()
        if verbose:
            console.print(
                f"[dim]Nodes from partition '{partition}': {nodes}[/dim]"
            )
        return nodes
    except subprocess.CalledProcessError:
        return ""


def _get_nodes_by_state(state: str, verbose: bool = False) -> str:
    """Get nodes with a specific state."""
    try:
        # Use scontrol with JSON for reliable parsing
        result = subprocess.run(
            ["scontrol", "show", "nodes", "--json"],
            capture_output=True,
            text=True,
            check=True,
        )
        data = json.loads(result.stdout)
        state_lower = state.lower()
        node_set = set()
        for node in data.get("nodes", []):
            node_state = node.get("state", [])
            # state can be a list like ["IDLE"] or ["ALLOCATED", "DRAIN"]
            if isinstance(node_state, list):
                state_strs = [s.lower() for s in node_state]
            else:
                state_strs = [str(node_state).lower()]
            # Match if any state component matches
            for s in state_strs:
                if state_lower in s or s.startswith(state_lower):
                    node_set.add(node.get("name", ""))
                    break
        nodes = ",".join(sorted(node_set))
        if verbose:
            console.print(
                f"[dim]Nodes with state '{state}': {nodes}[/dim]"
            )
        return nodes
    except subprocess.CalledProcessError as e:
        if verbose:
            console.print(
                f"[red]Failed to get nodes by state: {e.stderr}[/red]"
            )
        return ""
    except json.JSONDecodeError:
        return _get_nodes_by_state_text(state, verbose)


def _get_nodes_by_state_text(state: str, verbose: bool = False) -> str:
    """Get nodes by state using text output (fallback)."""
    try:
        result = subprocess.run(
            ["sinfo", "-t", state, "-h", "-N", "-o", "%N"],
            capture_output=True,
            text=True,
            check=True,
        )
        node_set = set()
        for line in result.stdout.strip().split("\n"):
            if line.strip():
                node_set.add(line.strip())
        nodes = ",".join(sorted(node_set))
        if verbose:
            console.print(
                f"[dim]Nodes with state '{state}': {nodes}[/dim]"
            )
        return nodes
    except subprocess.CalledProcessError:
        return ""


def _get_nodes_by_user(user: str, verbose: bool = False) -> str:
    """Get nodes running jobs by a specific user."""
    try:
        # Use JSON output for reliable parsing
        result = subprocess.run(
            ["squeue", "-u", user, "--json"],
            capture_output=True,
            text=True,
            check=True,
        )
        data = json.loads(result.stdout)
        # Collect unique nodes from all jobs
        node_set = set()
        for job in data.get("jobs", []):
            nodes = job.get("nodes", "")
            if isinstance(nodes, str) and nodes:
                # Handle comma-separated nodes or ranges
                for node in nodes.split(","):
                    if node.strip():
                        node_set.add(node.strip())

        nodes = ",".join(sorted(node_set))
        if verbose:
            console.print(
                f"[dim]Nodes used by user '{user}': {nodes}[/dim]"
            )
        return nodes
    except subprocess.CalledProcessError as e:
        if verbose:
            console.print(
                f"[red]Failed to get nodes by user: {e.stderr}[/red]"
            )
        return ""
    except json.JSONDecodeError:
        # Fallback to text parsing
        return _get_nodes_by_user_text(user, verbose)


def _get_nodes_by_user_text(user: str, verbose: bool = False) -> str:
    """Get nodes by user using text output (fallback)."""
    try:
        result = subprocess.run(
            ["squeue", "-u", user, "-h", "-o", "%N"],
            capture_output=True,
            text=True,
            check=True,
        )
        node_set = set()
        for line in result.stdout.strip().split("\n"):
            if line.strip():
                node_set.add(line.strip())

        nodes = ",".join(sorted(node_set))
        if verbose:
            console.print(
                f"[dim]Nodes used by user '{user}': {nodes}[/dim]"
            )
        return nodes
    except subprocess.CalledProcessError:
        return ""


def _get_nodes_by_reservation(
    reservation: str, verbose: bool = False
) -> str:
    """Get nodes in a specific reservation."""
    try:
        result = subprocess.run(
            ["scontrol", "show", "reservation", reservation, "--json"],
            capture_output=True,
            text=True,
            check=True,
        )
        data = json.loads(result.stdout)
        reservations = data.get("reservations", [])
        if not reservations:
            if verbose:
                console.print(
                    f"[yellow]No reservation '{reservation}' found[/yellow]"
                )
            return ""

        nodes = reservations[0].get("node_list", "")
        if verbose:
            console.print(
                f"[dim]Nodes in reservation '{reservation}': {nodes}[/dim]"
            )
        return nodes
    except subprocess.CalledProcessError as e:
        if verbose:
            console.print(
                f"[red]Failed to get reservation nodes: {e.stderr}[/red]"
            )
        return ""
    except json.JSONDecodeError:
        return _get_nodes_by_reservation_text(reservation, verbose)


def _get_nodes_by_reservation_text(
    reservation: str, verbose: bool = False
) -> str:
    """Get nodes from reservation using text output (fallback)."""
    try:
        result = subprocess.run(
            ["scontrol", "show", "reservation", reservation],
            capture_output=True,
            text=True,
            check=True,
        )
        # Parse Nodes= from output
        for line in result.stdout.split("\n"):
            if "Nodes=" in line:
                parts = line.split()
                for part in parts:
                    if part.startswith("Nodes="):
                        nodes = part[6:]
                        if verbose:
                            console.print(
                                f"[dim]Nodes in reservation "
                                f"'{reservation}': {nodes}[/dim]"
                            )
                        return nodes
        return ""
    except subprocess.CalledProcessError:
        return ""


def resolve_nodes_value(value: str, verbose: bool = False) -> str:
    """Resolve a nodes value, handling both direct names and filters.

    Args:
        value: Node specification (names, range, or filter expression)
        verbose: Print debug information

    Returns:
        Resolved node specification (names or range)
    """
    if is_node_filter(value):
        resolved = resolve_node_filter(value, verbose)
        if not resolved:
            console.print(
                f"[yellow]Warning: No nodes matched filter '{value}'[/yellow]"
            )
            return ""
        return resolved
    return value


def _get_all_nodes(verbose: bool = False) -> Set[str]:
    """Get all nodes in the cluster."""
    try:
        result = subprocess.run(
            ["scontrol", "show", "nodes", "--json"],
            capture_output=True,
            text=True,
            check=True,
        )
        data = json.loads(result.stdout)
        nodes = {node.get("name", "") for node in data.get("nodes", [])}
        nodes.discard("")
        return nodes
    except (subprocess.CalledProcessError, json.JSONDecodeError):
        return set()


# Expand Slurm-style node list with ranges
def _expand_range(expr: str) -> Set[str]:
    """Expand a Slurm range expression like [001-003,005]
    to a list of strings.

    Args:
        expr: Slurm range expression like "001-003,005"

    Returns:
        Set of node names
    """
    result = set()
    # e.g., expr = "001-003,005"
    for part in expr.split(","):
        part = part.strip()
        if "-" in part:
            start, end = part.split("-", 1)
            # Keep the original width for leading zeros
            width = max(len(start), len(end))
            try:
                for i in range(int(start), int(end) + 1):
                    result.add(str(i).zfill(width))
            except ValueError:
                result.add(part)  # If badly formatted, keep as is
        elif part:
            result.add(part)
    return result


def _split_hostlist(node_str: str) -> List[str]:
    """Split a hostlist by commas, respecting brackets.

    E.g., "node[1-3,5],foo[2-4]" -> ["node[1-3,5]", "foo[2-4]"]
    """
    segments = []
    current = []
    depth = 0
    for char in node_str:
        if char == "[":
            depth += 1
            current.append(char)
        elif char == "]":
            depth -= 1
            current.append(char)
        elif char == "," and depth == 0:
            segment = "".join(current).strip()
            if segment:
                segments.append(segment)
            current = []
        else:
            current.append(char)
    # Don't forget the last segment
    segment = "".join(current).strip()
    if segment:
        segments.append(segment)
    return segments


def _expand_node_list(node_str: str) -> Set[str]:
    """Expand a comma-separated node list or range to a set of nodes.

    Handles Slurm hostlist format like:
    - "node[10-14,19],node[20,22,25-27]"
    - "gpu-node[001-004],cpu-node[1-3]"
    """
    if not node_str:
        return set()

    # Simple case: no brackets or commas, just return as-is
    if "[" not in node_str and "," not in node_str:
        return {node_str}

    # Parse hostlist like "node[001-004,007],foo1,foo[2-3]"
    node_names = set()
    pattern = re.compile(r"^([^\[]+)\[(.+)\]$")
    # ^ matches "prefix[ranges]"

    for segment in _split_hostlist(node_str):
        segment = segment.strip()
        if not segment:
            continue
        m = pattern.match(segment)
        if m:
            prefix = m.group(1)
            ranges = m.group(2)
            for suffix in _expand_range(ranges):
                node_names.add(f"{prefix}{suffix}")
        else:
            # No brackets, just a plain node name
            node_names.add(segment)

    return node_names


def resolve_node_filters(
    args: List[str], verbose: bool = False
) -> Tuple[Set[str], List[str]]:
    """Resolve multiple node filters including exclusions.

    Handles:
    - Direct node names/ranges
    - Positive filters (partition=gpu, state=idle, etc.)
    - Negative filters (-partition=gpu, -state=drain, etc.)

    Args:
        args: List of node specs and filters
        verbose: Print debug information

    Returns:
        Tuple of (resolved node set, list of unrecognized args)
    """
    include_nodes: Set[str] = set()
    exclude_nodes: Set[str] = set()
    other_args: List[str] = []
    has_include_filter = False

    for arg in args:
        if not arg:
            continue

        # Check for negative/exclusion filter (not: prefix)
        if arg.lower().startswith("not:") and is_node_filter(arg):
            # Negative filter: not:partition=gpu, not:state=drain, etc.
            filter_expr = arg[4:]  # Remove leading 'not:'
            resolved = resolve_node_filter(filter_expr, verbose)
            if resolved and resolved != "ALL":
                exclude_nodes.update(_expand_node_list(resolved))
                if verbose:
                    console.print(
                        f"[dim]Excluding nodes from '{filter_expr}': "
                        f"{len(exclude_nodes)} nodes[/dim]"
                    )
        elif is_node_filter(arg):
            # Positive filter
            has_include_filter = True
            if arg.lower() == "all":
                include_nodes.update(_get_all_nodes(verbose))
            else:
                resolved = resolve_node_filter(arg, verbose)
                if resolved and resolved != "ALL":
                    include_nodes.update(_expand_node_list(resolved))
                elif resolved == "ALL":
                    include_nodes.update(_get_all_nodes(verbose))
        elif "=" not in arg and not arg.lower().startswith("not:"):
            # Direct node name or range
            include_nodes.update(_expand_node_list(arg))
        else:
            # Not a node filter, pass through
            other_args.append(arg)

    # If we have exclusions but no inclusions, start with all nodes
    if exclude_nodes and not include_nodes and not has_include_filter:
        include_nodes = _get_all_nodes(verbose)

    # Apply exclusions
    result_nodes = include_nodes - exclude_nodes

    if verbose and exclude_nodes:
        console.print(
            f"[dim]After exclusions: {len(result_nodes)} nodes[/dim]"
        )

    return result_nodes, other_args


def generate_node_filter_autocomplete() -> str:
    """Generate bash autocomplete script for node filters.

    Returns:
        Bash script fragment for node filter completion
    """
    states = " ".join(NODE_STATES)
    filters = " ".join(NODE_FILTER_PREFIXES)
    neg_filters = " ".join(f"-{p}" for p in NODE_FILTER_PREFIXES)

    return f"""
# Node filter completion helper
_slurm_complete_node_filter() {{
    local cur="$1"
    local prev="$2"
    local cached_nodes="$(_slurm_cache_nodes)"
    local cached_partitions="$(_slurm_cache_partitions)"
    local node_filters="{filters}"
    local neg_filters="{neg_filters}"
    local node_states="{states}"

    # Handle negative filters
    if [[ "$cur" == -partition=* ]]; then
        local val="${{cur#-partition=}}"
        COMPREPLY=($(compgen -W "$cached_partitions" -- "$val"))
        [[ ${{#COMPREPLY[@]}} -gt 0 ]] && COMPREPLY=("${{COMPREPLY[@]/#/-partition=}}")
        return 0
    elif [[ "$cur" == -state=* ]]; then
        local val="${{cur#-state=}}"
        COMPREPLY=($(compgen -W "$node_states" -- "$val"))
        [[ ${{#COMPREPLY[@]}} -gt 0 ]] && COMPREPLY=("${{COMPREPLY[@]/#/-state=}}")
        return 0
    elif [[ "$cur" == -user=* ]]; then
        local val="${{cur#-user=}}"
        local users="$(_slurm_cache_users)"
        COMPREPLY=($(compgen -W "$users" -- "$val"))
        [[ ${{#COMPREPLY[@]}} -gt 0 ]] && COMPREPLY=("${{COMPREPLY[@]/#/-user=}}")
        return 0
    elif [[ "$cur" == -reservation=* ]]; then
        local val="${{cur#-reservation=}}"
        local reservations="$(_slurm_cache_reservations)"
        COMPREPLY=($(compgen -W "$reservations" -- "$val"))
        [[ ${{#COMPREPLY[@]}} -gt 0 ]] && COMPREPLY=("${{COMPREPLY[@]/#/-reservation=}}")
        return 0
    # Handle positive filters
    elif [[ "$cur" == partition=* ]] || [[ "$prev" == "=" && "${{COMP_WORDS[COMP_CWORD-2]}}" == "partition" ]]; then
        local val="${{cur#partition=}}"
        [[ "$prev" == "=" ]] && val="$cur"
        COMPREPLY=($(compgen -W "$cached_partitions" -- "$val"))
        [[ ${{#COMPREPLY[@]}} -gt 0 && "$cur" == *=* ]] && COMPREPLY=("${{COMPREPLY[@]/#/partition=}}")
        return 0
    elif [[ "$cur" == state=* ]] || [[ "$prev" == "=" && "${{COMP_WORDS[COMP_CWORD-2]}}" == "state" ]]; then
        local val="${{cur#state=}}"
        [[ "$prev" == "=" ]] && val="$cur"
        COMPREPLY=($(compgen -W "$node_states" -- "$val"))
        [[ ${{#COMPREPLY[@]}} -gt 0 && "$cur" == *=* ]] && COMPREPLY=("${{COMPREPLY[@]/#/state=}}")
        return 0
    elif [[ "$cur" == user=* ]] || [[ "$prev" == "=" && "${{COMP_WORDS[COMP_CWORD-2]}}" == "user" ]]; then
        local val="${{cur#user=}}"
        [[ "$prev" == "=" ]] && val="$cur"
        local users="$(_slurm_cache_users)"
        COMPREPLY=($(compgen -W "$users" -- "$val"))
        [[ ${{#COMPREPLY[@]}} -gt 0 && "$cur" == *=* ]] && COMPREPLY=("${{COMPREPLY[@]/#/user=}}")
        return 0
    elif [[ "$cur" == reservation=* ]] || [[ "$prev" == "=" && "${{COMP_WORDS[COMP_CWORD-2]}}" == "reservation" ]]; then
        local val="${{cur#reservation=}}"
        [[ "$prev" == "=" ]] && val="$cur"
        local reservations="$(_slurm_cache_reservations)"
        COMPREPLY=($(compgen -W "$reservations" -- "$val"))
        [[ ${{#COMPREPLY[@]}} -gt 0 && "$cur" == *=* ]] && COMPREPLY=("${{COMPREPLY[@]/#/reservation=}}")
        return 0
    fi

    # Default: show nodes and filter options
    COMPREPLY=($(compgen -W "$cached_nodes $node_filters $neg_filters" -- "$cur"))
    return 0
}}
"""  # noqa: E501
