"""Utilities for managing QoS."""

import json
import subprocess
from typing import Any, List, Optional

from rich.box import SIMPLE_HEAVY
from rich.table import Table

from .base_resource import BaseSlurmResource
from .profiles import (
    format_with_template,
    get_profile_config,
    sort_data,
)
from .utils import console

# QoS configuration options (sacctmgr field names)
QOS_OPTIONS: List[str] = [
    "Description",
    "Flags",
    "GraceTime",
    "GrpJobs",
    "GrpJobsAccrue",
    "GrpSubmit",
    "GrpSubmitJobs",
    "GrpTRES",
    "GrpTRESMins",
    "GrpTRESRunMins",
    "GrpWall",
    "LimitFactor",
    "MaxJobsAccruePA",
    "MaxJobsAccruePerAccount",
    "MaxJobsAccruePU",
    "MaxJobsAccruePerUser",
    "MaxJobsPA",
    "MaxJobsPerAccount",
    "MaxJobsPU",
    "MaxJobsPerUser",
    "MaxSubmitJobsPA",
    "MaxSubmitJobsPerAccount",
    "MaxSubmitJobsPU",
    "MaxSubmitJobsPerUser",
    "MaxTRES",
    "MaxTRESPJ",
    "MaxTRESPerJob",
    "MaxTRESMins",
    "MaxTRESMinsPJ",
    "MaxTRESMinsPerJob",
    "MaxTRESPA",
    "MaxTRESPerAccount",
    "MaxTRESPN",
    "MaxTRESPerNode",
    "MaxTRESPU",
    "MaxTRESPerUser",
    "MaxTRESRunMinsPA",
    "MaxTRESRunMinsPerAccount",
    "MaxTRESRunMinsPU",
    "MaxTRESRunMinsPerUser",
    "MaxWall",
    "MaxWallDurationPerJob",
    "MinPrioThreshold",
    "MinTRES",
    "MinTRESPerJob",
    "Name",
    "Preempt",
    "PreemptExemptTime",
    "PreemptMode",
    "Priority",
    "RawUsage",
    "UsageFactor",
    "UsageThreshold",
]

# Valid QoS flags
QOS_FLAGS: List[str] = [
    "DenyOnLimit",
    "EnforceUsageThreshold",
    "NoDecay",
    "NoReserve",
    "OverPartQOS",
    "PartitionMaxNodes",
    "PartitionMinNodes",
    "PartitionTimeLimit",
    "Relative",
    "RequiresReservation",
    "UsageFactorSafe",
]

# Valid PreemptMode values
PREEMPT_MODE_VALUES: List[str] = [
    "OFF",
    "CANCEL",
    "GANG",
    "REQUEUE",
    "SUSPEND",
    "WITHIN",
]


