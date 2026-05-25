"""Job filter utilities for selecting jobs by various criteria.

Supports filtering jobs by:
- user=<username> - jobs by a specific user
- account=<account> - jobs charged to a specific account
- partition=<name> - jobs in a specific partition
- state=<state> - jobs with a specific state
- name=<pattern> - jobs matching exact name (squeue -n)
- jobname=<regex> - jobs matching name by regex pattern
- nodes=<nodelist> - jobs running on specific nodes
- reservation=<name> - jobs using a specific reservation

Exclusion filters (prefix with not:):
- not:user=<username> - exclude jobs by user
- not:account=<account> - exclude jobs by account
- not:partition=<name> - exclude jobs in partition
- not:state=<state> - exclude jobs with state
- not:jobname=<regex> - exclude jobs matching name regex

Filter syntax can be used in delete and update jobs commands:
- slurm-cli delete jobs user=john
- slurm-cli update jobs state=pending priority=100
- slurm-cli hold partition=gpu not:user=admin
- slurm-cli hold jobname=test.*
"""

import json
import re
import subprocess
from typing import List

from .utils import console

# Filter prefixes that indicate a job filter expression
JOB_FILTER_PREFIXES = [
    "user=",
    "account=",
    "partition=",
    "state=",
    "name=",
    "jobname=",
    "nodes=",
    "reservation=",
]


def is_job_filter(value: str) -> bool:
    """Check if a value is a job filter expression.

    Recognizes both positive and negative (not:) filters.

    Args:
        value: Value to check

    Returns:
        True if value is a job filter expression
    """
    if not value:
        return False
    value_lower = value.lower()
    # Check for not: prefix
    if value_lower.startswith("not:"):
        value_lower = value_lower[4:]
    return any(value_lower.startswith(p) for p in JOB_FILTER_PREFIXES)


def parse_job_filter(filter_expr: str) -> dict:
    """Parse a job filter expression into key-value pair.

    Args:
        filter_expr: Filter expression like "user=john"

    Returns:
        Dict with filter key and value, e.g. {"user": "john"}
    """
    if not filter_expr or "=" not in filter_expr:
        return {}
    key, value = filter_expr.split("=", 1)
    return {key.lower(): value}


def resolve_job_filter(filter_expr: str, verbose: bool = False) -> List[str]:
    """Resolve a job filter expression to a list of job IDs.

    Args:
        filter_expr: Filter expression like "user=john", "state=pending"
        verbose: Print debug information

    Returns:
        List of job IDs matching the filter
    """
    if not filter_expr:
        return []

    filter_lower = filter_expr.lower()

    # Parse filter type and value
    if filter_lower.startswith("user="):
        return _get_jobs_by_user(filter_expr[5:], verbose)
    elif filter_lower.startswith("account="):
        return _get_jobs_by_account(filter_expr[8:], verbose)
    elif filter_lower.startswith("partition="):
        return _get_jobs_by_partition(filter_expr[10:], verbose)
    elif filter_lower.startswith("state="):
        return _get_jobs_by_state(filter_expr[6:], verbose)
    elif filter_lower.startswith("name="):
        return _get_jobs_by_name(filter_expr[5:], verbose)
    elif filter_lower.startswith("jobname="):
        return _get_jobs_by_name_regex(filter_expr[8:], verbose)
    elif filter_lower.startswith("nodes="):
        return _get_jobs_by_nodes(filter_expr[6:], verbose)
    elif filter_lower.startswith("reservation="):
        return _get_jobs_by_reservation(filter_expr[12:], verbose)
    else:
        # Not a filter, assume it's a job ID
        return [filter_expr] if filter_expr.isdigit() else []


def _fetch_all_jobs(verbose: bool = False) -> List[dict]:
    """Fetch all jobs from scontrol."""
    try:
        result = subprocess.run(
            ["scontrol", "show", "job", "--json"],
            capture_output=True,
            text=True,
            check=True,
            errors="replace",
        )
        data = json.loads(result.stdout)
        return data.get("jobs", [])
    except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
        if verbose:
            console.print(f"[red]Failed to fetch jobs: {e}[/red]")
        return []


def _get_jobs_by_user(user: str, verbose: bool = False) -> List[str]:
    """Get job IDs for jobs by a specific user."""
    try:
        # Use squeue for efficiency
        result = subprocess.run(
            ["squeue", "-u", user, "-h", "-o", "%i"],
            capture_output=True,
            text=True,
            check=True,
            errors="replace",
        )
        job_ids = [
            jid.strip() for jid in result.stdout.strip().split("\n") if jid.strip()
        ]
        if verbose:
            console.print(f"[dim]Jobs for user '{user}': {len(job_ids)} found[/dim]")
        return job_ids
    except subprocess.CalledProcessError as e:
        if verbose:
            console.print(f"[red]Failed to get jobs by user: {e.stderr}[/red]")
        return []


