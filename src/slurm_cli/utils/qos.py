"""Utilities for managing QoS."""

import json
import subprocess
from typing import Any, Optional

from rich.box import SIMPLE_HEAVY
from rich.table import Table

from .base_resource import BaseSlurmResource
from .profiles import format_with_template, get_profile_config
from .utils import console


class Qos(BaseSlurmResource):
    def __init__(self, name: str, **kwargs: Any):
        self.name = name
        self.kwargs = kwargs

    @classmethod
    def create(cls, name: str, **kwargs: Any) -> None:
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
    def update(cls, name: str, **kwargs: Any) -> None:
        """Update a QoS."""
        console.print(f"Updating QoS: {name}")

    @classmethod
    def delete(cls, name: str) -> None:
        """Delete a QoS."""
        console.print(f"Deleting QoS: {name}")

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
        columns_cfg, styles_cfg, template_cfg = get_profile_config(
            profile, "qos", profile_str
        )
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