class Qos(BaseSlurmResource):
    def __init__(self, name: str, **kwargs: Any):
        self.name = name
        self.kwargs = kwargs

    @classmethod
    def get_profile_fields(cls) -> dict:
        """Return field names and descriptions for profile templates."""
        return {
            "name": "QoS name",
            "id": "QoS ID",
            "description": "QoS description",
            "priority": "Priority value",
            "usage_factor": "Usage factor (default: 1.0)",
            "usage_threshold": "Usage threshold",
            "grace_time": "Grace time in seconds",
            "flags": f"QoS flags: {', '.join(QOS_FLAGS)}",
            "preempt_mode": f"Preempt mode: {', '.join(PREEMPT_MODE_VALUES)}",
            "preempt_list": "List of QoS names that can be preempted",
            "preempt_exempt_time": "Preempt exempt time in seconds",
            "limit_factor": "Limit factor",
            "min_prio_threshold": "Minimum priority threshold",
            "grp_jobs": "Max running jobs for all users in QoS",
            "grp_jobs_accrue": "Max accruing jobs for all users in QoS",
            "grp_submit": "Max submitted jobs for all users in QoS",
            "grp_tres": "Max TRES for all users in QoS",
            "grp_tres_mins": "Max TRES minutes for all users in QoS",
            "grp_tres_run_mins": "Max TRES run mins for all users",
            "grp_wall": "Max wall clock time for all users in QoS",
            "max_jobs_per_user": "Max running jobs per user",
            "max_jobs_per_account": "Max running jobs per account",
            "max_jobs_accrue_per_user": "Max accruing jobs per user",
            "max_jobs_accrue_per_account": "Max accruing jobs per account",
            "max_submit_jobs_per_user": "Max submitted jobs per user",
            "max_submit_jobs_per_account": "Max submitted jobs per account",
            "max_wall": "Max wall clock time per job",
            "max_tres_per_job": "Max TRES per job",
            "max_tres_per_user": "Max TRES per user",
            "max_tres_per_account": "Max TRES per account",
            "max_tres_per_node": "Max TRES per node",
            "max_tres_mins_per_job": "Max TRES minutes per job",
            "max_tres_run_mins_per_user": "Max TRES run mins per user",
            "max_tres_run_mins_per_account": "Max TRES run mins per account",
            "max_tres_total": "Max TRES total",
            "min_tres_per_job": "Min TRES per job",
            "raw_usage": "Raw usage value",
        }

    @classmethod
    def create(
        cls, name: str, verbose: bool = False, **kwargs: Any
    ) -> None:
        """Create a new QoS."""
        console.print(f"Creating QoS: {name}")
        args = ["sacctmgr", "create", "qos", name]
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
                f"[green]QoS '{name}' created successfully.[/green]"
            )
            if result.stdout:
                console.print(result.stdout)
        except subprocess.CalledProcessError as e:
            console.print(
                f"[red]Failed to create QoS '{name}':[/red] {e.stderr or e}"
            )

    @classmethod
    def update(
        cls,
        name: str,
        verbose: bool = False,
        where_conditions: Optional[List[str]] = None,
        set_values: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> None:
        """Update a QoS.

        Two calling modes:
        1. Simple: update(name, key=value, ...) - updates QoS by name
        2. Where: update("", where_conditions=[...], set_values=[...])
           - uses WHERE/SET syntax for bulk updates

        Args:
            name: QoS name to update (for simple mode)
            verbose: Enable verbose output
            where_conditions: List of WHERE conditions (e.g., ["priority=100"])
            set_values: List of SET values (e.g., ["priority=200"])
            **kwargs: SET options as keyword arguments
        """
        # Build the command
        args = ["sacctmgr", "-i", "modify", "qos"]

        # Determine mode and build WHERE clause
        if where_conditions:
            # WHERE/SET mode
            args.append("where")
            for cond in where_conditions:
                args.append(cond)
        elif name:
            # Simple mode - update by name
            args.extend(["where", f"name={name}"])
        else:
            console.print(
                "[red]No QoS name or WHERE conditions specified.[/red]"
            )
            return

        # Build SET clause
        args.append("set")

        # Use set_values if provided, otherwise use kwargs
        if set_values:
            for val in set_values:
                # Validate preemptmode even in WHERE mode
                if "=" in val:
                    k, v = val.split("=", 1)
                    if k.lower() == "preemptmode":
                        if v.upper() not in PREEMPT_MODE_VALUES:
                            console.print(
                                f"[red]Invalid preemptmode '{v}'. "
                                f"Must be one of: "
                                f"{', '.join(PREEMPT_MODE_VALUES)}[/red]"
                            )
                            return
                args.append(val)
        else:
            for key, value in kwargs.items():
                if value is None:
                    continue

                key_lower = key.lower()

                # Validate preemptmode values
                if key_lower == "preemptmode":
                    if value.upper() not in PREEMPT_MODE_VALUES:
                        console.print(
                            f"[red]Invalid preemptmode '{value}'. "
                            f"Must be one of: "
                            f"{', '.join(PREEMPT_MODE_VALUES)}[/red]"
                        )
                        return

                args.append(f"{key_lower}={value}")

        if verbose:
            console.print(f"Running: {' '.join(args)}")

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
                    f"[green]QoS '{name}' updated successfully.[/green]"
                )
        except subprocess.CalledProcessError as e:
            console.print(
                f"[red]Failed to update QoS '{name}':[/red] "
                f"{e.stderr or e}"
            )

    @classmethod
    def delete(cls, name: str, verbose: bool = False) -> None:
        """Delete a QoS.

        Args:
            name: QoS name to delete
            verbose: Enable verbose output
        """
        if not name:
            console.print(
                "[red]No QoS name specified for deletion.[/red]"
            )
            return

        args = ["sacctmgr", "-i", "delete", "qos", f"names={name}"]

        if verbose:
            console.print(f"Running: {' '.join(args)}")

        try:
            result = subprocess.run(
                args,
                check=True,
                capture_output=True,
                text=True,
            )
            if result.stdout:
                console.print(result.stdout)
            console.print(
                f"[green]QoS '{name}' deleted successfully.[/green]"
            )
        except subprocess.CalledProcessError as e:
            console.print(
                f"[red]Failed to delete QoS '{name}':[/red] "
                f"{e.stderr or e}"
            )

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
        """Show QoS information.

        Args:
            field: Optional QoS name to filter by
            style: Output style ("pretty", "json", or "csv")
            force_cache_update: Whether to force cache update (unused)
            delimiter: Delimiter for CSV output (default: ";")
            zebra: Use zebra striping for table rows (default: False)
            profile: Profile name to use for output formatting
            profile_str: Inline profile string (overrides profile)
        """
        # Get profile configuration (for future enhancement)
        (
            columns_cfg,
            styles_cfg,
            template_cfg,
            sort_field,
            sort_asc,
        ) = get_profile_config(profile, "qos", profile_str)
        try:
            # Always get JSON output from sacctmgr
            result = subprocess.run(
                ["sacctmgr", "show", "qos", "--json"],
                check=True,
                capture_output=True,
                text=True,
            )

            if not result.stdout:
                console.print("[yellow]No QoS found.[/yellow]")
                return

            # Parse JSON data
            data = json.loads(result.stdout)
            qos_list = data.get("qos", [])

            # Filter by field (QoS name) if specified
            if field:
                qos_list = [
                    qos for qos in qos_list if qos.get("name") == field
                ]
                if not qos_list:
                    console.print(
                        f"[yellow]QoS '{field}' not found.[/yellow]"
                    )
                    return

            # Apply sorting
            if sort_field:
                qos_list = sort_data(qos_list, sort_field, sort_asc)

            # Helper functions (used by both CSV and pretty styles)
            def get_set_value(obj, default="-"):
                if isinstance(obj, dict):
                    if obj.get("set", False):
                        val = obj.get("number")
                        if val is not None:
                            return str(val)
                return default

            def format_tres_list(tres_list):
                """Format TRES list to human-readable string."""
                if not tres_list:
                    return "-"
                parts = []
                for tres in tres_list:
                    if isinstance(tres, dict):
                        name = tres.get("name") or tres.get("type", "")
                        count = tres.get("count", "")
                        if name and count:
                            parts.append(f"{name}={count}")
                return ",".join(parts) if parts else "-"

            def get_nested(obj, path):
                """Get nested dictionary value by dot-separated path."""
                keys = path.split(".")
                current = obj
                for key in keys:
                    if isinstance(current, dict):
                        current = current.get(key, {})
                    else:
                        return None
                return current

            if style == "json":
                # Print filtered JSON
                console.print_json(
                    json.dumps({"qos": qos_list}, indent=2)
                )
            elif template_cfg and style == "pretty":
                # Use template-based output
                for qos in qos_list:
                    prepared = cls._prepare_template_data(qos)
                    output = format_with_template(
                        template_cfg, prepared, resource="qos"
                    )
                    console.print(output)
            elif style in ["csv", "pretty"]:
                # Column definitions (used by both CSV and pretty styles)
                column_definitions = [
                    (
                        "name",
                        "Name",
                        "cyan",
                        "left",
                        lambda q: q.get("name", ""),
                    ),
                    (
                        "id",
                        "ID",
                        "magenta",
                        "right",
                        lambda q: str(q.get("id", "")),
                    ),
                    (
                        "description",
                        "Desc",
                        "white",
                        "left",
                        lambda q: q.get("description", ""),
                    ),
                    (
                        "priority",
                        "Priority",
                        "yellow",
                        "right",
                        lambda q: get_set_value(q.get("priority", {})),
                    ),
                    (
                        "usage_factor",
                        "UsageFactor",
                        "green",
                        "right",
                        lambda q: get_set_value(
                            q.get("usage_factor", {}), "1.0"
                        ),
                    ),
                    (
                        "usage_threshold",
                        "UsageThreshold",
                        "blue",
                        "right",
                        lambda q: get_set_value(
                            q.get("usage_threshold", {})
                        ),
                    ),
                    (
                        "flags",
                        "Flags",
                        "yellow",
                        "left",
                        lambda q: ",".join(q.get("flags", [])) or "-",
                    ),
                    (
                        "preempt_mode",
                        "PreemptMode",
                        "red",
                        "left",
                        lambda q: ",".join(
                            q.get("preempt", {}).get("mode", [])
                        )
                        or "-",
                    ),
                    (
                        "preempt_list",
                        "PreemptList",
                        "red",
                        "left",
                        lambda q: ",".join(
                            q.get("preempt", {}).get("list", [])
                        )
                        or "-",
                    ),
                    (
                        "preempt_exempt_time",
                        "PreemptExempt",
                        "red",
                        "right",
                        lambda q: get_set_value(
                            q.get("preempt", {}).get("exempt_time", {})
                        ),
                    ),
                    (
                        "grace_time",
                        "GraceTime",
                        "blue",
                        "right",
                        lambda q: (
                            str(
                                get_nested(q, "limits.grace_time") or ""
                            )
                            if get_nested(q, "limits.grace_time")
                            else "-"
                        ),
                    ),
                    (
                        "limits_factor",
                        "LimitsFactor",
                        "green",
                        "right",
                        lambda q: get_set_value(
                            get_nested(q, "limits.factor") or {}
                        ),
                    ),
                    (
                        "max_wall_per_job",
                        "MaxWall/Job",
                        "yellow",
                        "right",
                        lambda q: get_set_value(
                            get_nested(
                                q, "limits.max.wall_clock.per.job"
                            )
                            or {}
                        ),
                    ),
                    (
                        "max_jobs_per_user",
                        "MaxJobs/User",
                        "blue",
                        "right",
                        lambda q: get_set_value(
                            get_nested(q, "limits.max.jobs.per.user")
                            or {}
                        ),
                    ),
                    (
                        "max_active_jobs_per_user",
                        "MaxActive/User",
                        "blue",
                        "right",
                        lambda q: get_set_value(
                            get_nested(
                                q,
                                "limits.max.jobs.active_jobs.per.user",
                            )
                            or {}
                        ),
                    ),
                    (
                        "max_tres_per_job",
                        "MaxTRES/Job",
                        "cyan",
                        "left",
                        lambda q: format_tres_list(
                            get_nested(q, "limits.max.tres.per.job")
                            or []
                        ),
                    ),
                    (
                        "max_tres_per_user",
                        "MaxTRES/User",
                        "cyan",
                        "left",
                        lambda q: format_tres_list(
                            get_nested(q, "limits.max.tres.per.user")
                            or []
                        ),
                    ),
                    (
                        "max_tres_total",
                        "MaxTRES/Total",
                        "cyan",
                        "left",
                        lambda q: format_tres_list(
                            get_nested(q, "limits.max.tres.total") or []
                        ),
                    ),
                ]

                # Determine which columns have non-default values
                visible_columns = []
                for (
                    col_key,
                    col_name,
                    col_style,
                    col_justify,
                    col_func,
                ) in column_definitions:
                    # Check if any QoS has a non-default value
                    has_value = False
                    for qos in qos_list:
                        value = col_func(qos)
                        # Consider non-default if not empty/"-"
                        if value and value != "-":
                            # Skip default values
                            if (
                                col_key == "usage_factor"
                                and value == "1.0"
                            ):
                                continue
                            if col_key == "priority" and value == "0":
                                continue
                            if (
                                col_key == "preempt_mode"
                                and value == "DISABLED"
                            ):
                                continue
                            has_value = True
                            break

                    # Always show name, id, and description
                    if (
                        col_key in ["name", "id", "description"]
                        or has_value
                    ):
                        visible_columns.append(
                            (col_name, col_style, col_justify, col_func)
                        )

                # Output based on style
                if style == "csv":
                    # Print CSV header
                    headers = [
                        col_name
                        for col_name, _, _, _ in visible_columns
                    ]
                    print(delimiter.join(headers))

                    # Print CSV data rows
                    for qos in qos_list:
                        row_values = [
                            col_func(qos)
                            for _, _, _, col_func in visible_columns
                        ]
                        print(delimiter.join(row_values))
                else:  # pretty style
                    # Create table with dynamic columns
                    row_styles = (
                        ["", "on rgb(30,40,60)"] if zebra else None
                    )
                    table = Table(
                        title="Quality of Service (QoS)",
                        box=SIMPLE_HEAVY,
                        pad_edge=False,
                        padding=(0, 0),
                        row_styles=row_styles,
                    )
                    for (
                        col_name,
                        col_style,
                        col_justify,
                        _,
                    ) in visible_columns:
                        table.add_column(
                            col_name,
                            style=col_style,
                            justify=col_justify,
                            no_wrap=(col_justify == "right"),
                        )

                    # Add rows
                    for qos in qos_list:
                        row_values = [
                            col_func(qos)
                            for _, _, _, col_func in visible_columns
                        ]
                        table.add_row(*row_values)

                    console.print(table)

        except subprocess.CalledProcessError as e:
            console.print(
                f"[red]Failed to show QoS:[/red] {e.stderr or e}"
            )
        except json.JSONDecodeError as e:
            console.print(
                f"[red]Failed to parse JSON output:[/red] {e}"
            )

    @classmethod
    def _prepare_template_data(cls, qos: dict) -> dict:
        """Prepare QoS data for template formatting."""
        result = dict(qos)

        # Helper to extract set/number values
        def get_set_value(obj):
            if isinstance(obj, dict):
                if obj.get("set", False):
                    return obj.get("number")
            return None

        # Flatten common nested values
        result["priority"] = (
            get_set_value(qos.get("priority", {})) or "-"
        )
        result["usage_factor"] = (
            get_set_value(qos.get("usage_factor", {})) or "1.0"
        )
        result["grace_time"] = (
            get_set_value(qos.get("grace_time", {})) or "-"
        )

        # Format flags
        flags = qos.get("flags", [])
        result["flags"] = ",".join(flags) if flags else "-"

        # Format preempt mode
        preempt = qos.get("preempt", {})
        preempt_mode = preempt.get("mode", [])
        result["preempt_mode"] = (
            ",".join(preempt_mode) if preempt_mode else "-"
        )

        # Format limits - extract nested values
        limits = qos.get("limits", {})
        max_limits = limits.get("max", {})

        # Max jobs
        max_jobs = max_limits.get("jobs", {})
        result["max_jobs_per_user"] = (
            get_set_value(max_jobs.get("per", {}).get("user", {}))
            or "-"
        )
        result["max_jobs_active_per_user"] = (
            get_set_value(
                max_limits.get("active_jobs", {})
                .get("per", {})
                .get("user", {})
            )
            or "-"
        )

        # Max wall time
        max_wall = (
            max_limits.get("wall_clock", {})
            .get("per", {})
            .get("job", {})
        )
        result["max_wall"] = get_set_value(max_wall) or "-"

        # Format TRES lists
        def format_tres(tres_list):
            if not tres_list:
                return "-"
            parts = []
            for tres in tres_list:
                if isinstance(tres, dict):
                    name = tres.get("name") or tres.get("type", "")
                    count = tres.get("count", "")
                    if name and count:
                        parts.append(f"{name}={count}")
            return ",".join(parts) if parts else "-"

        tres = max_limits.get("tres", {})
        result["max_tres_per_job"] = format_tres(
            tres.get("per", {}).get("job", [])
        )
        result["max_tres_per_user"] = format_tres(
            tres.get("per", {}).get("user", [])
        )
        result["max_tres_total"] = format_tres(tres.get("total", []))

        return result

    @classmethod
    def generate_autocomplete_options(cls) -> str:
        """Generate bash autocomplete script for QoS options."""
        valid_keys = [opt.lower() for opt in QOS_OPTIONS]
        filter_opts = " ".join(f"{k}=" for k in valid_keys)
        flags_str = " ".join(QOS_FLAGS)
        preempt_modes_str = " ".join(PREEMPT_MODE_VALUES)

        script = f"""
_slurm_cli_qos_autocomplete() {{
    local cmd="$1"
    local pos="$2"

    local cur="${{COMP_WORDS[COMP_CWORD]}}"
    local prev="${{COMP_WORDS[COMP_CWORD-1]}}"
    local name="${{COMP_WORDS[$pos]}}"

    local cached_qos="$(_slurm_cache_qos)"
    local options="{filter_opts}"

    # First argument after 'qos'
    if [[ $name == qos && $prev == qos ]]; then
        case "$cmd" in
            show|delete) _slurm_complete "$options $cached_qos" "$cur" ;;
            create|update) _slurm_complete "$options $cached_qos" "$cur" ;;
        esac
        return
    fi

    # Handle key=value completion
    if _slurm_parse_keyval "$cur" "$prev"; then
        case "$_key" in
            flags)
                _slurm_complete_value "{flags_str}" "$_key" "$_val" "$cur" ;;
            preemptmode)
                _slurm_complete_value "{preempt_modes_str}" "$_key" "$_val" "$cur" ;;
            preempt|name)
                _slurm_complete_value "$cached_qos" "$_key" "$_val" "$cur" ;;
        esac
        return
    fi

    # Complete option names
    case "$cmd" in
        show|delete) _slurm_complete "$options" "$cur" ;;
        create|update) _slurm_complete "$options" "$cur" ;;
    esac
}}
"""  # noqa: E501
        return script
