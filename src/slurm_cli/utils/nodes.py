"""Utilities for managing nodes."""

import json
import subprocess
from typing import Any

from .base_resource import BaseSlurmResource
from .utils import console


class Node(BaseSlurmResource):
    def __init__(self, name: str, **kwargs: Any):
        self.name = name
        self.kwargs = kwargs

    @classmethod
    def create(cls, name: str, **kwargs: Any) -> None:
        """Create a new node."""
        console.print(f"Creating node: {name}")
        args = ["scontrol", "create", "node", f"name={name}"]
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
                f"[green]Node '{name}' created successfully.[/green]"
            )
            if result.stdout:
                console.print(result.stdout)
        except subprocess.CalledProcessError as e:
            console.print(
                f"[red]Failed to create node '{name}':[/red] {e.stderr or e}"
            )

    @classmethod
    def update(cls, name: str, **kwargs: Any) -> None:
        """Update a node."""
        console.print(f"Updating node: {name}")

    @classmethod
    def delete(cls, name: str) -> None:
        """Delete a node."""
        console.print(f"Deleting node: {name}")

    @classmethod
    def show(
        cls,
        field: str = None,
        data: dict = None,
        style: str = "pretty",
        force_cache_update: bool = False,
    ) -> None:
        """Show node information."""
        try:
            if style == "json":
                if data:
                    console.print_json(json.dumps(data, indent=4))
                else:
                    result = subprocess.run(
                        ["scontrol", "show", "nodes", "--json"],
                        check=True,
                        capture_output=True,
                        text=True,
                    )
                    if result.stdout:
                        console.print_json(result.stdout)
            else:  # pretty style
                if data:
                    console.print("Node information:")
                    if field:
                        console.print(f"Field: {field}")
                    console.print(json.dumps(data, indent=2))
                else:
                    result = subprocess.run(
                        ["scontrol", "show", "nodes"],
                        check=True,
                        capture_output=True,
                        text=True,
                    )
                    if result.stdout:
                        console.print(result.stdout)
        except subprocess.CalledProcessError as e:
            console.print(
                f"[red]Failed to show nodes:[/red] {e.stderr or e}"
            )
