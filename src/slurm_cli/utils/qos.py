"""Utilities for managing QoS."""

import subprocess
from typing import Any

from .utils import console


class Qos:
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
