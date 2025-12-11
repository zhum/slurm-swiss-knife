"""Utilities for managing users."""

import subprocess
from typing import Any, Optional

from .base_resource import BaseSlurmResource
from .profiles import get_profile_config
from .utils import console


class User(BaseSlurmResource):
    def __init__(self, name: str, **kwargs: Any):
        self.name = name
        self.kwargs = kwargs

    @classmethod
    def get_profile_fields(cls) -> dict:
        """Return field names and descriptions for profile templates."""
        return {
            "name": "Username",
            "default_account": "Default account",
            "admin_level": "Admin level",
        }

    @classmethod
    def create(
        cls, name: str, verbose: bool = False, **kwargs: Any
    ) -> None:
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

    @classmethod
    def show(
        cls,
        name: str = None,
        data: dict = None,
        style: str = "pretty",
        force_cache_update: bool = False,
        delimiter: str = ";",
        profile: str = "default",
        profile_str: Optional[str] = None,
    ) -> None:
        """Show user information."""
        # Get profile configuration (for future enhancement)
        _, _, _ = get_profile_config(profile, "users", profile_str)
        # For backward compatibility, support 'field' parameter name
        field = name
        try:
            if style == "json":
                result = subprocess.run(
                    ["sacctmgr", "show", "users", "--json"],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                if result.stdout:
                    console.print_json(result.stdout)
            else:  # pretty style
                result = subprocess.run(
                    ["sacctmgr", "show", "users"],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                if result.stdout:
                    console.print(result.stdout)
        except subprocess.CalledProcessError as e:
            console.print(
                f"[red]Failed to show users:[/red] {e.stderr or e}"
            )
