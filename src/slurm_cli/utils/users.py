"""Utilities for managing users."""

import subprocess
from typing import Any

from .utils import console


class User:
    def __init__(self, name: str, **kwargs: Any):
        self.name = name
        self.kwargs = kwargs

    @classmethod
    def create(cls, name: str, **kwargs: Any) -> None:
        """Create a new user."""
        console.print(f"Creating user: {name}")
        args = ["sacctmgr", "create", "user", name]
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
                f"[green]User '{name}' created successfully.[/green]"
            )
            if result.stdout:
                console.print(result.stdout)
        except subprocess.CalledProcessError as e:
            console.print(
                f"[red]Failed to create user '{name}':[/red] {e.stderr or e}"
            )

    @classmethod
    def update(cls, name: str, **kwargs: Any) -> None:
        """Update a user."""
        console.print(f"Updating user: {name}")

    @classmethod
    def delete(cls, name: str) -> None:
        """Delete a user."""
        console.print(f"Deleting user: {name}")
