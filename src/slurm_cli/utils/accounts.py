"""Utilities for managing accounts."""

import subprocess
from typing import Any

from .utils import console


class Account:
    def __init__(self, name: str, **kwargs: Any):
        self.name = name
        self.kwargs = kwargs

    @classmethod
    def create(cls, name: str, **kwargs: Any) -> None:
        """Create a new account."""
        console.print(f"Creating account: {name}")
        args = ["sacctmgr", "create", "account", name]
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
                f"[green]Account '{name}' created successfully.[/green]"
            )
            if result.stdout:
                console.print(result.stdout)
        except subprocess.CalledProcessError as e:
            console.print(
                f"[red]Failed to create account '{name}':[/red] {e.stderr or e}"
            )

    @classmethod
    def update(cls, name: str, **kwargs: Any) -> None:
        """Update an account."""
        console.print(f"Updating account: {name}")

    @classmethod
    def delete(cls, name: str) -> None:
        """Delete an account."""
        console.print(f"Deleting account: {name}")
