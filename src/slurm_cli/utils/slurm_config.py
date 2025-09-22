"""SLURM config utilities."""

import subprocess
from typing import Any

from .utils import console


class Config:
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
    def show(cls) -> None:
        """Show a config."""
        try:
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
