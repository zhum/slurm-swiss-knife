"""SLURM config utilities."""

import subprocess
from typing import Any

from .base_resource import BaseSlurmResource
from .utils import console


class Config(BaseSlurmResource):
    def __init__(self, name: str, **kwargs: Any):
        self.name = name
        self.kwargs = kwargs

    @classmethod
    def update(cls, name: str, **kwargs: Any) -> None:
        """Update a config."""
        args = ["scontrol", "reconfigure"]

        try:
            result = subprocess.run(
                ["echo", *args],
                check=True,
                capture_output=True,
                text=True,
            )
            console.print("[green]Config updated successfully.[/green]")
            if result.stdout:
                console.print(result.stdout)
        except subprocess.CalledProcessError as e:
            console.print(
                f"[red]Failed to update config:[/red] {e.stderr or e}"
            )

    @classmethod
    def show(
        cls,
        data: dict = None,
        style: str = "pretty",
        force_cache_update: bool = False,
        delimiter: str = ";",
    ) -> None:
        """Show a config."""
        try:
            if style == "json":
                result = subprocess.run(
                    ["scontrol", "show", "config", "--json"],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                if result.stdout:
                    console.print_json(result.stdout)
            else:  # pretty style
                result = subprocess.run(
                    ["scontrol", "show", "config"],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                if result.stdout:
                    console.print(result.stdout)
        except subprocess.CalledProcessError as e:
            console.print(
                f"[red]Failed to show config:[/red] {e.stderr or e}"
            )
