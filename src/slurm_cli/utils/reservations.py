"""Utilities for managing reservations."""

import json
import subprocess
from datetime import datetime
from typing import Any

from rich.markup import escape

from .base_resource import BaseSlurmResource
from .utils import console


class Reservation(BaseSlurmResource):

    _WIDTH = None
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
        cls, name: str = None, data: dict = None, style: str = "pretty"
    ) -> None:
        """Show reservation information."""
        if not data:
            console.print_json("[red]No data available.[/red]")
            return
        try:
            if name:
                if style == "json":
                    console.print_json(json.dumps(data[name], indent=2))
                else:  # pretty style
                    cls.print_one_pretty(name, data[name])
            else:
                if style == "json":
                    console.print_json(json.dumps(data, indent=2))
                else:  # pretty style
                    for res in data.keys():
                        cls.print_one_pretty(res, data[res])
        except subprocess.CalledProcessError as e:
            console.print(
                f"[red]Failed to show reservations:[/red] {e.stderr or e}"
            )

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
    def print_one_pretty(cls, name: str, data: dict) -> None:
        """Print pretty reservation information."""
        if not data:
            console.print("[red]No data available.[/red]")
            return
        end_delta = data["end_time"] - datetime.now().timestamp()
        start_delta = data["start_time"] - datetime.now().timestamp()
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
            f"[time]{cls.tm2str(data['start_time'])}[/]{start_str}"
            f" / [time]{cls.tm2str(data['end_time'])}[/]{end_str}"
        )
        console.print(
            f"Partition: [b blue]{escape(data['partition'])}[/] "
            f"Nodes/CPUs: [b]{data['node_count']}/"
            f"{data['core_count']}"
            f"[/] ([nodes]{data['node_list']}[/])"
        )
        data.pop("node_list")
        data.pop("partition")
        data.pop("core_count")
        data.pop("node_count")
        data.pop("start_time")
        data.pop("end_time")
        data.pop("purge_completed")  # WHAT'S THAT FOR???
        watts = data.pop("watts")
        if watts["set"]:
            data["watts"] = (
                f"[time]{watts['number']}[/]"
                if not watts["infinite"]
                else "[time]INF[/]"
            )
        cls.print_dict_pretty(data)
