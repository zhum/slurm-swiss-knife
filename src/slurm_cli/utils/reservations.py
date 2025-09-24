"""Utilities for managing reservations."""

import subprocess
from typing import Any

from .base_resource import BaseSlurmResource
from .utils import console


class Reservation(BaseSlurmResource):

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
        field: str = None,
        style: str = "pretty",
        force_cache_update: bool = False,
    ) -> None:
        """Show reservation information."""
        try:
            if style == "json":
                result = subprocess.run(
                    ["scontrol", "show", "reservations", "--json"],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                if result.stdout:
                    console.print_json(result.stdout)
            else:  # pretty style
                result = subprocess.run(
                    ["scontrol", "show", "reservations"],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                if result.stdout:
                    console.print(result.stdout)
        except subprocess.CalledProcessError as e:
            console.print(
                f"[red]Failed to show reservations:[/red] {e.stderr or e}"
            )
