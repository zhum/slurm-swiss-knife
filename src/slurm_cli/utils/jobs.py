"""Utilities for managing Slurm jobs."""

import json
import subprocess
from datetime import datetime
from typing import Any, Dict, List, Optional

from rich.box import SIMPLE_HEAVY
from rich.table import Table

from .base_resource import BaseSlurmResource
from .profiles import format_with_template, get_profile_config
from .utils import console


def _format_timestamp(epoch: int, default: str = "-") -> str:
    """Format Unix timestamp as YYYY-MM-DDTHH:MM:SS."""
    if not epoch or epoch <= 0:
        return default
    try:
        dt = datetime.fromtimestamp(epoch)
        return dt.strftime("%Y-%m-%dT%H:%M:%S")
    except (ValueError, OSError):
        return default


def _format_duration(minutes: int) -> str:
    """Format duration in minutes as DDD-HH:MM:SS (leading zeros ignored)."""
    if not minutes or minutes <= 0:
        return ""
    hours, mins = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    if days:
        return f"{days}-{hours:02d}:{mins:02d}:00"
    elif hours:
        return f"{hours}:{mins:02d}:00"
    else:
        return f"{mins}:00"


class Job(BaseSlurmResource):
    """Slurm job resource handler."""

    # Job states for filtering (in Slurm order)
    JOB_STATES = [
        "pending",
        "running",
        "cancelled",
        "completing",
        "completed",
        "boot_fail",
        "configuring",
        "deadline",
        "failed",
        "node_fail",
        "out_of_memory",
        "preempted",
        "resv_del_hold",
        "requeue_fed",
        "requeue_hold",
        "requeued",
        "resizing",
        "revoked",
        "signaling",
        "special_exit",
        "stage_out",
        "stopped",
        "suspended",
        "timeout",
    ]

    # Default columns for table output
    DEFAULT_COLUMNS = [
        "job_id",
        "user_name",
        "partition",
        "job_state",
        "start_time",
        "endlimit",
        "node_count",
        "gres",
        "reason",
    ]

    # All available columns
    ALL_COLUMNS = [
        "job_id",
        "name",
        "user_name",
        "account",
        "partition",
        "job_state",
        "time_limit",
        "endlimit",
        "node_count",
        "nodes",
        "cpus",
        "gres",
        "submit_time",
        "start_time",
        "end_time",
        "priority",
        "reason",
        "command",
        "working_directory",
        "standard_output",
        "standard_error",
    ]

    # Default styles for table columns
    DEFAULT_STYLES = {
        "job_id": "cyan bold",
        "name": "white",
        "user_name": "blue",
        "account": "magenta",
        "partition": "green",
        "job_state": "yellow",
        "time_limit": "dim",
        "endlimit": "dim",
        "node_count": "cyan",
        "nodes": "dim",
        "cpus": "yellow",
        "gres": "magenta",
        "submit_time": "dim",
        "start_time": "green",
        "end_time": "red",
        "priority": "magenta",
        "reason": "white",
        "command": "dim",
        "working_directory": "dim",
        "standard_output": "dim",
        "standard_error": "dim",
    }

    # Filter options
    JOB_FILTER_OPTIONS = [
        "job_id",
        "user",
        "account",
        "partition",
        "state",
        "name",
        "nodes",
        "reservation",
    ]

    def __init__(self, job_id: str = None, **kwargs: Any):
        self.job_id = job_id
        self.kwargs = kwargs

    @classmethod
    def get_profile_fields(cls) -> dict:
        """Return field names and descriptions for profile templates."""
        return {
            "job_id": "Job ID",
            "name": "Job name",
            "user_name": "Username",
            "account": "Account name",
            "partition": "Partition",
            "job_state": "Job state",
            "time_limit": "Time limit",
            "endlimit": "End time if known, otherwise time limit",
            "node_count": "Number of nodes",
            "nodes": "Node list",
            "cpus": "Number of CPUs",
            "gres": "Generic resources (GPUs, etc.)",
            "submit_time": "Submit time",
            "start_time": "Start time",
            "end_time": "End time",
            "priority": "Priority",
            "reason": "Reason/Comment",
            "command": "Command",
            "working_directory": "Working directory",
            "standard_output": "Standard output file",
            "standard_error": "Standard error file",
        }

    @classmethod
    def _fetch_jobs(
        cls, force_update: bool = False
    ) -> List[Dict[str, Any]]:
        """Fetch jobs from scontrol."""
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
        except (
            subprocess.CalledProcessError,
            json.JSONDecodeError,
        ) as e:
            console.print(f"[red]Failed to fetch jobs: {e}[/red]")
            return []

    @classmethod
    def _normalize_job(cls, job: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize job data for display."""

        # Handle nested structures
        def get_value(obj, key, default=""):
            val = obj.get(key, default)
            if isinstance(val, dict):
                if "number" in val:
                    return val.get("number", default)
                if "set" in val and not val.get("set", False):
                    return default
                return str(val)
            if isinstance(val, list):
                return ",".join(str(v) for v in val)
            return val if val else default

        # Get time limit from nested structure
        time_limit = job.get("time_limit", {})
        if isinstance(time_limit, dict):
            time_limit_val = time_limit.get("number", 0)
            if time_limit.get("infinite"):
                time_limit_str = "UNLIMITED"
            else:
                time_limit_str = _format_duration(time_limit_val)
        else:
            time_limit_str = (
                _format_duration(time_limit) if time_limit else ""
            )

        # Get node count
        node_count = get_value(job, "node_count", 0)
        if isinstance(node_count, dict):
            node_count = node_count.get("number", 0)

        # Get CPUs
        cpus = get_value(job, "cpus", 0)
        if isinstance(cpus, dict):
            cpus = cpus.get("number", 0)

        # Get job state - can be list or string
        job_state = job.get("job_state", "")
        if isinstance(job_state, list):
            job_state = ",".join(job_state)

        # Compute end_time and endlimit
        end_time_data = job.get("end_time", {})
        if isinstance(end_time_data, dict):
            end_time_set = end_time_data.get("set", False)
            end_time_num = end_time_data.get("number", 0)
            if end_time_set and end_time_num:
                end_time_str = _format_timestamp(end_time_num)
            else:
                end_time_str = "-"
        else:
            end_time_str = _format_timestamp(end_time_data)
            end_time_set = bool(end_time_data) and end_time_str != "-"

        # endlimit: end_time (as timestamp) if known, otherwise time_limit
        if end_time_str and end_time_str != "-":
            endlimit_str = end_time_str
        else:
            endlimit_str = time_limit_str if time_limit_str else "-"

        return {
            "job_id": str(get_value(job, "job_id", "")),
            "name": get_value(job, "name", ""),
            "user_name": get_value(job, "user_name", ""),
            "account": get_value(job, "account", ""),
            "partition": get_value(job, "partition", ""),
            "job_state": job_state,
            "time_limit": time_limit_str,
            "node_count": str(node_count),
            "nodes": get_value(job, "nodes", ""),
            "cpus": str(cpus),
            "gres": get_value(job, "tres_per_node", ""),
            "submit_time": _format_timestamp(
                job.get("submit_time", {}).get("number", 0)
                if isinstance(job.get("submit_time"), dict)
                else job.get("submit_time", 0)
            ),
            "start_time": _format_timestamp(
                job.get("start_time", {}).get("number", 0)
                if isinstance(job.get("start_time"), dict)
                else job.get("start_time", 0)
            ),
            "end_time": end_time_str,
            "endlimit": endlimit_str,
            "priority": str(job.get("priority", {}).get("number", ""))
            if isinstance(job.get("priority"), dict)
            else str(job.get("priority", "")),
            "reason": get_value(job, "state_reason", ""),
            "command": get_value(job, "command", ""),
            "working_directory": get_value(
                job, "current_working_directory", ""
            ),
            "standard_output": get_value(job, "standard_output", ""),
            "standard_error": get_value(job, "standard_error", ""),
        }

    @classmethod
    def _apply_filters(
        cls,
        jobs: List[Dict[str, Any]],
        filters: Dict[str, str],
    ) -> List[Dict[str, Any]]:
        """Apply filters to job list."""
        result = jobs

        for key, value in filters.items():
            key_lower = key.lower()
            value_lower = value.lower()

            if key_lower == "job_id":
                result = [
                    j
                    for j in result
                    if str(j.get("job_id", "")) == value
                ]
            elif key_lower == "user":
                result = [
                    j
                    for j in result
                    if value_lower in j.get("user_name", "").lower()
                ]
            elif key_lower == "account":
                result = [
                    j
                    for j in result
                    if value_lower in j.get("account", "").lower()
                ]
            elif key_lower == "partition":
                result = [
                    j
                    for j in result
                    if value_lower in j.get("partition", "").lower()
                ]
            elif key_lower == "state":
                result = [
                    j
                    for j in result
                    if value_lower in j.get("job_state", "").lower()
                ]
            elif key_lower == "name":
                result = [
                    j
                    for j in result
                    if value_lower in j.get("name", "").lower()
                ]
            elif key_lower == "nodes":
                result = [
                    j
                    for j in result
                    if value_lower in j.get("nodes", "").lower()
                ]
            elif key_lower == "reservation":
                result = [
                    j
                    for j in result
                    if value_lower in j.get("reservation", "").lower()
                ]

        return result

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
        """Show job information.

        Args:
            field: Optional filter (e.g., user=john, state=running)
            style: Output style ("pretty", "json", or "csv")
            force_cache_update: Whether to force cache update
            delimiter: Delimiter for CSV output (default: ";")
            zebra: Use zebra striping for table rows
            profile: Profile name to use for output formatting
            profile_str: Inline profile string (overrides profile)
        """
        # Get profile configuration
        columns, styles, template = get_profile_config(
            profile, "jobs", profile_str
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
            parts = field.split()
            for part in parts:
                if "=" in part:
                    key, value = part.split("=", 1)
                    filters[key] = value
                else:
                    # Treat as job_id filter
                    filters["job_id"] = part

        try:
            # Fetch jobs
            raw_jobs = cls._fetch_jobs(force_cache_update)

            if not raw_jobs:
                console.print("[yellow]No jobs found.[/yellow]")
                return

            # Normalize jobs
            jobs = [cls._normalize_job(j) for j in raw_jobs]

            # Apply filters
            if filters:
                jobs = cls._apply_filters(jobs, filters)

            if not jobs:
                console.print(
                    "[yellow]No jobs matching filters found.[/yellow]"
                )
                return

            # Output based on style
            if style == "json":
                console.print_json(json.dumps(jobs, indent=2))
            elif style == "csv":
                # CSV header
                print(delimiter.join(columns))
                for job in jobs:
                    row = [str(job.get(col, "")) for col in columns]
                    print(delimiter.join(row))
            elif template:
                # Template-based output
                for job in jobs:
                    console.print(format_with_template(template, job))
            else:
                # Pretty table output
                table = Table(
                    title="Slurm Jobs",
                    box=SIMPLE_HEAVY,
                    show_header=True,
                    header_style="bold",
                )

                # Add columns
                for col in columns:
                    col_style = merged_styles.get(col, "white")
                    table.add_column(
                        col.replace("_", " ").title(), style=col_style
                    )

                # Add rows
                for i, job in enumerate(jobs):
                    row_style = None
                    if zebra and i % 2 == 1:
                        row_style = "on grey15"
                    row = [str(job.get(col, "")) for col in columns]
                    table.add_row(*row, style=row_style)

                console.print(table)

        except subprocess.CalledProcessError as e:
            console.print(
                f"[red]Failed to show jobs:[/red] {e.stderr or e}"
            )

    @classmethod
    def create(cls, *args, **kwargs) -> None:
        """Jobs are created via sbatch/srun, not scontrol."""
        console.print(
            "[yellow]Jobs are created using sbatch or srun commands, "
            "not through this CLI.[/yellow]"
        )

    @classmethod
    def update(
        cls, job_id: str, verbose: bool = False, **kwargs: Any
    ) -> None:
        """Update a job using scontrol."""
        if not job_id:
            console.print("[red]Job ID is required.[/red]")
            return

        options = " ".join(f"{k}={v}" for k, v in kwargs.items())
        cmd = ["scontrol", "update", f"jobid={job_id}"]
        if options:
            cmd.append(options)

        try:
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True,
                errors="replace",
            )
            if result.stdout:
                console.print(result.stdout)
            if verbose:
                console.print(
                    f"[green]Job '{job_id}' updated successfully.[/green]"
                )
        except subprocess.CalledProcessError as e:
            console.print(
                f"[red]Failed to update job '{job_id}':[/red] {e.stderr or e}"
            )

    @classmethod
    def delete(
        cls, job_id: str, verbose: bool = False, **kwargs: Any
    ) -> None:
        """Cancel job(s) using scancel.

        Args:
            job_id: Job ID or filter expression (e.g., user=john)
            verbose: Print verbose output
            **kwargs: Additional filter options
        """
        # Check if job_id is a filter expression
        if job_id and "=" in job_id:
            # Parse as filter
            key, value = job_id.split("=", 1)
            kwargs[key] = value
            job_id = None

        # If we have filters, fetch and filter jobs first
        if kwargs:
            raw_jobs = cls._fetch_jobs()
            if not raw_jobs:
                console.print("[yellow]No jobs found.[/yellow]")
                return

            jobs = [cls._normalize_job(j) for j in raw_jobs]
            jobs = cls._apply_filters(jobs, kwargs)

            if not jobs:
                console.print(
                    "[yellow]No jobs matching filters found.[/yellow]"
                )
                return

            # Cancel all matching jobs in one call
            job_ids = [j["job_id"] for j in jobs]
            console.print(
                f"[yellow]Cancelling {len(job_ids)} job(s)...[/yellow]"
            )
            cls._cancel_jobs(job_ids, verbose=verbose)
        elif job_id:
            # Cancel single job by ID
            cls._cancel_jobs([job_id], verbose=verbose)
        else:
            console.print("[red]Job ID or filter is required.[/red]")

    @classmethod
    def _cancel_jobs(
        cls, job_ids: List[str], verbose: bool = False
    ) -> None:
        """Cancel jobs by IDs (pass all to scancel in one call)."""
        if not job_ids:
            return
        try:
            result = subprocess.run(
                ["scancel"] + job_ids,
                check=True,
                capture_output=True,
                text=True,
                errors="replace",
            )
            if result.stdout:
                console.print(result.stdout)
            if verbose:
                console.print(
                    f"[green]{len(job_ids)} job(s) cancelled.[/green]"
                )
        except subprocess.CalledProcessError as e:
            console.print(
                f"[red]Failed to cancel jobs:[/red] {e.stderr or e}"
            )

    @classmethod
    def generate_autocomplete_options(cls) -> str:
        """Generate bash autocomplete script for job options."""
        filter_opts = " ".join(
            f"{opt}=" for opt in cls.JOB_FILTER_OPTIONS
        )
        states = " ".join(cls.JOB_STATES)

        script = f"""
_slurm_cli_jobs_autocomplete() {{
    local cmd="$1"
    local pos="$2"

    local cur="${{COMP_WORDS[COMP_CWORD]}}"
    local prev="${{COMP_WORDS[COMP_CWORD-1]}}"

    local filter_options="{filter_opts}"

    # Handle key=value completion
    if _slurm_parse_keyval "$cur" "$prev"; then
        case "$_key" in
            state)
                _slurm_complete_value "{states}" "$_key" "$_val" "$cur" ;;
            user)
                _slurm_complete_value "$(_slurm_cache_users)" "$_key" "$_val" "$cur" ;;
            account)
                _slurm_complete_value "$(_slurm_cache_accounts)" "$_key" "$_val" "$cur" ;;
            partition)
                _slurm_complete_value "$(_slurm_cache_partitions)" "$_key" "$_val" "$cur" ;;
            nodes)
                _slurm_complete_value "$(_slurm_cache_nodes)" "$_key" "$_val" "$cur" ;;
            reservation)
                _slurm_complete_value "$(_slurm_cache_reservations)" "$_key" "$_val" "$cur" ;;
        esac
        [[ ${{#COMPREPLY[@]}} -gt 0 ]] && return
    fi

    local cached_jobs="$(_slurm_cache_jobs)"

    # Default: show filter options and job IDs
    case "$cmd" in
        show)
            _slurm_complete "$filter_options" "$cur" ;;
        delete|del|cancel)
            _slurm_complete "$filter_options $cached_jobs" "$cur" ;;
        update)
            _slurm_complete "$cached_jobs" "$cur" ;;
    esac
}}
"""  # noqa: E501
        return script
