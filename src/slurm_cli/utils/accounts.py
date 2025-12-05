"""Utilities for managing accounts."""

import json
import subprocess
from typing import Any

from rich.box import SIMPLE_HEAVY
from rich.table import Table

from .base_resource import BaseSlurmResource
from .utils import console


class Account(BaseSlurmResource):
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
            error_msg = e.stderr or e
            console.print(
                f"[red]Failed to create account '{name}':[/red] {error_msg}"
            )

    @classmethod
    def update(cls, name: str, **kwargs: Any) -> None:
        """Update an account."""
        console.print(f"Updating account: {name}")

    @classmethod
    def delete(cls, name: str) -> None:
        """Delete an account."""
        console.print(f"Deleting account: {name}")

    @classmethod
    def show(
        cls,
        field: str = None,
        style: str = "pretty",
        force_cache_update: bool = False,
        delimiter: str = ";",
        zebra: bool = False,
    ) -> None:
        """Show account information.

        Args:
            field: Optional account name to filter by
            style: Output style ("pretty", "json", or "csv")
            force_cache_update: Whether to force cache update (unused)
            delimiter: Delimiter for CSV output (default: ";")
            zebra: Use zebra striping for table rows (default: False)
        """
        try:
            # Always get JSON output from sacctmgr
            result = subprocess.run(
                ["sacctmgr", "show", "accounts", "--json"],
                check=True,
                capture_output=True,
                text=True,
            )

            if not result.stdout:
                console.print("[yellow]No accounts found.[/yellow]")
                return

            # Parse JSON data
            data = json.loads(result.stdout)
            accounts = data.get("accounts", [])

            # Filter by field (account name) if specified
            if field:
                accounts = [
                    acc for acc in accounts if acc.get("name") == field
                ]
                if not accounts:
                    console.print(
                        f"[yellow]Account '{field}' not found.[/yellow]"
                    )
                    return

            if style == "json":
                # Print filtered JSON
                filtered_data = {"accounts": accounts}
                console.print_json(json.dumps(filtered_data, indent=2))
            elif style == "csv":
                # Print CSV format
                # Header
                headers = [
                    "Name",
                    "Description",
                    "Organization",
                    "Coordinators",
                ]
                print(delimiter.join(headers))

                # Data rows
                for account in accounts:
                    name = account.get("name", "")
                    description = account.get("description", "")
                    organization = account.get("organization", "")
                    coordinators = account.get("coordinators", [])

                    # Format coordinators list
                    coord_str = (
                        ",".join(coordinators) if coordinators else ""
                    )

                    row = [name, description, organization, coord_str]
                    print(delimiter.join(row))
            else:  # pretty style
                # Create a rich table
                row_styles = ["", "on rgb(30,40,60)"] if zebra else None
                table = Table(
                    title="Accounts",
                    box=SIMPLE_HEAVY,
                    pad_edge=False,
                    padding=(0, 0),
                    row_styles=row_styles,
                )
                table.add_column("Name", style="cyan", no_wrap=True)
                table.add_column("Description", style="white")
                table.add_column("Organization", style="green")
                table.add_column("Coordinators", style="yellow")

                for account in accounts:
                    name = account.get("name", "")
                    description = account.get("description", "")
                    organization = account.get("organization", "")
                    coordinators = account.get("coordinators", [])

                    # Format coordinators list
                    coord_str = (
                        ", ".join(coordinators) if coordinators else "-"
                    )

                    table.add_row(
                        name, description, organization, coord_str
                    )

                console.print(table)

        except subprocess.CalledProcessError as e:
            error_msg = e.stderr or e
            console.print(
                f"[red]Failed to show accounts:[/red] {error_msg}"
            )
        except json.JSONDecodeError as e:
            console.print(
                f"[red]Failed to parse JSON output:[/red] {e}"
            )
