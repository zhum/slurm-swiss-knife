"""Utilities for managing reservations."""

import subprocess
from typing import Any

from .utils import console


class Reservation:
    def __init__(self, name: str, **kwargs: Any):
        self.name = name
        self.kwargs = kwargs

    @classmethod
    def create(cls, name: str, **kwargs: Any) -> None:
        """Create a new reservation."""
        console.print(f"Creating reservation: {name}")
        args = ["scontrol", "create", "reservation", f"name={name}"]
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
                f"[green]Reservation '{name}' created successfully.[/green]"
            )
            if result.stdout:
                console.print(result.stdout)
        except subprocess.CalledProcessError as e:
            console.print(
                f"[red]Failed to create reservation '{name}':[/red] {e.stderr or e}"
            )

    @classmethod
    def update(cls, name: str, **kwargs: Any) -> None:
        """Update a reservation."""
        console.print(f"Updating reservation: {name}")

    @classmethod
    def delete(cls, name: str) -> None:
        """Delete a reservation."""
        console.print(f"Deleting reservation: {name}")
