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

Note: This requires Click's completion support
which is available in Click 8.0+.
"""

from typing import Any, Dict, List, Optional, Tuple

import click
from fast_autocomplete import AutoComplete
from rich.panel import Panel
from rich.table import Table

from .utils.accounts import Account
from .utils.config import ROUTES, VERBS
from .utils.coordinators import Coordinator
from .utils.nodes import Node
from .utils.partitions import Partition
from .utils.qos import Qos
from .utils.reservations import Reservation
from .utils.resources import Resource
from .utils.slurm_config import Config
from .utils.users import User
from .utils.utils import console

# , Union


CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])


def get_resource_choices() -> List[str]:
    routes = ROUTES["get-set"]
    if isinstance(routes, dict):
        choices = list(routes.keys())
        # Add aliases
        aliases = {
            "partitions": ["part", "parts"],
            "nodes": ["node"],
            "users": ["user"],
            "qos": ["qoses"],
            "accounts": ["acc", "account"],
            "reservations": ["res", "reservation"],
            "coordinators": ["coord", "coordinator"],
        }
        for resource, alias_list in aliases.items():
            if resource in choices:
                choices.extend(alias_list)
        return choices
    return []


def get_create_resource_choices() -> List[str]:
    routes = ROUTES["create"]
    if isinstance(routes, dict):
        choices = list(routes.keys())
        # Add aliases
        aliases = {
            "partitions": ["part", "parts"],
            "nodes": ["node"],
            "users": ["user"],
            "qos": ["qoses"],
            "accounts": ["acc", "account"],
            "reservations": ["res", "reservation"],
            "coordinators": ["coord", "coordinator"],
        }
        for resource, alias_list in aliases.items():
            if resource in choices:
                choices.extend(alias_list)
        return choices
    return []


def resolve_resource_alias(resource: str) -> str:
    """Resolve resource alias to canonical name."""
    aliases = {
        "part": "partitions",
        "parts": "partitions",
        "node": "nodes",
        "user": "users",
        "qoses": "qos",
        "acc": "accounts",
        "account": "accounts",
        "res": "reservations",
        "reservation": "reservations",
        "coord": "coordinators",
        "coordinator": "coordinators",
    }
    return aliases.get(resource, resource)


def get_output_style(ctx: click.Context) -> str:
    """Get the output style from context."""
    return ctx.obj.get("style", "pretty")


def get_force_cache_update(ctx: click.Context) -> bool:
    """Get the force cache update flag from context."""
    return ctx.obj.get("force_cache_update", False)


def create_autocomplete() -> AutoComplete:
    """Create and return an autocomplete instance."""
    words: Dict[str, Dict[str, Any]] = {
        value: {} for value in VERBS.keys()
    }
    return AutoComplete(words=words, synonyms=VERBS)


def ensure_resource_name(
    resource: str,
    field: str = None,
    force_update: bool = False,
) -> Tuple[str, str, dict]:
    """
    Ensure the resource name is a valid resource name.
    Return the resource type, field, and data.
    """
    if resource[:4] == "part":
        data = Resource.cached_resource(
            "partitions",
            force_update,
        )
        return resource, field, data
    elif resource[:4] == "node":
        data = Resource.cached_resource(
            "nodes",
            force_update,
        )
        return resource, field, data
    elif resource[:4] == "user":
        data = Resource.cached_resource(
            "users",
            force_update,
        )
        return resource, field, data
    elif resource[:3] == "qos":
        data = Resource.cached_resource(
            "qos",
            force_update,
        )
        return resource, field, data
    elif resource[:3] == "acc":
        data = Resource.cached_resource(
            "accounts",
            force_update,
        )
        return resource, field, data
    elif resource[:3] == "res":
        data = Resource.cached_resource(
            "reservations",
            force_update,
        )
        return resource, field, data
    elif resource[:5] == "coord":
        data = Resource.cached_resource(
            "coordinators",
            force_update,
        )
        return resource, field, data
    elif resource[:4] == "conf":
        data = Resource.cached_resource(
            "config",
            force_update,
        )
        return resource, field, data
    else:
        resource_type, data = Resource.guess_resource_type(
            resource, force_update
        )
        if resource_type.value:
            return resource_type.value, resource, data
        else:
            return None, resource, data


def show_command_help_with_resources(
    ctx: click.Context, param: click.Parameter, value: bool
) -> None:
    """Custom help callback that shows command help plus resource list."""
    if not value or ctx.resilient_parsing:
        return

    # Show the standard command help
    click.echo(ctx.get_help())

    # Add the resource list
    console.print("\n[bold]Available Slurm Resources:[/bold]")
    table = Table()
    table.add_column("Resource Type", style="cyan", no_wrap=True)
    table.add_column("Available Fields", style="green")
    table.add_column("Operations", style="yellow")

    routes = ROUTES["get-set"]
    if isinstance(routes, dict):
        for resource_type, fields in routes.items():
            if isinstance(fields, dict):
                field_list = (
                    ", ".join(fields.keys()) if fields else "N/A"
                )
            else:
                field_list = "N/A"
            operations: List[str] = []
            if (
                isinstance(ROUTES["get-set"], dict)
                and resource_type in ROUTES["get-set"]
            ):
                operations.append("get/set")
            if (
                isinstance(ROUTES["create"], dict)
                and resource_type in ROUTES["create"]
            ):
                operations.append("create")
            if (
                isinstance(ROUTES["create"], dict)
                and resource_type in ROUTES["create"]
            ):
                operations.append("delete")

            table.add_row(
                resource_type, field_list, ", ".join(operations)
            )

    console.print(table)
    ctx.exit()


@click.group(context_settings=CONTEXT_SETTINGS)
@click.version_option()
@click.help_option("-h", "--help")
@click.option(
    "--style",
    type=click.Choice(["pretty", "json"]),
    default="pretty",
    help="Output style: pretty (default) or json",
)
@click.option(
    "--pretty",
    "-p",
    is_flag=True,
    help="Use pretty output format (equivalent to --style pretty)",
)
@click.option(
    "--json",
    "-j",
    is_flag=True,
    help="Use JSON output format (equivalent to --style json)",
)
@click.option(
    "--force-cache-update",
    "-f",
    is_flag=True,
    help="Force update of resource cache, bypassing cache timeout",
)
@click.option(
    "--cache-timeout",
    "-t",
    type=int,
    default=60,
    help="Cache timeout in seconds (default: 60)",
)
@click.pass_context
def main(
    ctx: click.Context,
    style: str,
    pretty: bool,
    json: bool,
    force_cache_update: bool,
    cache_timeout: int,
) -> None:
    """Slurm Swiss Knife - A CLI tool for Slurm cluster management."""
    # Handle convenience flags
    if pretty:
        style = "pretty"
    elif json:
        style = "json"

    # Store style and cache update flag in context
    # for subcommands to access
    ctx.ensure_object(dict)
    ctx.obj["style"] = style
    ctx.obj["force_cache_update"] = force_cache_update

    # Set the cache timeout in the Resource class
    Resource.set_cache_timeout(cache_timeout)


class CustomGroup(click.Group):
    """Custom Click group that hides alias commands from help."""

    def format_commands(self, ctx, formatter):
        """Custom command formatter that filters out aliases."""
        commands = []
        main_command_names = {
            "show",
            "update",
            "create",
            "delete",
            "list-resources",
            "autocomplete",
            "help",
            "version",
        }

        for subcommand in self.list_commands(ctx):
            cmd = self.get_command(ctx, subcommand)
            # Skip commands that are aliases (not main command names)
            if cmd and subcommand not in main_command_names:
                continue
            elif cmd:
                commands.append((subcommand, cmd))

        if commands:
            with formatter.section("Commands"):
                formatter.write_dl(
                    [
                        (name, cmd.help or cmd.short_help or "")
                        for name, cmd in commands
                    ]
                )


# Change the main group to use our custom group class
main.__class__ = CustomGroup


def register_commands() -> None:
    """Register all commands."""
    # Clear existing commands to avoid duplicates
    main.commands.clear()

    # Register main commands only
    # Aliases will be handled by modifying the help text to show them inline
    main.add_command(show, name="show")
    main.add_command(update, name="update")
    main.add_command(create, name="create")
    main.add_command(delete, name="delete")
    main.add_command(list_resources, name="list-resources")
    main.add_command(autocomplete, name="autocomplete")
    main.add_command(help, name="help")
    main.add_command(version, name="version")

    # Register aliases as separate commands but hide them from help
    # Show aliases
    main.add_command(show, name="sh")
    main.add_command(show, name="s")

    # Update aliases
    main.add_command(update, name="u")
    main.add_command(update, name="upd")
    main.add_command(update, name="edit")
    main.add_command(update, name="change")
    main.add_command(update, name="ch")
    main.add_command(update, name="set")
    main.add_command(update, name="mod")
    main.add_command(update, name="modify")

    # Create aliases
    main.add_command(create, name="c")
    main.add_command(create, name="new")
    main.add_command(create, name="add")

    # Delete aliases
    main.add_command(delete, name="del")
    main.add_command(delete, name="d")
    main.add_command(delete, name="remove")
    main.add_command(delete, name="rem")
    main.add_command(delete, name="rm")

    # List-resources aliases
    main.add_command(list_resources, name="list")
    main.add_command(list_resources, name="ls")
    main.add_command(list_resources, name="l")

    # Modify help text to show aliases inline
    show.help = (
        "Show information about Slurm resources (aliases: sh, s)"
    )
    update.help = (
        "Update Slurm resource fields "
        "(aliases: u, upd, edit, change, ch, set, mod, modify)"
    )
    create.help = "Create Slurm resources (aliases: c, new, add)"
    delete.help = (
        "Delete Slurm resources (aliases: del, d, remove, rem, rm)"
    )
    list_resources.help = (
        "List available Slurm resources (aliases: list, ls, l)"
    )


# Show command
@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument(
    "resource",
    type=str,  # lick.Choice(get_resource_choices()),
    required=True,
)
@click.argument("field", required=False)
@click.option(
    "--verbose", "-v", is_flag=True, help="Enable verbose output"
)
@click.option(
    "--help",
    "-h",
    is_flag=True,
    is_eager=True,
    callback=show_command_help_with_resources,
    help="Show this message and exit.",
)
@click.pass_context
def show(
    ctx: click.Context,
    resource: Optional[str],
    field: Optional[str],
    verbose: bool,
    **kwargs,
) -> None:
    """Show information about Slurm resources (aliases: sh, s)."""
    style = get_output_style(ctx)
    force_cache_update = get_force_cache_update(ctx)
    canonical_resource, field, data = ensure_resource_name(
        resource, field, force_cache_update
    )
    # TODO: eliminate double checking of cached resource
    if canonical_resource[:4] == "conf":
        Config.show(data=data, style=style)
    elif canonical_resource[:3] == "res":
        if field:
            Reservation.show(name=field, data=data, style=style)
        else:
            Reservation.show(data=data, style=style)
    elif canonical_resource[:4] == "part":
        if field:
            Partition.show(name=field, data=data, style=style)
        else:
            Partition.show(data=data, style=style)
    elif canonical_resource[:4] == "node":
        if field:
            Node.show(name=field, data=data, style=style, verbose=verbose)
        else:
            Node.show(data=data, style=style)
    elif canonical_resource[:4] == "user":
        if field:
            User.show(name=field, data=data, style=style)
        else:
            User.show(data=data, style=style)
    elif canonical_resource[:3] == "qos":
        if field:
            Qos.show(name=field, data=data, style=style)
        else:
            Qos.show(data=data, style=style)
    elif canonical_resource[:3] == "acc":
        if field:
            Account.show(name=field, data=data, style=style)
        else:
            Account.show(data=data, style=style)
    elif canonical_resource[:5] == "coord":
        if field:
            Coordinator.show(name=field, data=data, style=style)
        else:
            Coordinator.show(data=data, style=style)
    else:
        console.print(f"[red]Resource '{resource}' not found.[/red]")


# Update command
@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument("resource", type=click.Choice(get_resource_choices()))
@click.argument("field")
@click.argument("value")
@click.argument("names", nargs=-1, required=False)
@click.option(
    "--verbose", "-v", is_flag=True, help="Enable verbose output"
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be updated without making changes",
)
@click.option(
    "--help",
    "-h",
    is_flag=True,
    is_eager=True,
    callback=show_command_help_with_resources,
    help="Show this message and exit.",
)
def update(
    resource: str,
    field: str,
    value: str,
    names: tuple,
    verbose: bool,
    dry_run: bool,
    **kwargs,
) -> None:
    """Update Slurm resource fields (aliases: u, edit, mod, modify)."""
    # Resolve resource alias to canonical name
    canonical_resource = resolve_resource_alias(resource)

    # Parse additional arguments into key-value pairs
    update_options = {}
    if names:
        for arg in names:
            if "=" in arg:
                # Handle key=value format
                key, value_part = arg.split("=", 1)
                update_options[key] = value_part
            else:
                # Treat as a simple value
                update_options[arg] = None

    # Build the update message
    if names:
        additional_args = " ".join(f"'{arg}'" for arg in names)
        if dry_run:
            console.print(
                f"[yellow]DRY RUN:[/yellow] Would update "
                f"{canonical_resource} {field} '{value}' {additional_args}"
            )
        else:
            if verbose:
                console.print(
                    f"Updating {canonical_resource} {field} '{value}' "
                    f"{additional_args}"
                )

            if canonical_resource[:4] == "part":
                Partition.update(field, verbose, **update_options)
            elif canonical_resource[:4] == "node":
                Node.update(field, verbose, **update_options)
            elif canonical_resource[:4] == "user":
                User.update(field, verbose, **update_options)
            elif canonical_resource[:3] == "qos":
                Qos.update(field, verbose, **update_options)
            elif canonical_resource[:3] == "acc":
                Account.update(field, verbose, **update_options)
            elif canonical_resource[:3] == "res":
                Reservation.update(field, verbose, **update_options)
            elif canonical_resource[:5] == "coord":
                Coordinator.update(field, verbose, **update_options)
            elif canonical_resource[:4] == "conf":
                Config.update(field, verbose, **update_options)
            else:
                console.print(
                    f"[red]Resource '{canonical_resource}' not found.[/red]"
                )
    else:
        # If no additional arguments, show general update message
        if dry_run:
            console.print(
                f"[yellow]DRY RUN:[/yellow] Would update "
                f"{canonical_resource} {field} '{value}'"
            )
        else:
            console.print(
                f"Updating {canonical_resource} {field} '{value}'"
            )


# # Update command
# @click.command(context_settings=CONTEXT_SETTINGS)
# @click.argument("resource", type=click.Choice(get_resource_choices()))
# @click.argument("field")
# @click.argument("value")
# @click.argument("names", nargs=-1, required=False)
# @click.option(
#     "--verbose", "-v", is_flag=True, help="Enable verbose output"
# )
# @click.option(
#     "--dry-run",
#     is_flag=True,
#     help="Show what would be updated without making changes",
# )
# @click.option(
#     "--help",
#     "-h",
#     is_flag=True,
#     is_eager=True,
#     callback=show_command_help_with_resources,
#     help="Show this message and exit.",
# )
# # Create command aliases
# def create(
#     resource: str,
#     field: str,
#     value: str,
#     names: tuple,
#     verbose: bool,
#     dry_run: bool,
#     **kwargs,
# ) -> None:
#     """Update Slurm resource fields (alias for update)."""
#     # Resolve resource alias to canonical name
#     canonical_resource = resolve_resource_alias(resource)

#     # Parse additional arguments into key-value pairs
#     update_options = {}
#     if names:
#         for arg in names:
#             if "=" in arg:
#                 # Handle key=value format
#                 key, value_part = arg.split("=", 1)
#                 update_options[key] = value_part
#             else:
#                 # Treat as a simple value
#                 update_options[arg] = None

#     # Build the update message
#     if names:
#         additional_args = " ".join(f"'{arg}'" for arg in names)
#         if dry_run:
#             console.print(
#                 f"[yellow]DRY RUN:[/yellow] Would update "
#                 f"{canonical_resource} {field} '{value}' {additional_args}"
#             )
#         else:
#             if verbose:
#                 console.print(
#                     f"Updating {canonical_resource} {field} '{value}' "
#                     f"{additional_args}"
#                 )

#             if canonical_resource[:4] == "part":
#                 Partition.update(field, verbose, **update_options)
#             elif canonical_resource[:4] == "node":
#                 Node.update(field, verbose, **update_options)
#             elif canonical_resource[:4] == "user":
#                 User.update(field, verbose, **update_options)
#             elif canonical_resource[:3] == "qos":
#                 Qos.update(field, verbose, **update_options)
#             elif canonical_resource[:3] == "acc":
#                 Account.update(field, verbose, **update_options)
#             elif canonical_resource[:3] == "res":
#                 Reservation.update(field, verbose, **update_options)
#             elif canonical_resource[:5] == "coord":
#                 Coordinator.update(field, verbose, **update_options)
#             elif canonical_resource[:4] == "conf":
#                 Config.update(field, verbose, **update_options)
#             else:
#                 console.print(
#                     f"[red]Resource '{canonical_resource}' not found.[/red]"
#                 )
#     else:
#         # If no additional arguments, show general update message
#         if dry_run:
#             console.print(
#                 f"[yellow]DRY RUN:[/yellow] Would update "
#                 f"{canonical_resource} {field} '{value}'"
#             )
#         else:
#             console.print(
#                 f"Updating {canonical_resource} {field} '{value}'"
#             )


@click.command(context_settings=CONTEXT_SETTINGS, name="modify")
@click.argument("resource", type=click.Choice(get_resource_choices()))
@click.argument("field")
@click.argument("value")
@click.argument("names", nargs=-1, required=False)
@click.option(
    "--verbose", "-v", is_flag=True, help="Enable verbose output"
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be updated without making changes",
)
@click.option(
    "--help",
    "-h",
    is_flag=True,
    is_eager=True,
    callback=show_command_help_with_resources,
    help="Show this message and exit.",
)
def update_alias_modify(
    resource: str,
    field: str,
    value: str,
    names: tuple,
    verbose: bool,
    dry_run: bool,
    **kwargs,
) -> None:
    """Update Slurm resource fields (alias for update)."""
    # Resolve resource alias to canonical name
    canonical_resource = resolve_resource_alias(resource)

    # Parse additional arguments into key-value pairs
    update_options = {}
    if names:
        for arg in names:
            if "=" in arg:
                # Handle key=value format
                key, value_part = arg.split("=", 1)
                update_options[key] = value_part
            else:
                # Treat as a simple value
                update_options[arg] = None

    # Build the update message
    if names:
        additional_args = " ".join(f"'{arg}'" for arg in names)
        if dry_run:
            console.print(
                f"[yellow]DRY RUN:[/yellow] Would update "
                f"{canonical_resource} {field} '{value}' {additional_args}"
            )
        else:
            if verbose:
                console.print(
                    f"Updating {canonical_resource} {field} '{value}' "
                    f"{additional_args}"
                )

            if canonical_resource[:4] == "part":
                Partition.update(field, verbose, **update_options)
            elif canonical_resource[:4] == "node":
                Node.update(field, verbose, **update_options)
            elif canonical_resource[:4] == "user":
                User.update(field, verbose, **update_options)
            elif canonical_resource[:3] == "qos":
                Qos.update(field, verbose, **update_options)
            elif canonical_resource[:3] == "acc":
                Account.update(field, verbose, **update_options)
            elif canonical_resource[:3] == "res":
                Reservation.update(field, verbose, **update_options)
            elif canonical_resource[:5] == "coord":
                Coordinator.update(field, verbose, **update_options)
            elif canonical_resource[:4] == "conf":
                Config.update(field, verbose, **update_options)
            else:
                console.print(
                    f"[red]Resource '{canonical_resource}' not found.[/red]"
                )
    else:
        # If no additional arguments, show general update message
        if dry_run:
            console.print(
                f"[yellow]DRY RUN:[/yellow] Would update "
                f"{canonical_resource} {field} '{value}'"
            )
        else:
            console.print(
                f"Updating {canonical_resource} {field} '{value}'"
            )


# Create command group with resource subcommands
@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument("resource", type=click.Choice(get_resource_choices()))
@click.argument("field")
@click.argument("value")
@click.argument("names", nargs=-1, required=False)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be created without making changes",
)
@click.option(
    "--verbose", "-v", is_flag=True, help="Enable verbose output"
)
@click.option(
    "--help",
    "-h",
    is_flag=True,
    is_eager=True,
    callback=show_command_help_with_resources,
    help="Show this message and exit.",
)
def create(
    resource: str,
    field: str,
    value: str,
    names: tuple,
    verbose: bool,
    dry_run: bool,
    **kwargs,
) -> None:
    """Create Slurm resource fields (aliases: c, new, add)."""
    # Resolve resource alias to canonical name
    canonical_resource = resolve_resource_alias(resource)

    # Parse additional arguments into key-value pairs
    create_options = {}
    if names:
        for arg in names:
            if "=" in arg:
                # Handle key=value format
                key, value_part = arg.split("=", 1)
                create_options[key] = value_part
            else:
                # Treat as a simple value
                create_options[arg] = None

    if names:
        additional_args = " ".join(f"'{arg}'" for arg in names)
    else:
        additional_args = None

    if dry_run:
        console.print(
            f"[yellow]DRY RUN:[/yellow] Would create "
            f"{canonical_resource} {field} '{value}' {additional_args}"
        )
    else:
        if verbose:
            console.print(
                f"Creating {canonical_resource} {field} '{value}' "
                f"{additional_args}"
            )

        if canonical_resource[:4] == "part":
            Partition.create(field, verbose, **create_options)
        elif canonical_resource[:4] == "node":
            Node.create(field, verbose, **create_options)
        elif canonical_resource[:4] == "user":
            User.create(field, verbose, **create_options)
        elif canonical_resource[:3] == "qos":
            Qos.create(field, verbose, **create_options)
        elif canonical_resource[:3] == "acc":
            Account.create(field, verbose, **create_options)
        elif canonical_resource[:3] == "res":
            Reservation.create(field, verbose, **create_options)
        elif canonical_resource[:5] == "coord":
            Coordinator.create(field, verbose, **create_options)
        else:
            console.print(
                f"[red]Resource '{canonical_resource}' not found.[/red]"
            )


# Create command aliases
@click.command(context_settings=CONTEXT_SETTINGS, name="c")
@click.argument(
    "resource", type=click.Choice(get_create_resource_choices())
)
@click.argument("field")
@click.argument("value")
@click.argument("names", nargs=-1, required=False)
@click.option(
    "--verbose", "-v", is_flag=True, help="Enable verbose output"
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be created without making changes",
)
@click.option(
    "--help",
    "-h",
    is_flag=True,
    is_eager=True,
    callback=show_command_help_with_resources,
    help="Show this message and exit.",
)
def create_alias_c(
    resource: str,
    field: str,
    value: str,
    names: tuple,
    verbose: bool,
    dry_run: bool,
    **kwargs,
) -> None:
    """Create Slurm resource fields (alias for create)."""
    # Resolve resource alias to canonical name
    canonical_resource = resolve_resource_alias(resource)

    # Parse additional arguments into key-value pairs
    create_options = {}
    if names:
        for arg in names:
            if "=" in arg:
                # Handle key=value format
                key, value_part = arg.split("=", 1)
                create_options[key] = value_part
            else:
                # Treat as a simple value
                create_options[arg] = None

    if names:
        additional_args = " ".join(f"'{arg}'" for arg in names)
    else:
        additional_args = None

    if dry_run:
        console.print(
            f"[yellow]DRY RUN:[/yellow] Would create "
            f"{canonical_resource} {field} '{value}' {additional_args}"
        )
    else:
        if verbose:
            console.print(
                f"Creating {canonical_resource} {field} '{value}' "
                f"{additional_args}"
            )

        if canonical_resource[:4] == "part":
            Partition.create(field, verbose, **create_options)
        elif canonical_resource[:4] == "node":
            Node.create(field, verbose, **create_options)
        elif canonical_resource[:4] == "user":
            User.create(field, verbose, **create_options)
        elif canonical_resource[:3] == "qos":
            Qos.create(field, verbose, **create_options)
        elif canonical_resource[:3] == "acc":
            Account.create(field, verbose, **create_options)
        elif canonical_resource[:3] == "res":
            Reservation.create(field, verbose, **create_options)
        elif canonical_resource[:5] == "coord":
            Coordinator.create(field, verbose, **create_options)
        else:
            console.print(
                f"[red]Resource '{canonical_resource}' not found.[/red]"
            )


@click.command(context_settings=CONTEXT_SETTINGS, name="new")
@click.argument(
    "resource", type=click.Choice(get_create_resource_choices())
)
@click.argument("field")
@click.argument("value")
@click.argument("names", nargs=-1, required=False)
@click.option(
    "--verbose", "-v", is_flag=True, help="Enable verbose output"
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be created without making changes",
)
@click.option(
    "--help",
    "-h",
    is_flag=True,
    is_eager=True,
    callback=show_command_help_with_resources,
    help="Show this message and exit.",
)
def create_alias_new(
    resource: str,
    field: str,
    value: str,
    names: tuple,
    verbose: bool,
    dry_run: bool,
    **kwargs,
) -> None:
    """Create Slurm resource fields (alias for create)."""
    # Resolve resource alias to canonical name
    canonical_resource = resolve_resource_alias(resource)

    # Parse additional arguments into key-value pairs
    create_options = {}
    if names:
        for arg in names:
            if "=" in arg:
                # Handle key=value format
                key, value_part = arg.split("=", 1)
                create_options[key] = value_part
            else:
                # Treat as a simple value
                create_options[arg] = None

    if names:
        additional_args = " ".join(f"'{arg}'" for arg in names)
    else:
        additional_args = None

    if dry_run:
        console.print(
            f"[yellow]DRY RUN:[/yellow] Would create "
            f"{canonical_resource} {field} '{value}' {additional_args}"
        )
    else:
        if verbose:
            console.print(
                f"Creating {canonical_resource} {field} '{value}' "
                f"{additional_args}"
            )

        if canonical_resource[:4] == "part":
            Partition.create(field, verbose, **create_options)
        elif canonical_resource[:4] == "node":
            Node.create(field, verbose, **create_options)
        elif canonical_resource[:4] == "user":
            User.create(field, verbose, **create_options)
        elif canonical_resource[:3] == "qos":
            Qos.create(field, verbose, **create_options)
        elif canonical_resource[:3] == "acc":
            Account.create(field, verbose, **create_options)
        elif canonical_resource[:3] == "res":
            Reservation.create(field, verbose, **create_options)
        elif canonical_resource[:5] == "coord":
            Coordinator.create(field, verbose, **create_options)
        else:
            console.print(
                f"[red]Resource '{canonical_resource}' not found.[/red]"
            )


@click.command(context_settings=CONTEXT_SETTINGS, name="add")
@click.argument(
    "resource", type=click.Choice(get_create_resource_choices())
)
@click.argument("field")
@click.argument("value")
@click.argument("names", nargs=-1, required=False)
@click.option(
    "--verbose", "-v", is_flag=True, help="Enable verbose output"
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be created without making changes",
)
@click.option(
    "--help",
    "-h",
    is_flag=True,
    is_eager=True,
    callback=show_command_help_with_resources,
    help="Show this message and exit.",
)
def create_alias_add(
    resource: str,
    field: str,
    value: str,
    names: tuple,
    verbose: bool,
    dry_run: bool,
    **kwargs,
) -> None:
    """Create Slurm resource fields (alias for create)."""
    # Resolve resource alias to canonical name
    canonical_resource = resolve_resource_alias(resource)

    # Parse additional arguments into key-value pairs
    create_options = {}
    if names:
        for arg in names:
            if "=" in arg:
                # Handle key=value format
                key, value_part = arg.split("=", 1)
                create_options[key] = value_part
            else:
                # Treat as a simple value
                create_options[arg] = None

    if names:
        additional_args = " ".join(f"'{arg}'" for arg in names)
    else:
        additional_args = None

    if dry_run:
        console.print(
            f"[yellow]DRY RUN:[/yellow] Would create "
            f"{canonical_resource} {field} '{value}' {additional_args}"
        )
    else:
        if verbose:
            console.print(
                f"Creating {canonical_resource} {field} '{value}' "
                f"{additional_args}"
            )

        if canonical_resource[:4] == "part":
            Partition.create(field, verbose, **create_options)
        elif canonical_resource[:4] == "node":
            Node.create(field, verbose, **create_options)
        elif canonical_resource[:4] == "user":
            User.create(field, verbose, **create_options)
        elif canonical_resource[:3] == "qos":
            Qos.create(field, verbose, **create_options)
        elif canonical_resource[:3] == "acc":
            Account.create(field, verbose, **create_options)
        elif canonical_resource[:3] == "res":
            Reservation.create(field, verbose, **create_options)
        elif canonical_resource[:5] == "coord":
            Coordinator.create(field, verbose, **create_options)
        else:
            console.print(
                f"[red]Resource '{canonical_resource}' not found.[/red]"
            )


@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument(
    "resource", type=click.Choice(get_create_resource_choices())
)
@click.argument("names", nargs=-1, required=False)
@click.option(
    "--name",
    "-n",
    help="Name of the resource to delete (alternative to positional argument)",
)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="Force deletion without confirmation",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be deleted without making changes",
)
@click.option(
    "--verbose", "-v", is_flag=True, help="Enable verbose output"
)
@click.option(
    "--help",
    "-h",
    is_flag=True,
    is_eager=True,
    callback=show_command_help_with_resources,
    help="Show this message and exit.",
)
def delete(
    resource: str,
    names: tuple,
    name: Optional[str],
    force: bool,
    dry_run: bool,
    verbose: bool,
    **kwargs,
) -> None:  # noqa: E501
    """Delete Slurm resources (aliases: del, d, remove, rem, rm)."""
    # Resolve resource alias to canonical name
    canonical_resource = resolve_resource_alias(resource)

    # Handle multiple names - prioritize positional names over --name option
    if names:
        resource_names = names
    elif name:
        resource_names = [name]
    else:
        resource_names = [None]

    for resource_name in resource_names:
        if dry_run:
            if resource_name:
                console.print(
                    "[yellow]DRY RUN:[/yellow] "
                    f"Would delete {canonical_resource} '{resource_name}'"
                )
            else:
                console.print(
                    "[yellow]DRY RUN:[/yellow] "
                    f"Would delete {canonical_resource}"
                )
    else:
        if not force and not click.confirm(
            f"Are you sure you want to delete {canonical_resource}"
            + (f" '{resource_name}'" if resource_name else "")
            + "?"
        ):
            console.print("[red]Operation cancelled.[/red]")
            raise click.Abort()

        if resource_name:
            if verbose:
                console.print(
                    f"Deleting {canonical_resource} '{resource_name}'"
                )
            else:
                console.print(
                    f"Deleting {canonical_resource} '{resource_name}'"
                )
            console.print(
                f"Deleting {canonical_resource} '{resource_name}'"
            )
        else:
            console.print(f"Deleting {canonical_resource}")


# Delete command aliases
@click.command(context_settings=CONTEXT_SETTINGS, name="del")
@click.argument("resource", type=click.Choice(get_resource_choices()))
@click.argument("names", nargs=-1, required=False)
@click.option(
    "--name",
    "-n",
    help="Name of the resource to delete (alternative to positional argument)",
)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="Force deletion without confirmation",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be deleted without making changes",
)
@click.option(
    "--verbose", "-v", is_flag=True, help="Enable verbose output"
)
@click.option(
    "--help",
    "-h",
    is_flag=True,
    is_eager=True,
    callback=show_command_help_with_resources,
    help="Show this message and exit.",
)
def delete_alias_del(
    resource: str,
    names: tuple,
    name: Optional[str],
    force: bool,
    dry_run: bool,
    verbose: bool,
    **kwargs,
) -> None:
    """Delete Slurm resources (alias for delete)."""
    # Resolve resource alias to canonical name
    canonical_resource = resolve_resource_alias(resource)

    # Handle multiple names - prioritize positional names over --name option
    if names:
        resource_names = names
    elif name:
        resource_names = [name]
    else:
        resource_names = [None]

    for resource_name in resource_names:
        if dry_run:
            if resource_name:
                console.print(
                    "[yellow]DRY RUN:[/yellow] "
                    f"Would delete {canonical_resource} '{resource_name}'"
                )
            else:
                console.print(
                    "[yellow]DRY RUN:[/yellow] "
                    f"Would delete {canonical_resource}"
                )
        else:
            if not force and not click.confirm(
                f"Are you sure you want to delete {canonical_resource}"
                + (f" '{resource_name}'" if resource_name else "")
                + "?"
            ):
                console.print("[red]Operation cancelled.[/red]")
                raise click.Abort()

            if resource_name:
                if verbose:
                    console.print(
                        f"Deleting {canonical_resource} '{resource_name}'"
                    )
                else:
                    console.print(
                        f"Deleting {canonical_resource} '{resource_name}'"
                    )
                console.print(
                    f"Deleting {canonical_resource} '{resource_name}'"
                )
            else:
                console.print(f"Deleting {canonical_resource}")


@click.command(context_settings=CONTEXT_SETTINGS, name="d")
@click.argument("resource", type=click.Choice(get_resource_choices()))
@click.argument("names", nargs=-1, required=False)
@click.option(
    "--name",
    "-n",
    help="Name of the resource to delete (alternative to positional argument)",
)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="Force deletion without confirmation",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be deleted without making changes",
)
@click.option(
    "--verbose", "-v", is_flag=True, help="Enable verbose output"
)
@click.option(
    "--help",
    "-h",
    is_flag=True,
    is_eager=True,
    callback=show_command_help_with_resources,
    help="Show this message and exit.",
)
def delete_alias_d(
    resource: str,
    names: tuple,
    name: Optional[str],
    force: bool,
    dry_run: bool,
    verbose: bool,
    **kwargs,
) -> None:
    """Delete Slurm resources (alias for delete)."""
    # Resolve resource alias to canonical name
    canonical_resource = resolve_resource_alias(resource)

    # Handle multiple names - prioritize positional names over --name option
    if names:
        resource_names = names
    elif name:
        resource_names = [name]
    else:
        resource_names = [None]

    for resource_name in resource_names:
        if dry_run:
            if resource_name:
                console.print(
                    "[yellow]DRY RUN:[/yellow] "
                    f"Would delete {canonical_resource} '{resource_name}'"
                )
            else:
                console.print(
                    "[yellow]DRY RUN:[/yellow] "
                    f"Would delete {canonical_resource}"
                )
        else:
            if not force and not click.confirm(
                f"Are you sure you want to delete {canonical_resource}"
                + (f" '{resource_name}'" if resource_name else "")
                + "?"
            ):
                console.print("[red]Operation cancelled.[/red]")
                raise click.Abort()

            if resource_name:
                if verbose:
                    console.print(
                        f"Deleting {canonical_resource} '{resource_name}'"
                    )
                else:
                    console.print(
                        f"Deleting {canonical_resource} '{resource_name}'"
                    )
                console.print(
                    f"Deleting {canonical_resource} '{resource_name}'"
                )
            else:
                console.print(f"Deleting {canonical_resource}")


@click.command(context_settings=CONTEXT_SETTINGS, name="remove")
@click.argument("resource", type=click.Choice(get_resource_choices()))
@click.argument("names", nargs=-1, required=False)
@click.option(
    "--name",
    "-n",
    help="Name of the resource to delete (alternative to positional argument)",
)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="Force deletion without confirmation",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be deleted without making changes",
)
@click.option(
    "--verbose", "-v", is_flag=True, help="Enable verbose output"
)
@click.option(
    "--help",
    "-h",
    is_flag=True,
    is_eager=True,
    callback=show_command_help_with_resources,
    help="Show this message and exit.",
)
def delete_alias_remove(
    resource: str,
    names: tuple,
    name: Optional[str],
    force: bool,
    dry_run: bool,
    verbose: bool,
    **kwargs,
) -> None:
    """Delete Slurm resources (alias for delete)."""
    # Resolve resource alias to canonical name
    canonical_resource = resolve_resource_alias(resource)

    # Handle multiple names - prioritize positional names over --name option
    if names:
        resource_names = names
    elif name:
        resource_names = [name]
    else:
        resource_names = [None]

    for resource_name in resource_names:
        if dry_run:
            if resource_name:
                console.print(
                    "[yellow]DRY RUN:[/yellow] "
                    f"Would delete {canonical_resource} '{resource_name}'"
                )
            else:
                console.print(
                    "[yellow]DRY RUN:[/yellow] "
                    f"Would delete {canonical_resource}"
                )
        else:
            if not force and not click.confirm(
                f"Are you sure you want to delete {canonical_resource}"
                + (f" '{resource_name}'" if resource_name else "")
                + "?"
            ):
                console.print("[red]Operation cancelled.[/red]")
                raise click.Abort()

            if resource_name:
                if verbose:
                    console.print(
                        f"Deleting {canonical_resource} '{resource_name}'"
                    )
                else:
                    console.print(
                        f"Deleting {canonical_resource} '{resource_name}'"
                    )
                console.print(
                    f"Deleting {canonical_resource} '{resource_name}'"
                )
            else:
                console.print(f"Deleting {canonical_resource}")


@click.command(context_settings=CONTEXT_SETTINGS, name="rem")
@click.argument("resource", type=click.Choice(get_resource_choices()))
@click.argument("names", nargs=-1, required=False)
@click.option(
    "--name",
    "-n",
    help="Name of the resource to delete (alternative to positional argument)",
)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="Force deletion without confirmation",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be deleted without making changes",
)
@click.option(
    "--verbose", "-v", is_flag=True, help="Enable verbose output"
)
@click.option(
    "--help",
    "-h",
    is_flag=True,
    is_eager=True,
    callback=show_command_help_with_resources,
    help="Show this message and exit.",
)
def delete_alias_rem(
    resource: str,
    names: tuple,
    name: Optional[str],
    force: bool,
    dry_run: bool,
    verbose: bool,
    **kwargs,
) -> None:
    """Delete Slurm resources (alias for delete)."""
    # Resolve resource alias to canonical name
    canonical_resource = resolve_resource_alias(resource)

    # Handle multiple names - prioritize positional names over --name option
    if names:
        resource_names = names
    elif name:
        resource_names = [name]
    else:
        resource_names = [None]

    for resource_name in resource_names:
        if dry_run:
            if resource_name:
                console.print(
                    "[yellow]DRY RUN:[/yellow] "
                    f"Would delete {canonical_resource} '{resource_name}'"
                )
            else:
                console.print(
                    "[yellow]DRY RUN:[/yellow] "
                    f"Would delete {canonical_resource}"
                )
        else:
            if not force and not click.confirm(
                f"Are you sure you want to delete {canonical_resource}"
                + (f" '{resource_name}'" if resource_name else "")
                + "?"
            ):
                console.print("[red]Operation cancelled.[/red]")
                raise click.Abort()

            if resource_name:
                if verbose:
                    console.print(
                        f"Deleting {canonical_resource} '{resource_name}'"
                    )
                else:
                    console.print(
                        f"Deleting {canonical_resource} '{resource_name}'"
                    )
                console.print(
                    f"Deleting {canonical_resource} '{resource_name}'"
                )
            else:
                console.print(f"Deleting {canonical_resource}")


@click.command(context_settings=CONTEXT_SETTINGS, name="rm")
@click.argument("resource", type=click.Choice(get_resource_choices()))
@click.argument("names", nargs=-1, required=False)
@click.option(
    "--name",
    "-n",
    help="Name of the resource to delete (alternative to positional argument)",
)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="Force deletion without confirmation",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be deleted without making changes",
)
@click.option(
    "--verbose", "-v", is_flag=True, help="Enable verbose output"
)
@click.option(
    "--help",
    "-h",
    is_flag=True,
    is_eager=True,
    callback=show_command_help_with_resources,
    help="Show this message and exit.",
)
def delete_alias_rm(
    resource: str,
    names: tuple,
    name: Optional[str],
    force: bool,
    dry_run: bool,
    verbose: bool,
    **kwargs,
) -> None:
    """Delete Slurm resources (alias for delete)."""
    # Resolve resource alias to canonical name
    canonical_resource = resolve_resource_alias(resource)

    # Handle multiple names - prioritize positional names over --name option
    if names:
        resource_names = names
    elif name:
        resource_names = [name]
    else:
        resource_names = [None]

    for resource_name in resource_names:
        if dry_run:
            if resource_name:
                console.print(
                    "[yellow]DRY RUN:[/yellow] "
                    f"Would delete {canonical_resource} '{resource_name}'"
                )
            else:
                console.print(
                    "[yellow]DRY RUN:[/yellow] "
                    f"Would delete {canonical_resource}"
                )
        else:
            if not force and not click.confirm(
                f"Are you sure you want to delete {canonical_resource}"
                + (f" '{resource_name}'" if resource_name else "")
                + "?"
            ):
                console.print("[red]Operation cancelled.[/red]")
                raise click.Abort()

            if resource_name:
                if verbose:
                    console.print(
                        f"Deleting {canonical_resource} '{resource_name}'"
                    )
                else:
                    console.print(
                        f"Deleting {canonical_resource} '{resource_name}'"
                    )
                console.print(
                    f"Deleting {canonical_resource} '{resource_name}'"
                )
            else:
                console.print(f"Deleting {canonical_resource}")


@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument("word", default="")
@click.option(
    "--max-cost",
    "-m",
    default=3,
    help="Maximum edit distance for fuzzy matching",
)
@click.option(
    "--size",
    "-s",
    default=3,
    help="Maximum number of suggestions to return",
)
def autocomplete(word: str, max_cost: int, size: int) -> None:
    """Test autocomplete functionality."""
    autocomplete_instance = create_autocomplete()

    if word:
        results = autocomplete_instance.search(
            word=word,
            max_cost=max_cost,
            size=size,
        )
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
                f"[yellow]No suggestions found for '{word}'[/yellow]"
            )  # noqa: E501
    else:
        console.print(
            "[yellow]Please provide a word to search for suggestions.[/yellow]"
        )


@click.command(context_settings=CONTEXT_SETTINGS)
def list_resources() -> None:
    """List all available resource types and their fields
    (aliases: list, ls, l)."""
    table = Table(title="Available Slurm Resources")
    table.add_column("Resource Type", style="cyan", no_wrap=True)
    table.add_column("Available Fields", style="green")
    table.add_column("Operations", style="yellow")

    routes = ROUTES["get-set"]
    if isinstance(routes, dict):
        for resource_type, fields in routes.items():
            if isinstance(fields, dict):
                field_list = (
                    ", ".join(fields.keys()) if fields else "N/A"
                )
            else:
                field_list = "N/A"
            operations: List[str] = []
            if (
                isinstance(ROUTES["get-set"], dict)
                and resource_type in ROUTES["get-set"]
            ):
                operations.append("get/set")
            if (
                isinstance(ROUTES["create"], dict)
                and resource_type in ROUTES["create"]
            ):
                operations.append("create")
            if (
                isinstance(ROUTES["create"], dict)
                and resource_type in ROUTES["create"]
            ):
                operations.append("delete")

            table.add_row(
                resource_type, field_list, ", ".join(operations)
            )

    console.print(table)


# List-resources command aliases
@click.command(context_settings=CONTEXT_SETTINGS, name="list")
def list_resources_alias_list() -> None:
    """List all available resource types and their fields
    (alias for list-resources)."""
    table = Table(title="Available Slurm Resources")
    table.add_column("Resource Type", style="cyan", no_wrap=True)
    table.add_column("Available Fields", style="green")
    table.add_column("Operations", style="yellow")

    routes = ROUTES["get-set"]
    if isinstance(routes, dict):
        for resource_type, fields in routes.items():
            if isinstance(fields, dict):
                field_list = (
                    ", ".join(fields.keys()) if fields else "N/A"
                )
            else:
                field_list = "N/A"
            operations: List[str] = []
            if (
                isinstance(ROUTES["get-set"], dict)
                and resource_type in ROUTES["get-set"]
            ):
                operations.append("get/set")
            if (
                isinstance(ROUTES["create"], dict)
                and resource_type in ROUTES["create"]
            ):
                operations.append("create")
            if (
                isinstance(ROUTES["create"], dict)
                and resource_type in ROUTES["create"]
            ):
                operations.append("delete")

            table.add_row(
                resource_type, field_list, ", ".join(operations)
            )

    console.print(table)


@click.command(context_settings=CONTEXT_SETTINGS, name="ls")
def list_resources_alias_ls() -> None:
    """List all available resource types and their fields
    (alias for list-resources)."""
    table = Table(title="Available Slurm Resources")
    table.add_column("Resource Type", style="cyan", no_wrap=True)
    table.add_column("Available Fields", style="green")
    table.add_column("Operations", style="yellow")

    routes = ROUTES["get-set"]
    if isinstance(routes, dict):
        for resource_type, fields in routes.items():
            if isinstance(fields, dict):
                field_list = (
                    ", ".join(fields.keys()) if fields else "N/A"
                )
            else:
                field_list = "N/A"
            operations: List[str] = []
            if (
                isinstance(ROUTES["get-set"], dict)
                and resource_type in ROUTES["get-set"]
            ):
                operations.append("get/set")
            if (
                isinstance(ROUTES["create"], dict)
                and resource_type in ROUTES["create"]
            ):
                operations.append("create")
            if (
                isinstance(ROUTES["create"], dict)
                and resource_type in ROUTES["create"]
            ):
                operations.append("delete")

            table.add_row(
                resource_type, field_list, ", ".join(operations)
            )

    console.print(table)


@click.command(context_settings=CONTEXT_SETTINGS, name="l")
def list_resources_alias_l() -> None:
    """List all available resource types and their fields
    (alias for list-resources)."""
    table = Table(title="Available Slurm Resources")
    table.add_column("Resource Type", style="cyan", no_wrap=True)
    table.add_column("Available Fields", style="green")
    table.add_column("Operations", style="yellow")

    routes = ROUTES["get-set"]
    if isinstance(routes, dict):
        for resource_type, fields in routes.items():
            if isinstance(fields, dict):
                field_list = (
                    ", ".join(fields.keys()) if fields else "N/A"
                )
            else:
                field_list = "N/A"
            operations: List[str] = []
            if (
                isinstance(ROUTES["get-set"], dict)
                and resource_type in ROUTES["get-set"]
            ):
                operations.append("get/set")
            if (
                isinstance(ROUTES["create"], dict)
                and resource_type in ROUTES["create"]
            ):
                operations.append("create")
            if (
                isinstance(ROUTES["create"], dict)
                and resource_type in ROUTES["create"]
            ):
                operations.append("delete")

            table.add_row(
                resource_type, field_list, ", ".join(operations)
            )

    console.print(table)


@click.command(context_settings=CONTEXT_SETTINGS)
def version() -> None:
    """Show version information."""
    console.print("[bold blue]Slurm Swiss Knife[/bold blue] v0.1.0")
    console.print("A CLI tool for Slurm cluster management")


@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument("word", required=False)
def help(word: Optional[str] = None) -> None:
    """Show help information and available resources."""
    if word:
        # Use autocomplete to find suggestions
        autocomplete_instance = create_autocomplete()
        results = autocomplete_instance.search(
            word=word,
            max_cost=3,
            size=10,
        )
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
                f"[yellow]No suggestions found for '{word}'[/yellow]"
            )  # noqa: E501
    else:
        # Show available commands
        console.print(
            Panel(
                "[bold]Available commands:[/bold]\n"
                "• show - Show information about Slurm resources\n"
                "• update - Update Slurm resource fields\n"
                "• create - Create new Slurm resources\n"
                "• delete - Delete Slurm resources\n"
                "• autocomplete - Test autocomplete functionality\n"
                "• list-resources - List all available resource types",
                title="Slurm Swiss Knife Commands",
            )
        )
        # Show available resources
        console.print("\n[bold]Available Slurm Resources:[/bold]")
        table = Table()
        table.add_column("Resource Type", style="cyan", no_wrap=True)
        table.add_column("Available Fields", style="green")
        table.add_column("Operations", style="yellow")

        routes = ROUTES["get-set"]
        if isinstance(routes, dict):
            for resource_type, fields in routes.items():
                if isinstance(fields, dict):
                    field_list = (
                        ", ".join(fields.keys()) if fields else "N/A"
                    )
                else:
                    field_list = "N/A"
                operations: List[str] = []
                if (
                    isinstance(ROUTES["get-set"], dict)
                    and resource_type in ROUTES["get-set"]
                ):
                    operations.append("get/set")
                if (
                    isinstance(ROUTES["create"], dict)
                    and resource_type in ROUTES["create"]
                ):
                    operations.append("create")
                if (
                    isinstance(ROUTES["create"], dict)
                    and resource_type in ROUTES["create"]
                ):
                    operations.append("delete")

                table.add_row(
                    resource_type, field_list, ", ".join(operations)
                )

        console.print(table)


# Register commands when module is imported
register_commands()


if __name__ == "__main__":
    main()
