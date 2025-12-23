"""Utilities for managing reservations."""

import json
import subprocess
from datetime import datetime
from typing import Any, Optional

from rich.markup import escape

from .base_resource import BaseSlurmResource
from .profiles import format_with_template, get_profile_config

# from .resources import Resource
from .utils import console


class Reservation(BaseSlurmResource):
    _WIDTH = None

    # Aliases for argument names (short form -> canonical form)
    arg_aliases = {
        "start": "starttime",
        "end": "endtime",
    }

    @classmethod
    def get_profile_fields(cls) -> dict:
        """Return field names and descriptions for profile templates."""
        return {
            "name": "Reservation name",
            "partition": "Partition name",
            "start_time": "Start time (formatted)",
            "end_time": "End time (formatted)",
            "time_status": "Time status (e.g., 'ends in 5d 3h')",
            "node_count": "Number of nodes",
            "core_count": "Number of cores",
            "node_list": "List of nodes",
            "users": "Allowed users",
            "accounts": "Allowed accounts",
            "flags": "Reservation flags",
            "tres": "TRES specification",
            "max_start_delay": "Max start delay",
        }

    valid_args = {
        "accounts": {
            "type": "list",
            "help": "Comma-separated list of accounts"
            "that are allowed to use this reservation",
        },
        "burstbuffer": {
            "type": "list",
            "help": "Comma-separated list of burst buffer resources"
            "to be reserved",
        },
        "corecnt": {
            "type": "int",
            "help": "Number of cores to be reserved",
        },
        "licenses": {
            "type": "list",
            "help": "Comma-separated list of licenses" "to be reserved",
        },
        "maxstartdelay": {
            "type": "time",
            "help": "Maximum start delay",
        },
        "nodecnt": {
            "type": "int",
            "help": "Number of nodes to be reserved",
        },
        "nodes": {
            "type": "nodes",
            "help": "Comma-separated list of nodes" "to be reserved",
        },
        "starttime": {
            "type": "time",
            "help": "Start time",
        },
        "endtime": {
            "type": "time",
            "help": "End time",
        },
        "duration": {
            "type": "time",
            "help": "Duration",
        },
        "partitionname": {
            "type": "partition",
            "help": "Partition used to reserve nodes from",
        },
        "flags": {
            "type": "list",
            "help": "Comma-separated list of flags"
            "to be reserved. Flags list: ANY_NODES, "
            "DAILY, FLEX, IGNORE_JOBS, HOURLY, LICENSE_ONLY, "
            "MAINT, MAGNETIC, NO_HOLD_JOBS_AFTER, OVERLAP, "
            "PART_NODES, PURGE_COMP, REPLACE, REPLACE_DOWN, "
            "SPEC_NODES, STATIC_ALLOC, TIME_FLOAT, WEEKDAY, "
            "WEEKEND, WEEKLY",
        },
        "features": {
            "type": "list",
            "help": "Comma-separated list of features" "to be reserved",
        },
        "groups": {
            "type": "list",
            "help": "Comma-separated list of groups" "to be reserved",
        },
        "skip": {
            "type": "[yes, no, y, n, 1, 0]",
            "help": "Skip",
        },
        "users": {
            "type": "list",
            "help": "Comma-separated list of users" "to be reserved",
        },
        "tres": {
            "type": "list",
            "help": "Comma-separated list of TRES" "to be reserved",
        },
        "trespernode": {
            "type": "list",
            "help": "Comma-separated list of TRES per node"
            "to be reserved",
        },
    }

    def __init__(self, name: str, **kwargs: Any):
        self.name = name
        self.kwargs = kwargs

    @classmethod
    def max_width(cls) -> int:
        """Get the maximum width of the console."""
        if cls._WIDTH is None:
            cls._WIDTH = console.width
        return cls._WIDTH

    @classmethod
    def create(
        cls, name: str, verbose: bool = False, **kwargs: Any
    ) -> None:
        """Create a new reservation."""
        set = {}
        add = {}
        delete = {}
        if not cls._check_args(kwargs, set, add, delete):
            return
        options = " ".join(
            [f"{key}={value}" for key, value in set.items()]
        )
        if len(add) > 0:
            console.print(
                "[yellow]Warning: Adding options is not supported"
                " for reservations.[/yellow]"
            )
        if len(delete) > 0:
            console.print(
                "[yellow]Warning: Deleting options is not supported"
                " for reservations.[/yellow]"
            )
        if len(set) > 0:
            options += " "
            options += " ".join(
                [f"{key}-={value}" for key, value in delete.items()]
            )
        args = [
            "scontrol",
            "create",
            "reservation",
            f"name={name}",
            options,
        ]

        try:
            result = subprocess.run(
                ["echo", *args],
                check=True,
                capture_output=True,
                text=True,
            )
            if result.stdout:
                console.print(result.stdout)
            if verbose:
                console.print(
                    f"[green]Reservation '{name}' "
                    "created successfully.[/green]"
                )

        except subprocess.CalledProcessError as e:
            console.print(
                f"[red]Failed to create reservation '{name}':[/red]"
                f" {e.stderr or e}"
            )

    @classmethod
    def update(
        cls, name: str, verbose: bool = False, **kwargs: Any
    ) -> None:
        """Update a reservation."""
        set = {}
        add = {}
        delete = {}
        if not cls._check_args(kwargs, set, add, delete):
            return
        options = " ".join(
            [f"{key}={value}" for key, value in set.items()]
        )
        if len(add) > 0:
            options += " "
            options += " ".join(
                [f"{key}+={value}" for key, value in add.items()]
            )
        if len(delete) > 0:
            options += " "
            options += " ".join(
                [f"{key}-={value}" for key, value in delete.items()]
            )
        args = [
            "scontrol",
            "update",
            f"reservationname={name}",
            options,
        ]

        try:
            result = subprocess.run(
                ["echo", *args],
                check=True,
                capture_output=True,
                text=True,
            )
            if result.stdout:
                console.print(result.stdout)
            if verbose:
                console.print(
                    f"[green]Reservation '{name}' "
                    "updated successfully.[/green]"
                )
        except subprocess.CalledProcessError as e:
            console.print(
                f"[red]Failed to update reservation '{name}':[/red]"
                f" {e.stderr or e}"
            )

    @classmethod
    def delete(cls, name: str) -> None:
        """Delete a reservation."""
        args = [
            "scontrol",
            "delete",
            "reservationname={name}",
        ]
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
                f"[green]Reservation '{name}' "
                "deleted successfully.[/green]"
            )
        except subprocess.CalledProcessError as e:
            console.print(
                f"[red]Failed to delete reservation '{name}':[/red]"
                f" {e.stderr or e}"
            )

    @classmethod
    def show(
        cls,
        name: str = None,
        data: dict = None,
        style: str = "pretty",
        delimiter: str = ";",
        zebra: bool = False,
        profile: str = "default",
        profile_str: Optional[str] = None,
    ) -> None:
        """Show reservation information."""
        # Get profile configuration
        _, _, template = get_profile_config(
            profile, "reservations", profile_str
        )
        if not data:
            console.print_json("[red]No data available.[/red]")
            return
        if name and name not in data:
            console.print(f"[red]Reservation '{name}' not found.[/red]")
            return
        try:
            if style == "json":
                if name:
                    console.print_json(json.dumps(data[name], indent=2))
                else:
                    console.print_json(json.dumps(data, indent=2))
            elif style == "csv":
                cls._show_csv(data, name, delimiter)
            elif template:
                # Use template-based output
                if name:
                    res_data = cls._prepare_template_data(
                        name, data[name]
                    )
                    output = format_with_template(
                        template, res_data, resource="reservations"
                    )
                    console.print(output)
                else:
                    for res_name, res_data in data.items():
                        prepared = cls._prepare_template_data(
                            res_name, res_data
                        )
                        output = format_with_template(
                            template, prepared, resource="reservations"
                        )
                        console.print(output)
            else:  # default pretty style
                if name:
                    cls.print_one_pretty(name, data[name])
                else:
                    for res in data.keys():
                        cls.print_one_pretty(res, data[res])
        except subprocess.CalledProcessError as e:
            console.print(
                f"[red]Failed to show reservations:[/red] {e.stderr or e}"
            )

    @classmethod
    def _prepare_template_data(cls, name: str, data: dict) -> dict:
        """Prepare reservation data for template formatting."""
        result = dict(data)
        result["name"] = name

        # Format timestamps
        start_time = cls._get_timestamp(data.get("start_time"))
        end_time = cls._get_timestamp(data.get("end_time"))
        result["start_time"] = (
            cls.tm2str(start_time) if start_time else "-"
        )
        result["end_time"] = cls.tm2str(end_time) if end_time else "-"

        # Calculate deltas
        now = datetime.now().timestamp()
        if start_time > now:
            result[
                "time_status"
            ] = f"starts in {cls.delta2str(start_time - now)}"
        elif end_time > now:
            result[
                "time_status"
            ] = f"ends in {cls.delta2str(end_time - now)}"
        else:
            result["time_status"] = "expired"

        # Format users list
        if "users" in result and isinstance(result["users"], list):
            result["users"] = ",".join(result["users"])

        # Format accounts list
        if "accounts" in result and isinstance(
            result["accounts"], list
        ):
            result["accounts"] = ",".join(result["accounts"])

        return result

    @classmethod
    def _show_csv(
        cls,
        data: dict,
        name: str = None,
        delimiter: str = ";",
    ) -> None:
        """Show reservations in CSV format."""
        # Define columns for CSV output
        columns = [
            "name",
            "partition",
            "start_time",
            "end_time",
            "node_count",
            "core_count",
            "node_list",
            "users",
            "accounts",
            "flags",
            "tres",
        ]

        # Print header
        print(
            delimiter.join(
                col.title().replace("_", " ") for col in columns
            )
        )

        # Filter data if name is specified
        items = {name: data[name]} if name else data

        for res_name, res_data in items.items():
            prepared = cls._prepare_template_data(res_name, res_data)
            row = []
            for col in columns:
                val = prepared.get(col, "")
                if val is None or val == "":
                    val = ""
                elif isinstance(val, list):
                    val = ",".join(str(v) for v in val)
                elif isinstance(val, dict):
                    if val.get("set"):
                        val = str(val.get("number", ""))
                    else:
                        val = ""
                else:
                    val = str(val)
                row.append(val)
            print(delimiter.join(row))

    @classmethod
    def tm2str(cls, tm: int) -> str:
        """Convert time to string."""
        return datetime.fromtimestamp(tm).strftime("%Y-%m-%d %H:%M:%S")

    @classmethod
    def delta2str(cls, delta: int) -> str:
        """Convert delta to string."""
        days = delta // 86400
        hours = (delta % 86400) // 3600
        minutes = (delta % 3600) // 60
        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"

    @classmethod
    def _get_timestamp(cls, value: Any) -> float:
        """Extract timestamp from value (handles dict with set/number)."""
        if isinstance(value, dict):
            if value.get("set"):
                return float(value.get("number", 0))
            return 0.0
        return float(value) if value else 0.0

    @classmethod
    def print_one_pretty(cls, name: str, data: dict) -> None:
        """Print pretty reservation information."""
        if not data:
            console.print("[red]No data available.[/red]")
            return
        end_time = cls._get_timestamp(data["end_time"])
        start_time = cls._get_timestamp(data["start_time"])
        end_delta = end_time - datetime.now().timestamp()
        start_delta = start_time - datetime.now().timestamp()
        if start_delta > 0:
            start_str = f"(in [time]{cls.delta2str(start_delta)}[/])"
            end_str = ""
        elif end_delta > 0:
            start_str = ""
            end_str = f"(in [time]{cls.delta2str(end_delta)}[/])"
        else:
            start_str = ""
            end_str = ""
        console.print("=============================================")
        console.print(
            f"Reservation: [object]{escape(name)}[/] Start/End: "
            f"[time]{cls.tm2str(start_time)}[/]{start_str}"
            f" / [time]{cls.tm2str(end_time)}[/]{end_str}"
        )
        console.print(
            f"Partition: [b blue]{escape(data['partition'])}[/] "
            f"Nodes/CPUs: [b]{data['node_count']}/"
            f"{data['core_count']}"
            f"[/] ([nodes]{data['node_list']}[/])"
        )
        data.pop("node_list", None)
        data.pop("partition", None)
        data.pop("core_count", None)
        data.pop("node_count", None)
        data.pop("start_time", None)
        data.pop("end_time", None)
        data.pop("purge_completed", None)  # WHAT'S THAT FOR???
        watts = data.pop("watts", None)
        if watts and isinstance(watts, dict) and watts.get("set"):
            data["watts"] = (
                f"[time]{watts['number']}[/]"
                if not watts.get("infinite")
                else "[time]INF[/]"
            )
        elif watts and not isinstance(watts, dict):
            data["watts"] = str(watts)
        # Highlight users in pink
        if "users" in data:
            users_val = data["users"]
            if isinstance(users_val, list):
                users_val = ",".join(users_val)
            data["users"] = f"[hot_pink]{users_val}[/hot_pink]"
        cls.print_dict_pretty(data)

    @classmethod
    def generate_autocomplete_options(cls) -> str:
        """
        Generate autocomplete for bash completion.
        Assume we already have entered
        "slurm-cli {new|del|upd|show} reservation"
        and we are trying to autocomplete the next command.

        For each command (new, del, upd, show) generate a list of options
        1. show:
            - name
        2. new:
            a. name is not entered:
                - reservationname
                - list of valid_args keys
            b. name is entered:
                I) option name is not entered:
                    - list of valid_args keys
                II) option name is entered:
                    - list of values,
                      depending of type
                      format: key=value
        3. del:
            - name
        4. upd:
            a. name is not entered:
                - reservationname
                - list of valid_args keys
            b. name is entered:
                I) option name is not entered:
                    - list of valid_args keys
                II) option name is entered:
                    - list of values,
                      depending of type
                      format: key=value
        Output should be part of the autocomplete script
        for bash completion.
        For keys with types nodes, partition, account, qos, user
        use jq utility to extract keys from cache files.
        """

        # Get valid argument keys including aliases
        valid_keys = list(cls.valid_args.keys()) + list(
            cls.arg_aliases.keys()
        )
        # Build types dict including aliases pointing to their canonical types
        valid_types_list = [
            f'[{k}]="{v["type"]}"' for k, v in cls.valid_args.items()
        ]
        # Add alias types (point to same type as canonical)
        for alias, canonical in cls.arg_aliases.items():
            if canonical in cls.valid_args:
                valid_types_list.append(
                    f'[{alias}]="{cls.valid_args[canonical]["type"]}"'
                )
        valid_types = " ".join(valid_types_list)
        options = " ".join(f"{k}=" for k in valid_keys)
        flags = (
            "ANY_NODES DAILY FLEX IGNORE_JOBS HOURLY LICENSE_ONLY MAINT "
            "MAGNETIC NO_HOLD_JOBS_AFTER OVERLAP PART_NODES PURGE_COMP "
            "REPLACE REPLACE_DOWN SPEC_NODES STATIC_ALLOC TIME_FLOAT "
            "WEEKDAY WEEKEND WEEKLY"
        )

        script = f"""
_slurm_cli_reservations_autocomplete() {{
    local cmd="$1"
    local pos="$2"

    local cur="${{COMP_WORDS[COMP_CWORD]}}"
    local prev="${{COMP_WORDS[COMP_CWORD-1]}}"
    local name="${{COMP_WORDS[$pos]}}"

    local cached_reservations="$(_slurm_cache_reservations)"
    local options="{options}"

    # First argument after 'reservations'
    if [[ $name == reservations && $prev == reservations ]]; then
        _slurm_complete "$cached_reservations" "$cur"
        return
    fi

    case "$cmd" in
        show|delete) return ;;
        create|update)
            if _slurm_parse_keyval "$cur" "$prev"; then
                local -A valid_types=({valid_types})
                local type=${{valid_types[$_key]}}
                case "$type" in
                    nodes)
                        _slurm_complete_nodes_value "$_val" "$cur" ;;
                    partition)
                        _slurm_complete_value "$(_slurm_cache_partitions)" "$_key" "$_val" "$cur" ;;
                    account)
                        _slurm_complete_value "$(_slurm_cache_accounts)" "$_key" "$_val" "$cur" ;;
                    int|time) ;;
                    *)
                        case "$_key" in
                            flags)
                                _slurm_complete_value "{flags}" "$_key" "$_val" "$cur" ;;
                            skip)
                                _slurm_complete_value "yes no y n 1 0" "$_key" "$_val" "$cur" ;;
                            state)
                                # Node filter: nodes=state=<state>
                                local states="idle alloc drain down mixed comp"
                                COMPREPLY=($(compgen -W "$states" -- "$_val"))
                                [[ ${{#COMPREPLY[@]}} -gt 0 ]] && COMPREPLY=("${{COMPREPLY[@]/#/nodes=state=}}")
                                ;;
                            partition)
                                # Node filter: nodes=partition=<partition>
                                COMPREPLY=($(compgen -W "$(_slurm_cache_partitions)" -- "$_val"))
                                [[ ${{#COMPREPLY[@]}} -gt 0 ]] && COMPREPLY=("${{COMPREPLY[@]/#/nodes=partition=}}")
                                ;;
                            user)
                                # Node filter: nodes=user=<user>
                                COMPREPLY=($(compgen -W "$(_slurm_cache_users)" -- "$_val"))
                                [[ ${{#COMPREPLY[@]}} -gt 0 ]] && COMPREPLY=("${{COMPREPLY[@]/#/nodes=user=}}")
                                ;;
                            reservation)
                                # Node filter: nodes=reservation=<reservation>
                                COMPREPLY=($(compgen -W "$cached_reservations" -- "$_val"))
                                [[ ${{#COMPREPLY[@]}} -gt 0 ]] && COMPREPLY=("${{COMPREPLY[@]/#/nodes=reservation=}}")
                                ;;
                        esac
                        ;;
                esac
                return
            fi
            _slurm_complete "$options" "$cur"
            ;;
    esac
}}
"""
        return script
