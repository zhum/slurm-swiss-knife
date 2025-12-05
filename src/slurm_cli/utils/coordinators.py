"""Utilities for managing coordinators."""

import subprocess
from typing import Any

from .base_resource import BaseSlurmResource
from .utils import console


class Coordinator(BaseSlurmResource):
    def __init__(self, name: str, **kwargs: Any):
        self.name = name
        self.kwargs = kwargs

    @classmethod
    def create(
        cls,
        name: str,
        verbose: bool = False,
        value: str = None,
        names: tuple = None,
    ) -> None:
        """Create a new coordinator."""
        # console.print(
        # f"Creating coordinator: {name} {value} {names} {kwargs}"
        # )
        if not value and not names:
            console.print(
                f"[red]Coordinator '{name}' creation failed:[/]"
                f"Use slurm-cli create coordinator <account(s)> <user(s)>"
            )
            return
        args = [
            "sacctmgr",
            "add",
            "coordinator",
            f"accounts={name}",
            f"names={value}",
        ]

        try:
            result = subprocess.run(
                args,
                check=True,
                capture_output=True,
                text=True,
            )
            console.print(
                f"[green]Coordinator '{name}' created successfully.[/green]"
            )
            if result.stdout:
                console.print(result.stdout)
        except subprocess.CalledProcessError as e:
            console.print(
                f"[red]Failed to create coordinator '{name}':[/]"
                f"{e.stderr or e}"
            )

    @classmethod
    def update(cls, name: str, **kwargs: Any) -> None:
        """Update a coordinator."""
        console.print(f"Updating coordinator: {name}")

    @classmethod
    def delete(cls, name: str) -> None:
        """Delete a coordinator."""
        console.print(f"Deleting coordinator: {name}")

    @classmethod
    def show(
        cls,
        field: str = None,
        style: str = "pretty",
        force_cache_update: bool = False,
        delimiter: str = ";",
    ) -> None:
        """Show coordinator information."""
        print(
            f"Showing coordinator: {field} {style} {force_cache_update}"
        )
        try:
            if style == "json":
                result = subprocess.run(
                    [
                        "echo",
                        "sacctmgr",
                        "show",
                        "coordinators",
                        "--json",
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                if result.stdout:
                    console.print_json(result.stdout)
            else:  # pretty style
                result = subprocess.run(
                    ["echo", "sacctmgr", "show", "coordinators"],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                if result.stdout:
                    console.print(result.stdout)
        except subprocess.CalledProcessError as e:
            console.print(
                f"[red]Failed to show coordinators:[/red] {e.stderr or e}"
            )
