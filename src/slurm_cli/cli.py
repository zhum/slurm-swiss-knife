#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Main CLI entry point for Slurm CLI.

To enable bash autocompletion for this command:

1. Install the completion script:
   eval "$(_CLICK_COMPLETE=bash_source slurm-cli)"

2. Add the above line to your ~/.bashrc or ~/.bash_profile to make it
   permanent.

3. Restart your shell or run: source ~/.bashrc

Alternatively, you can generate a completion script file:
   _CLICK_COMPLETE=bash_source slurm-cli > \
       ~/.local/share/bash-completion/completions/slurm-cli

Note: This requires Click's completion support which is available in Click \
8.0+.
"""

from enum import Enum
from typing import Dict, List, Any, Optional
import re
import time
import os
import json
import subprocess

import click
from click_aliases import ClickAliasedGroup
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from fast_autocomplete import AutoComplete

from .utils.config import VERBS, ROUTES

# Initialize Rich console for better output
console = Console()

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


def get_resource_choices() -> List[str]:
    routes = ROUTES['get-set']
    if isinstance(routes, dict):
        return list(routes.keys())
    return []


def get_create_resource_choices() -> List[str]:
    routes = ROUTES['create']
    if isinstance(routes, dict):
        return list(routes.keys())
    return []


def create_autocomplete() -> AutoComplete:
    """Create and return an autocomplete instance."""
    words: Dict[str, Dict[str, Any]] = {value: {} for value in VERBS.keys()}
    return AutoComplete(words=words, synonyms=VERBS)


class ResourceType(str, Enum):
    """Enum for available resource types."""
    partitions = "partitions"
    nodes = "nodes"
    jobs = "jobs"
    users = "users"
    qos = "qos"
    accounts = "accounts"
    reservations = "reservations"
    config = "config"
    unknown = "unknown"


class Resource:
    CACHE_TIMEOUT = 60
    cached_nodes_file = "/tmp/slurm_cli_nodes.json"
    cached_partitions_file = "/tmp/slurm_cli_partitions.json"
    cached_jobs_file = "/tmp/slurm_cli_jobs.json"
    cached_users_file = "/tmp/slurm_cli_users.json"
    cached_qos_file = "/tmp/slurm_cli_qos.json"
    cached_accounts_file = "/tmp/slurm_cli_accounts.json"
    cached_reservations_file = "/tmp/slurm_cli_reservations.json"

    @classmethod
    def guess_resource_type(cls, name: str) -> ResourceType:
        """Guess the resource type from the resource name."""
        if re.match(r"^[0-9_]+$", name):
            return ResourceType.jobs
        if cls.cached_resource(name,
                               cls.cached_nodes_file,
                               "scontrol show node --json",
                               ResourceType.nodes):
            return ResourceType.nodes
        if cls.cached_resource(name,
                               cls.cached_partitions_file,
                               "scontrol show partition --json",
                               ResourceType.partitions):
            return ResourceType.partitions
        if cls.cached_resource(name, cls.cached_users_file,
                               "sacctmgr show user --json",
                               ResourceType.users):
            return ResourceType.users
        if cls.cached_resource(name, cls.cached_qos_file,
                               "sacctmgr show qos --json",
                               ResourceType.qos):
            return ResourceType.qos
        if cls.cached_resource(name, cls.cached_accounts_file,
                               "sacctmgr show accounts --json",
                               ResourceType.accounts):
            return ResourceType.accounts
        if cls.cached_resource(name, cls.cached_reservations_file,
                               "scontrol show reservations --json",
                               ResourceType.reservations):
            return ResourceType.reservations
        return ResourceType.unknown

    @classmethod
    def update_cache(cls, file: str, cmd: str) -> Dict[str, Any]:
        raw_data = cls.run_cmd_json("scontrol show node --json")
        data = {node['name']: node for node in raw_data["nodes"]}
        with open(cls.cached_nodes_file, 'w') as f:
            json.dump(data, f)
            os.chmod(cls.cached_nodes_file, 0o600)
        return data

    @classmethod
    def cached_resource(cls, name: str, file: str, cmd: str, resource_type: ResourceType) -> bool:  # noqa: E501
        """Check if the resource is a cached resource."""
        if os.path.exists(file):
            file_mtime = os.path.getmtime(file)
            if time.time() - file_mtime < cls.CACHE_TIMEOUT:
                with open(file, 'r') as f:
                    raw_data = json.load(f)
                data = {resource['name']: resource for resource in raw_data.get(resource_type, [])}  # noqa: E501
                return name in data

        cls.update_cache(file, cmd)
        return name in data

    @classmethod
    def run_cmd_json(cls, cmd: str) -> Dict[str, Any]:
        """Run a command and return the JSON output."""
        result = json.loads(cls.run_cmd(cmd))
        if isinstance(result, dict):
            return result
        return {}

    @classmethod
    def run_cmd(cls, cmd: str) -> str:
        """Run a command and return the output."""
        return subprocess.check_output(cmd, shell=True).decode('utf-8')


@click.group(cls=ClickAliasedGroup)
@click.version_option()
def main() -> None:
    """Slurm Swiss Knife - A CLI tool for Slurm cluster management."""
    pass


def register_commands() -> None:
    """Register all commands with their aliases using click-aliases."""
    # Register commands with aliases (aliases are hidden from help)
    main.add_command(show, name='show', aliases=['s'])
    main.add_command(update, name='update',
                     aliases=['u', 'set', 'modify', 'edit'])
    main.add_command(create, name='create',
                     aliases=['c', 'cr', 'add', 'new'])
    main.add_command(delete, name='delete',
                     aliases=['d', 'del', 'remove', 'rm'])
    main.add_command(autocomplete, name='autocomplete',
                     aliases=['auto', 'a', 'ac', 'autocomplete'])
    main.add_command(list_resources, name='list-resources',
                     aliases=['list', 'l', 'ls', 'resources'])
    main.add_command(version, name='version',
                     aliases=['v', 'ver', 'version'])
    main.add_command(help_command, name='help',
                     aliases=['h', '?'])


@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument('resource',
                type=click.Choice(get_resource_choices()),
                required=False)
@click.argument('field', required=False)
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
def show(resource: Optional[str], field: Optional[str], verbose: bool) -> None:
    """Show information about Slurm resources."""
    if verbose:
        console.print(f"[bold blue]Showing[/bold blue] {resource}")
        if field:
            console.print(f"[bold green]Field:[/bold green] {field}")
    else:
        console.print(f"Showing {resource}")
        if field:
            console.print(f"Field: {field}")


@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument('resource', type=click.Choice(get_resource_choices()))
@click.argument('field')
@click.argument('value')
@click.option('--dry-run', is_flag=True,
              help='Show what would be updated without making changes')
def update(resource: str, field: str, value: str, dry_run: bool) -> None:
    """Update Slurm resource fields."""
    if dry_run:
        console.print(f"[yellow]DRY RUN:[/yellow] Would update "
                      f"{resource}.{field} = {value}")
    else:
        console.print(f"Updating {resource}.{field} = {value}")


@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument('resource', type=click.Choice(get_create_resource_choices()))
@click.option('--name', '-n', help='Name for the new resource')
@click.option('--dry-run', is_flag=True,
              help='Show what would be created without making changes')
def create(resource: str, name: Optional[str], dry_run: bool) -> None:
    """Create new Slurm resources."""
    if dry_run:
        console.print(f"[yellow]DRY RUN:[/yellow] Would create new {resource}")
        if name:
            console.print(f"[yellow]DRY RUN:[/yellow] With name: {name}")
    else:
        console.print(f"Creating new {resource}")
        if name:
            console.print(f"With name: {name}")


@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument('resource', type=click.Choice(get_create_resource_choices()))
@click.option('--name', '-n', help='Name of the resource to delete')
@click.option('--force', '-f', is_flag=True,
              help='Force deletion without confirmation')
@click.option('--dry-run', is_flag=True,
              help='Show what would be deleted without making changes')
def delete(resource: str, name: Optional[str], force: bool,
           dry_run: bool) -> None:
    """Delete Slurm resources."""
    if dry_run:
        console.print(f"[yellow]DRY RUN:[/yellow] Would delete {resource}")
        if name:
            console.print(f"[yellow]DRY RUN:[/yellow] With name: {name}")
    else:
        if not force and not click.confirm(
            f"Are you sure you want to delete {resource}?"
        ):
            console.print("[red]Operation cancelled.[/red]")
            raise click.Abort()

        console.print(f"Deleting {resource}")
        if name:
            console.print(f"With name: {name}")


@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument('word', default='')
@click.option('--max-cost', '-m', default=3,
              help='Maximum edit distance for fuzzy matching')
@click.option('--size', '-s', default=3,
              help='Maximum number of suggestions to return')
def autocomplete(word: str, max_cost: int, size: int) -> None:
    """Test autocomplete functionality."""
    autocomplete_instance = create_autocomplete()

    if word:
        results = autocomplete_instance.search(word=word,
                                               max_cost=max_cost,
                                               size=size)
        suggestions: List[str] = sum(results, [])

        if suggestions:
            table = Table(title=f"Autocomplete results for '{word}'")
            table.add_column("Suggestion", style="cyan")
            table.add_column("Type", style="magenta")

            for suggestion in suggestions:
                table.add_row(suggestion, "command")

            console.print(table)
        else:
            console.print(
                f"[yellow]No suggestions found for '{word}'[/yellow]")
    else:
        console.print(Panel(
            "[bold]Available commands:[/bold]\n"
            "• show - Show information about Slurm resources\n"
            "• update - Update Slurm resource fields\n"
            "• create - Create new Slurm resources\n"
            "• delete - Delete Slurm resources\n"
            "• autocomplete - Test autocomplete functionality\n"
            "• list-resources - List all available resource types",
            title="Slurm Swiss Knife Commands"
        ))


@click.command(context_settings=CONTEXT_SETTINGS)
def list_resources() -> None:
    """List all available resource types and their fields."""
    table = Table(title="Available Slurm Resources")
    table.add_column("Resource Type", style="cyan", no_wrap=True)
    table.add_column("Available Fields", style="green")
    table.add_column("Operations", style="yellow")

    routes = ROUTES['get-set']
    if isinstance(routes, dict):
        for resource_type, fields in routes.items():
            if isinstance(fields, dict):
                field_list = ", ".join(fields.keys()) if fields else "N/A"
            else:
                field_list = "N/A"
            operations: List[str] = []
            if (isinstance(ROUTES['get-set'], dict) and
                    resource_type in ROUTES['get-set']):
                operations.append("get/set")
            if (isinstance(ROUTES['create'], dict) and
                    resource_type in ROUTES['create']):
                operations.append("create")
            if (isinstance(ROUTES['create'], dict) and
                    resource_type in ROUTES['create']):
                operations.append("delete")

            table.add_row(resource_type, field_list, ", ".join(operations))

    console.print(table)


@click.command(context_settings=CONTEXT_SETTINGS)
def version() -> None:
    """Show version information."""
    console.print("[bold blue]Slurm Swiss Knife[/bold blue] v0.1.0")
    console.print("A CLI tool for Slurm cluster management")


@click.command(context_settings=CONTEXT_SETTINGS)
@click.pass_context
def help_command(ctx: click.Context) -> None:
    """Show help information."""
    # Print the help for the main group
    click.echo(ctx.parent.get_help() if ctx.parent else "Help not available")


# Register commands when module is imported
register_commands()


if __name__ == "__main__":
    main()