def _get_jobs_by_account(account: str, verbose: bool = False) -> List[str]:
    """Get job IDs for jobs charged to a specific account."""
    try:
        result = subprocess.run(
            ["squeue", "-A", account, "-h", "-o", "%i"],
            capture_output=True,
            text=True,
            check=True,
            errors="replace",
        )
        job_ids = [
            jid.strip() for jid in result.stdout.strip().split("\n") if jid.strip()
        ]
        if verbose:
            console.print(
                f"[dim]Jobs for account '{account}': " f"{len(job_ids)} found[/dim]"
            )
        return job_ids
    except subprocess.CalledProcessError as e:
        if verbose:
            console.print(f"[red]Failed to get jobs by account: {e.stderr}[/red]")
        return []


def _get_jobs_by_partition(partition: str, verbose: bool = False) -> List[str]:
    """Get job IDs for jobs in a specific partition."""
    try:
        result = subprocess.run(
            ["squeue", "-p", partition, "-h", "-o", "%i"],
            capture_output=True,
            text=True,
            check=True,
            errors="replace",
        )
        job_ids = [
            jid.strip() for jid in result.stdout.strip().split("\n") if jid.strip()
        ]
        if verbose:
            console.print(
                f"[dim]Jobs in partition '{partition}': " f"{len(job_ids)} found[/dim]"
            )
        return job_ids
    except subprocess.CalledProcessError as e:
        if verbose:
            console.print(f"[red]Failed to get jobs by partition: {e.stderr}[/red]")
        return []


def _get_jobs_by_state(state: str, verbose: bool = False) -> List[str]:
    """Get job IDs for jobs with a specific state."""
    try:
        result = subprocess.run(
            ["squeue", "-t", state, "-h", "-o", "%i"],
            capture_output=True,
            text=True,
            check=True,
            errors="replace",
        )
        job_ids = [
            jid.strip() for jid in result.stdout.strip().split("\n") if jid.strip()
        ]
        if verbose:
            console.print(f"[dim]Jobs with state '{state}': {len(job_ids)} found[/dim]")
        return job_ids
    except subprocess.CalledProcessError as e:
        if verbose:
            console.print(f"[red]Failed to get jobs by state: {e.stderr}[/red]")
        return []


def _get_jobs_by_name(name: str, verbose: bool = False) -> List[str]:
    """Get job IDs for jobs matching a name pattern."""
    try:
        result = subprocess.run(
            ["squeue", "-n", name, "-h", "-o", "%i"],
            capture_output=True,
            text=True,
            check=True,
            errors="replace",
        )
        job_ids = [
            jid.strip() for jid in result.stdout.strip().split("\n") if jid.strip()
        ]
        if verbose:
            console.print(f"[dim]Jobs with name '{name}': {len(job_ids)} found[/dim]")
        return job_ids
    except subprocess.CalledProcessError as e:
        if verbose:
            console.print(f"[red]Failed to get jobs by name: {e.stderr}[/red]")
        return []


def _get_jobs_by_name_regex(pattern: str, verbose: bool = False) -> List[str]:
    """Get job IDs for jobs with name matching a regex pattern.

    Args:
        pattern: Regex pattern to match against job names
        verbose: Print debug information

    Returns:
        List of job IDs with names matching the pattern
    """
    try:
        # Compile regex pattern (case-insensitive)
        try:
            regex = re.compile(pattern, re.IGNORECASE)
        except re.error as e:
            if verbose:
                console.print(f"[red]Invalid regex pattern '{pattern}': {e}[/red]")
            return []

        # Get all jobs with their names
        result = subprocess.run(
            ["squeue", "-h", "-o", "%i %j"],
            capture_output=True,
            text=True,
            check=True,
            errors="replace",
        )

        job_ids = []
        for line in result.stdout.strip().split("\n"):
            if not line.strip():
                continue
            parts = line.split(maxsplit=1)
            if len(parts) >= 2:
                job_id, job_name = parts[0], parts[1]
                if regex.search(job_name):
                    job_ids.append(job_id.strip())

        if verbose:
            console.print(
                f"[dim]Jobs matching name pattern '{pattern}': "
                f"{len(job_ids)} found[/dim]"
            )
        return job_ids
    except subprocess.CalledProcessError as e:
        if verbose:
            console.print(f"[red]Failed to get jobs by name regex: {e.stderr}[/red]")
        return []


def _get_jobs_by_nodes(nodes: str, verbose: bool = False) -> List[str]:
    """Get job IDs for jobs running on specific nodes."""
    try:
        result = subprocess.run(
            ["squeue", "-w", nodes, "-h", "-o", "%i"],
            capture_output=True,
            text=True,
            check=True,
            errors="replace",
        )
        job_ids = [
            jid.strip() for jid in result.stdout.strip().split("\n") if jid.strip()
        ]
        if verbose:
            console.print(f"[dim]Jobs on nodes '{nodes}': {len(job_ids)} found[/dim]")
        return job_ids
    except subprocess.CalledProcessError as e:
        if verbose:
            console.print(f"[red]Failed to get jobs by nodes: {e.stderr}[/red]")
        return []


