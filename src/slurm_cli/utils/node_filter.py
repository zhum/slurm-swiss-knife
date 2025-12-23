"""Node filter utilities for selecting nodes by various criteria.

Supports filtering nodes by:
- partition=<name> - nodes from a specific partition
- state=<state> - nodes with a specific state
- user=<username> - nodes running jobs by a specific user
- reservation=<name> - nodes in a specific reservation

Filter syntax can be used anywhere node names are expected, e.g.:
- slurm-cli update reservations test nodes=partition=cpu
- slurm-cli update nodes state=drain partition=gpu
"""

import json
import subprocess
from typing import List, Optional

from .utils import console


# Filter prefixes that indicate a node filter expression
NODE_FILTER_PREFIXES = [
    "partition=",
    "state=",
    "user=",
    "reservation=",
]


def is_node_filter(value: str) -> bool:
    """Check if a value is a node filter expression or special keyword."""
    if not value:
        return False
    value_lower = value.lower()
    # Check for ALL keyword
    if value_lower == "all":
        return True
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