def _get_jobs_by_reservation(reservation: str, verbose: bool = False) -> List[str]:
    """Get job IDs for jobs using a specific reservation."""
    try:
        result = subprocess.run(
            ["squeue", "-R", reservation, "-h", "-o", "%i"],
            capture_output=True,
            text=True,
            check=True,
            errors="replace",
        )
        job_ids = [
            jid.strip() for jid in result.stdout.strip().split("\n") if jid.strip()
        ]
        if verbose:
            console.print(
                f"[dim]Jobs in reservation '{reservation}': "
                f"{len(job_ids)} found[/dim]"
            )
        return job_ids
    except subprocess.CalledProcessError as e:
        if verbose:
            console.print(f"[red]Failed to get jobs by reservation: {e.stderr}[/red]")
        return []


def _get_all_jobs(verbose: bool = False) -> List[str]:
    """Get all job IDs from the queue."""
    try:
        result = subprocess.run(
            ["squeue", "-h", "-o", "%i"],
            capture_output=True,
            text=True,
            check=True,
            errors="replace",
        )
        job_ids = [
            jid.strip() for jid in result.stdout.strip().split("\n") if jid.strip()
        ]
        if verbose:
            console.print(f"[dim]All jobs: {len(job_ids)} found[/dim]")
        return job_ids
    except subprocess.CalledProcessError as e:
        if verbose:
            console.print(f"[red]Failed to get all jobs: {e.stderr}[/red]")
        return []


def resolve_job_filters(
    args: List[str], verbose: bool = False
) -> tuple[set, List[str]]:
    """Resolve a list of job arguments with inclusion/exclusion support.

    Handles positive filters, negative filters (not:prefix),
    and direct job IDs.
    Returns a set of job IDs after applying all filters.

    Args:
        args: List of job IDs or filter expressions
        verbose: Print debug information

    Returns:
        Tuple of (job_ids_set, other_args) where:
        - job_ids_set: Set of resolved job IDs after exclusions
        - other_args: List of args that are not job IDs or filters
    """
    included_jobs: set = set()
    excluded_jobs: set = set()
    other_args: List[str] = []
    has_positive_filter = False

    for arg in args:
        if not arg:
            continue

        arg_lower = arg.lower()

        # Check for not: prefix (exclusion)
        if arg_lower.startswith("not:"):
            filter_part = arg[4:]  # Remove "not:" prefix
            if is_job_filter(filter_part):
                resolved = resolve_job_filter(filter_part, verbose)
                excluded_jobs.update(resolved)
                if verbose:
                    console.print(
                        f"[dim]Excluding {len(resolved)} jobs "
                        f"from filter: {filter_part}[/dim]"
                    )
            else:
                other_args.append(arg)
        elif is_job_filter(arg):
            # Positive filter
            has_positive_filter = True
            resolved = resolve_job_filter(arg, verbose)
            included_jobs.update(resolved)
            if verbose:
                console.print(
                    f"[dim]Including {len(resolved)} jobs " f"from filter: {arg}[/dim]"
                )
        elif arg.isdigit() or "_" in arg:
            # Direct job ID (may include array job IDs like 123_4)
            has_positive_filter = True
            included_jobs.add(arg)
        else:
            other_args.append(arg)

    # If only exclusions specified, start with all jobs
    if not has_positive_filter and excluded_jobs:
        all_jobs = _get_all_jobs(verbose)
        included_jobs = set(all_jobs)
        if verbose:
            console.print(f"[dim]Starting with all {len(included_jobs)} jobs[/dim]")

    # Apply exclusions
    final_jobs = included_jobs - excluded_jobs

    if verbose and excluded_jobs:
        console.print(f"[dim]After exclusions: {len(final_jobs)} jobs[/dim]")

    return final_jobs, other_args


def resolve_job_ids(
    args: List[str], verbose: bool = False
) -> tuple[List[str], List[str]]:
    """Resolve a list of job IDs and filters to job IDs.

    Note: This function is kept for backward compatibility with scancel.
    For job control commands that need exclusion support,
    use resolve_job_filters.

    Args:
        args: List of job IDs or filter expressions
        verbose: Print debug information

    Returns:
        Tuple of (job_ids, user_filters) where:
        - job_ids: List of resolved job IDs
        - user_filters: List of user= filters (for scancel -u optimization)
    """
    job_ids = []
    user_filters = []

    for arg in args:
        if not arg:
            continue
        arg_lower = arg.lower()

        # Special handling for user= filter (can use scancel -u)
        if arg_lower.startswith("user="):
            user_filters.append(arg[5:])
        elif is_job_filter(arg):
            # Resolve filter to job IDs
            resolved = resolve_job_filter(arg, verbose)
            job_ids.extend(resolved)
        elif arg.isdigit() or "_" in arg:
            # Direct job ID (may include array job IDs like 123_4)
            job_ids.append(arg)

    # Remove duplicates while preserving order
    seen = set()
    unique_job_ids = []
    for jid in job_ids:
        if jid not in seen:
            seen.add(jid)
            unique_job_ids.append(jid)

    return unique_job_ids, user_filters
