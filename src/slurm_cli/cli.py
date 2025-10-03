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

CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])
RESOURCES_ALIASES = {
    "partitions": ["part", "parts"],
    "nodes": ["node"],
    "users": ["user"],
    "qos": ["q"],
    "accounts": ["acc", "account"],
    "reservations": ["res", "reservation"],
    "coordinators": ["coord", "coordinator"],
}


def get_resource_choices() -> List[str]:
    routes = ROUTES["get-set"]
    if isinstance(routes, dict):
        choices = list(routes.keys())
        # Add aliases
        for resource, alias_list in RESOURCES_ALIASES.items():
            if resource in choices:
                choices.extend(alias_list)
        return list(sorted(choices))
    return []


def get_show_resource_choices() -> List[str]:
    ret = get_resource_choices()
    ret.extend(
        [
            "conf[ig]",
            "prob[lems]",
            "stat[s]",
            "assoc[iations]",
            "dump[s]",
            "ev[ents]",
            "lic[enses]",
            "reso[urces]",
            "bad[s]",
            "r[unawayjobs]",
            "tra[nsactions]",
            "tr[es]",
            "ar[chive]",
        ]
    )
    return ret


def resolve_resource_alias(resource: str) -> str:
    """Resolve resource alias to canonical name."""
    for orig, alias_list in RESOURCES_ALIASES.items():
        if orig in alias_list:
            return orig
    return resource


# def resolve_command_alias(command: str) -> str:
#     """Resolve command alias to canonical name."""
#     for orig, alias_list in COMMANDS_ALIASES.items():
#         if orig in alias_list:
#             return orig
#     return command


def get_output_style(ctx: click.Context) -> str:
    """Get the output style from context."""
    return ctx.obj.get("style", "pretty")


def get_force_update(ctx: click.Context) -> bool:
    """Get the force update flag from context."""
    return ctx.obj.get("force_update", False)


def print_help(command: str, ctx: click.Context) -> None:
    """Print help for a command."""
    if command[:12] == "create coord":
        click.echo(
            "Create a coordinator(s).\n"
            "Usage: slurm-cli create coordinator <account(s)> <user(s)>"
        )
    elif command[:12] == "update coord":
        click.echo(
            "Update a coordinator(s).\n"
            "Usage: slurm-cli update coordinator <account(s)> <user(s)>"
        )
    elif command[:12] == "delete coord":
        click.echo(
            "Delete a coordinator(s).\n"
            "Usage: slurm-cli delete coordinator <account(s)> <user(s)>"
        )
    else:
        click.echo(f"Unknown command: {command}")
    ctx.exit()


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
    Return the resource type, field, and cached resource data.
    """
    if resource[:4] == "prob":
        return "problems", field, []
    elif resource[:4] == "stat":
        return "stats", field, []
    elif resource[:4] == "assoc":
        return "associations", field, []
    elif resource[:4] == "dump":
        return "dump", field, []
    elif resource[:2] == "ev":
        return "events", field, []
    elif resource[:3] == "lic" or resource[:4] == "reso":
        return "licenses", field, []
    elif resource[:3] == "bad" or resource[:3] == "runa":
        return "runawayjobs", field, []
    elif resource[:3] == "tra":
        return "transactions", field, []
    elif resource[:2] == "tr":
        return "tres", field, []
    elif resource[:2] == "ar":
        return "archive", field, []
    elif resource[:5] == "coord":  # !
        return "coordinators", field, []
    elif resource[:1] == "j":
        data = Resource.cached_resource(
            "jobs",
            force_update,
        )
        return resource, field, data
    elif resource[:4] == "node":
        data = Resource.cached_resource(
            "nodes",
            force_update,
        )
        return resource, field, data
    elif resource[:4] == "part":
        data = Resource.cached_resource(
            "partitions",
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
        if resource_type:
            return resource_type, resource, data
        else:
            return None, resource, data


def show_command_help(
    ctx: click.Context, param: click.Parameter, value: bool
) -> None:
    """Custom help callback that shows command help plus resource list."""
    if not value or ctx.resilient_parsing:
        return

    # Show the standard command help
    click.echo(ctx.get_help())


def show_command_help_with_resources(
    # ctx: click.Context, param: click.Parameter, value: bool
) -> None:
    """Custom help callback that shows command help plus resource list."""
    # if not value or ctx.resilient_parsing:
    #     return

    # Show the standard command help
    # click.echo(ctx.get_help())

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
                operations.append("get, mod")
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
        for field in [
            "problems",
            "stats",
            "events",
            "runawayjobs",
            "transactions",
        ]:
            table.add_row(field, "N/A", "get")
        for field in [
            "dump",
            "licenses",
            "associations",
            "runawayjobs (bad)",
            "transactions",
            "tres",
            "archive",
        ]:
            table.add_row(field, "N/A", "get")
    console.print(table)
    # ctx.exit()


# main section
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
    "--force-update",
    "-f",
    is_flag=True,
    help="Force update of SLURM data, bypassing cache timeout",
)
@click.option(
    "--cache-timeout",
    "-t",
    type=int,
    default=60,
    help="SLURM cache timeout in seconds (default: 60)",
)
@click.pass_context
def main(
    ctx: click.Context,
    style: str,
    pretty: bool,
    json: bool,
    force_update: bool,
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
    ctx.obj["force_update"] = force_update

    # Set the cache timeout in the Resource class
    Resource.set_cache_timeout(cache_timeout)


class CustomGroup(click.Group):
    """Custom Click group that hides alias commands from help
    and supports prefix matching."""

    def get_command(self, ctx, cmd_name):
        """Override to support prefix matching for commands."""
        # First try exact match (including aliases)
        rv = super().get_command(ctx, cmd_name)
        if rv is not None:
            return rv

        # Try prefix matching on main commands only
        main_commands = {
            "show": ["show", "get"],
            "create": ["new", "add", "create"],
            "update": ["edit", "change", "modify", "update"],
            "delete": ["delete", "remove", "rm"],
            "list-resources": ["ls", "list"],
            "autocomplete": ["autocomplete"],
            "help": ["help"],
            "version": ["version"]
        }
        matches = [
            (cmd, alias) for cmd, aliases in main_commands.items()
            for alias in aliases
            if alias.startswith(cmd_name)
        ]

        if len(matches) == 1:
            return super().get_command(ctx, matches[0][0])
        elif len(matches) > 1:
            ctx.fail(
                f"Ambiguous command: {cmd_name}. "
                f"Could be: {', '.join([f'{alias}' for _, alias in matches])}")

        return None

    def format_commands(self, ctx, formatter):
        """Custom command formatter that filters out aliases."""
        commands = []
        main_command_names = {
            "show", "get",
            "update", "edit", "change", "modify",
            "create", "new", "add",
            "delete", "remove", "rm",
            "list-resources", "ls",
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

    # for command, aliases in COMMANDS_ALIASES.items():
    #     command = command.replace("-", "_")
    #     for alias in aliases:
    #         main.add_command(globals()[command], name=alias)

    # Modify help text to show aliases inline
    show.help = (
        "Show information about Slurm resources (aliases: get)"
    )
    update.help = (
        "Update Slurm resource fields "
        "(aliases: edit, change, modify)"
    )
    create.help = "Create Slurm resources (aliases: new, add)"
    delete.help = (
        "Delete Slurm resources (aliases: remove, rm)"
    )
    list_resources.help = (
        "List available Slurm resources (aliases: ls)"
    )
    version.help = "Show version information"
    # Show version information (aliases: ver, v)"
    help.help = "Show help information"


# Show command
@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument(
    "resource",
    type=click.Choice(get_show_resource_choices()),
    required=False,
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
    callback=show_command_help,
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
    if not resource:
        show_command_help(ctx, None, True)
        return

    style = get_output_style(ctx)
    force_update = get_force_update(ctx)
    canonical_resource, field, data = ensure_resource_name(
        resource, field, force_update
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
            Node.show(
                name=field, data=data, style=style, verbose=verbose
            )
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
            Coordinator.show(field=field, style=style)
        else:
            Coordinator.show(style=style)
    else:
        console.print(f"[red]Resource '{resource}' not found.[/red]")


# Update command
@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument(
    "resource",
    type=click.Choice(get_resource_choices()),
    required=False,
)
@click.argument("field", required=False)
@click.argument("value", required=False)
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
    callback=show_command_help,
    help="Show this message and exit.",
)
@click.pass_context
def update(
    ctx: click.Context,
    resource: str,
    field: str,
    value: str,
    names: tuple,
    verbose: bool,
    dry_run: bool,
    **kwargs,
) -> None:
    """Update Slurm resource fields (aliases: u, edit, mod, modify)."""
    # Show help if no resource, field, or value is provided
    if not resource or not field or not value:
        show_command_help(ctx, None, True)
        return

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
@click.argument(
    "resource",
    type=click.Choice(get_resource_choices()),
    required=False,
)
@click.argument("field", required=False)
# @click.argument("value", required=False)
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
    callback=show_command_help,
    help="Show this message and exit.",
)
@click.pass_context
def create(
    ctx: click.Context,
    resource: str,
    field: str,
    # value: str,
    names: tuple,
    verbose: bool,
    dry_run: bool,
    **kwargs,
) -> None:
    """Create Slurm resource fields (aliases: c, new, add)."""
    # Show help if no resource, field, or value is provided
    if not resource or not field:
        # or not value:
        show_command_help(ctx, None, True)
        return

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
            f"{canonical_resource} {field} {additional_args}"
        )
    else:
        if verbose:
            console.print(
                f"Creating {canonical_resource} {field} "
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
            if names[:2] == "-h" or names == "help":
                print_help("create coordinator", ctx)
                return
            Coordinator.create(field, verbose, **create_options)
        else:
            console.print(
                f"[red]Resource '{canonical_resource}' not found.[/red]"
            )


# delete command
@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument(
    "resource",
    type=click.Choice(get_resource_choices()),
    required=False,
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
    callback=show_command_help,
    help="Show this message and exit.",
)
@click.pass_context
def delete(
    ctx: click.Context,
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
    if not resource:
        show_command_help(ctx, None, True)
        return

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


# autocomplete command
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
    print("""
# Reservation autocomplete function
_slurm_cli_initialize_autocomplete() {

    # Check for optional CLI options and print their values for debugging
    local -A opts=()
    local i=1

    while [[ $i -lt ${COMP_CWORD} ]]; do
        arg="${COMP_WORDS[$i]}"
        case "$arg" in
        -v|--version)
            opts[version]="1"
            ;;
        -h|--help)
            opts[help]="1"
            ;;
        --style)
            if [[ $((i+1)) -lt ${#COMP_WORDS[@]} ]]; then
                opts[style]="${COMP_WORDS[$((i+1))]}"
                ((i++))
            else
                COMPREPLY=($(compgen -W "pretty json" -- "$cur"))
                return
            fi
            ;;
        -p|--pretty)
            opts[pretty]="1"
            ;;
        -j|--json)
            opts[json]="1"
            ;;
        -f|--force-update)
            opts[force_update]="1"
            ;;
        -t|--cache-timeout)
            if [[ $((i+1)) -lt ${#COMP_WORDS[@]} ]]; then
                opts[cache_timeout]="${COMP_WORDS[$((i+1))]}"
                ((i++))
            fi
            ;;
        *)
            break
            ;;
        esac
        ((i++))
    done

    if [[ ${COMP_WORDS[COMP_CWORD]:0:1} == "-" ]]; then
        COMPREPLY=($(compgen -W "-v -h -p -j -f -t --style --pretty --json --force-update --cache-timeout --help --version" -- "$cur"))
        return
    fi

    # Get command and resource name if any
    local cmd=""
    local resource=""
    cmd="${COMP_WORDS[$i]}"
    resource="${COMP_WORDS[$((i+1))]}"
    # echo -e "\\nCOMP_CWORD=$COMP_CWORD; i=$i COMP_WORDS=${COMP_WORDS[@]} Current=${COMP_WORDS[COMP_CWORD]} cmd=$cmd resource=$resource"

    local cur="${COMP_WORDS[COMP_CWORD]}"
    local prev="${COMP_WORDS[COMP_CWORD-1]}"

    # Guess the command by prefix, using the same commands as in get_command
    local guessed="no"
    case "$cmd" in
        s*)
            guessed="show"
            cmd="show"
            ;;
        g*)
            guessed="get"
            cmd="show"
            ;;
        cr*)
            guessed="create"
            cmd="create"
            ;;
        ne*)
            guessed="new"
            cmd="create"
            ;;
        ad*)
            guessed="add"
            cmd="create"
            ;;
        u*)
            guessed="update"
            cmd="update"
            ;;
        e*)
            guessed="edit"
            cmd="update"
            ;;
        ch*)
            guessed="change"
            cmd="update"
            ;;
        m*)
            guessed="modify"
            cmd="update"
            ;;
        d*)
            guessed="delete"
            cmd="delete"
            ;;
        re*)
            guessed="remove"
            cmd="delete"
            ;;
        rm*)
            guessed="rm"
            cmd="delete"
            ;;
        l*)
            guessed="list-resources"
            cmd="list-resources"
            ;;
        au*)
            guessed="autocomplete"
            cmd="autocomplete"
            ;;
        h*)
            guessed="help"
            cmd="help"
            ;;
        v*)
            guessed="version"
            cmd="version"
            ;;
        *)
            ;;
    esac
    if [[ $i == $((COMP_CWORD)) ]]; then
        if [[ $guessed != "no" ]]; then
            COMPREPLY=($(compgen -W "$guessed" -- "$cur"))
            return
        else
            COMPREPLY=($(compgen -W "show get create add new update edit change modify delete remove rm list-resources autocomplete help version -v -h -p -j -f -t --style --pretty --json --force-update --cache-timeout --help --version" -- "$cur"))
            return
        fi
    fi

    i=$((i+1))
    guessed="no"
    case "$resource" in
        lic*)
            guessed="licenses"
            ;;
        reso*)
            guessed="resources"
            # _slurm_cli_license_autocomplete "$cmd" "$cur" "$prev"
            ;;
        res*)
            guessed="reservations"
            # _slurm_cli_reservation_autocomplete "$cmd" "$cur" "$prev"
            ;;
        no*)
            guessed="nodes"
            # _slurm_cli_node_autocomplete "$cmd" "$cur" "$prev"
            ;;
        part*)
            guessed="partitions"
            # _slurm_cli_partition_autocomplete "$cmd" "$cur" "$prev"
            ;;
        acc*)
            guessed="accounts"
            # _slurm_cli_account_autocomplete "$cmd" "$cur" "$prev"
            ;;
        qos*)
            guessed="qos"
            # _slurm_cli_qos_autocomplete "$cmd" "$cur" "$prev"
            ;;
        us*)
            guessed="users"
            # _slurm_cli_user_autocomplete "$cmd" "$cur" "$prev"
            ;;
        pr*)
            guessed="problems"
            # _slurm_cli_problem_autocomplete "$cmd" "$cur" "$prev"
            ;;
        st*)
            guessed="stats"
            # _slurm_cli_stat_autocomplete "$cmd" "$cur" "$prev"
            ;;
        as*)
            guessed="associations"
            # _slurm_cli_association_autocomplete "$cmd" "$cur" "$prev"
            ;;
        du*)
            guessed="dumps"
            # _slurm_cli_dump_autocomplete "$cmd" "$cur" "$prev"
            ;;
        ev*)
            guessed="events"
            # _slurm_cli_event_autocomplete "$cmd" "$cur" "$prev"
            ;;
        b*)
            guessed="bad"
            # _slurm_cli_runawayjob_autocomplete "$cmd" "$cur" "$prev"
            ;;
        runa*)
            guessed="runawayjobs"
            # _slurm_cli_runawayjob_autocomplete "$cmd" "$cur" "$prev"
            ;;
        tr*)
            guessed="tres"
            # _slurm_cli_tres_autocomplete "$cmd" "$cur" "$prev"
            ;;
        ar*)
            guessed="archive"
            # _slurm_cli_archive_autocomplete "$cmd" "$cur" "$prev"
            ;;
        co*)
            guessed="coordinators"
            # _slurm_cli_coordinator_autocomplete "$cmd" "$cur" "$prev"
            ;;
    esac

    # echo "i=$i COMP_CWORD=$COMP_CWORD guessed=$guessed"
    if [[ $i == $((COMP_CWORD)) ]]; then
        if [[ $guessed != "no" ]]; then
            COMPREPLY=($(compgen -W "$guessed" -- "$cur"))
            return
        else
            COMPREPLY=($(compgen -W "reservations nodes partitions accounts qos users coordinators problems stats associations dump events licenses bad runawayjobs tres archives coordinators" -- "$cur"))
            return
        fi
    fi
    # command current_autocomplete_word_index
    _slurm_cli_${resource}_autocomplete "$cmd" "$i"

    # echo "${COMP_REPLY[@]}"
}
""")
    print(Reservation.generate_autocomplete_options())
    print("""

# Register the completion function
complete -F _slurm_cli_initialize_autocomplete slurm-cli
    """)
    return

# list-resources command
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
        for field in [
            "problems",
            "stats",
            "events",
            "runawayjobs",
            "transactions",
        ]:
            table.add_row(field, "N/A", "get/set")

    console.print(table)


@click.command(context_settings=CONTEXT_SETTINGS)
def version() -> None:
    """Show version information."""
    console.print("[bold blue]clurm-cli:[/] Slurm Swiss Knife v0.1.0")
    console.print("A CLI tool for Slurm cluster management")


@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument("word", required=False)
@click.argument("subcommand", required=False)
def help(
    word: Optional[str] = None, subcommand: Optional[str] = None
) -> None:
    """Show FULL help information and available resources."""
    if subcommand:
        ctx = click.get_current_context()
        word = resolve_command_alias(word)
        print_help(f"{word} {subcommand}", ctx)
        return
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

        show_command_help_with_resources()
        # # Show available resources
        # console.print("\n[bold]Available Slurm Resources:[/bold]")
        # table = Table()
        # table.add_column("Resource Type", style="cyan", no_wrap=True)
        # table.add_column("Available Fields", style="green")
        # table.add_column("Operations", style="yellow")

        # routes = ROUTES["get-set"]
        # if isinstance(routes, dict):
        #     for resource_type, fields in routes.items():
        #         if isinstance(fields, dict):
        #             field_list = (
        #                 ", ".join(fields.keys()) if fields else "N/A"
        #             )
        #         else:
        #             field_list = "N/A"
        #         operations: List[str] = []
        #         if (
        #             isinstance(ROUTES["get-set"], dict)
        #             and resource_type in ROUTES["get-set"]
        #         ):
        #             operations.append("get/set")
        #         if (
        #             isinstance(ROUTES["create"], dict)
        #             and resource_type in ROUTES["create"]
        #         ):
        #             operations.append("create")
        #         if (
        #             isinstance(ROUTES["create"], dict)
        #             and resource_type in ROUTES["create"]
        #         ):
        #             operations.append("delete")

        #         table.add_row(
        #             resource_type, field_list, ", ".join(operations)
        #         )

        # console.print(table)


# Register commands when module is imported
register_commands()


if __name__ == "__main__":
    main()

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


# @click.command(context_settings=CONTEXT_SETTINGS, name="modify")
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
# def update_alias_modify(
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

# # Create command aliases
# @click.command(context_settings=CONTEXT_SETTINGS, name="c")
# @click.argument(
#     "resource", type=click.Choice(get_create_resource_choices())
# )
# @click.argument("field")
# @click.argument("value")
# @click.argument("names", nargs=-1, required=False)
# @click.option(
#     "--verbose", "-v", is_flag=True, help="Enable verbose output"
# )
# @click.option(
#     "--dry-run",
#     is_flag=True,
#     help="Show what would be created without making changes",
# )
# @click.option(
#     "--help",
#     "-h",
#     is_flag=True,
#     is_eager=True,
#     callback=show_command_help_with_resources,
#     help="Show this message and exit.",
# )
# def create_alias_c(
#     resource: str,
#     field: str,
#     value: str,
#     names: tuple,
#     verbose: bool,
#     dry_run: bool,
#     **kwargs,
# ) -> None:
#     """Create Slurm resource fields (alias for create)."""
#     # Resolve resource alias to canonical name
#     canonical_resource = resolve_resource_alias(resource)

#     # Parse additional arguments into key-value pairs
#     create_options = {}
#     if names:
#         for arg in names:
#             if "=" in arg:
#                 # Handle key=value format
#                 key, value_part = arg.split("=", 1)
#                 create_options[key] = value_part
#             else:
#                 # Treat as a simple value
#                 create_options[arg] = None

#     if names:
#         additional_args = " ".join(f"'{arg}'" for arg in names)
#     else:
#         additional_args = None

#     if dry_run:
#         console.print(
#             f"[yellow]DRY RUN:[/yellow] Would create "
#             f"{canonical_resource} {field} '{value}' {additional_args}"
#         )
#     else:
#         if verbose:
#             console.print(
#                 f"Creating {canonical_resource} {field} '{value}' "
#                 f"{additional_args}"
#             )

#         if canonical_resource[:4] == "part":
#             Partition.create(field, verbose, **create_options)
#         elif canonical_resource[:4] == "node":
#             Node.create(field, verbose, **create_options)
#         elif canonical_resource[:4] == "user":
#             User.create(field, verbose, **create_options)
#         elif canonical_resource[:3] == "qos":
#             Qos.create(field, verbose, **create_options)
#         elif canonical_resource[:3] == "acc":
#             Account.create(field, verbose, **create_options)
#         elif canonical_resource[:3] == "res":
#             Reservation.create(field, verbose, **create_options)
#         elif canonical_resource[:5] == "coord":
#             Coordinator.create(field, verbose, **create_options)
#         else:
#             console.print(
#                 f"[red]Resource '{canonical_resource}' not found.[/red]"
#             )


# @click.command(context_settings=CONTEXT_SETTINGS, name="new")
# @click.argument(
#     "resource", type=click.Choice(get_create_resource_choices())
# )
# @click.argument("field")
# @click.argument("value")
# @click.argument("names", nargs=-1, required=False)
# @click.option(
#     "--verbose", "-v", is_flag=True, help="Enable verbose output"
# )
# @click.option(
#     "--dry-run",
#     is_flag=True,
#     help="Show what would be created without making changes",
# )
# @click.option(
#     "--help",
#     "-h",
#     is_flag=True,
#     is_eager=True,
#     callback=show_command_help_with_resources,
#     help="Show this message and exit.",
# )
# def create_alias_new(
#     resource: str,
#     field: str,
#     value: str,
#     names: tuple,
#     verbose: bool,
#     dry_run: bool,
#     **kwargs,
# ) -> None:
#     """Create Slurm resource fields (alias for create)."""
#     # Resolve resource alias to canonical name
#     canonical_resource = resolve_resource_alias(resource)

#     # Parse additional arguments into key-value pairs
#     create_options = {}
#     if names:
#         for arg in names:
#             if "=" in arg:
#                 # Handle key=value format
#                 key, value_part = arg.split("=", 1)
#                 create_options[key] = value_part
#             else:
#                 # Treat as a simple value
#                 create_options[arg] = None

#     if names:
#         additional_args = " ".join(f"'{arg}'" for arg in names)
#     else:
#         additional_args = None

#     if dry_run:
#         console.print(
#             f"[yellow]DRY RUN:[/yellow] Would create "
#             f"{canonical_resource} {field} '{value}' {additional_args}"
#         )
#     else:
#         if verbose:
#             console.print(
#                 f"Creating {canonical_resource} {field} '{value}' "
#                 f"{additional_args}"
#             )

#         if canonical_resource[:4] == "part":
#             Partition.create(field, verbose, **create_options)
#         elif canonical_resource[:4] == "node":
#             Node.create(field, verbose, **create_options)
#         elif canonical_resource[:4] == "user":
#             User.create(field, verbose, **create_options)
#         elif canonical_resource[:3] == "qos":
#             Qos.create(field, verbose, **create_options)
#         elif canonical_resource[:3] == "acc":
#             Account.create(field, verbose, **create_options)
#         elif canonical_resource[:3] == "res":
#             Reservation.create(field, verbose, **create_options)
#         elif canonical_resource[:5] == "coord":
#             Coordinator.create(field, verbose, **create_options)
#         else:
#             console.print(
#                 f"[red]Resource '{canonical_resource}' not found.[/red]"
#             )


# @click.command(context_settings=CONTEXT_SETTINGS, name="add")
# @click.argument(
#     "resource", type=click.Choice(get_create_resource_choices())
# )
# @click.argument("field")
# @click.argument("value")
# @click.argument("names", nargs=-1, required=False)
# @click.option(
#     "--verbose", "-v", is_flag=True, help="Enable verbose output"
# )
# @click.option(
#     "--dry-run",
#     is_flag=True,
#     help="Show what would be created without making changes",
# )
# @click.option(
#     "--help",
#     "-h",
#     is_flag=True,
#     is_eager=True,
#     callback=show_command_help_with_resources,
#     help="Show this message and exit.",
# )
# def create_alias_add(
#     resource: str,
#     field: str,
#     value: str,
#     names: tuple,
#     verbose: bool,
#     dry_run: bool,
#     **kwargs,
# ) -> None:
#     """Create Slurm resource fields (alias for create)."""
#     # Resolve resource alias to canonical name
#     canonical_resource = resolve_resource_alias(resource)

#     # Parse additional arguments into key-value pairs
#     create_options = {}
#     if names:
#         for arg in names:
#             if "=" in arg:
#                 # Handle key=value format
#                 key, value_part = arg.split("=", 1)
#                 create_options[key] = value_part
#             else:
#                 # Treat as a simple value
#                 create_options[arg] = None

#     if names:
#         additional_args = " ".join(f"'{arg}'" for arg in names)
#     else:
#         additional_args = None

#     if dry_run:
#         console.print(
#             f"[yellow]DRY RUN:[/yellow] Would create "
#             f"{canonical_resource} {field} '{value}' {additional_args}"
#         )
#     else:
#         if verbose:
#             console.print(
#                 f"Creating {canonical_resource} {field} '{value}' "
#                 f"{additional_args}"
#             )

#         if canonical_resource[:4] == "part":
#             Partition.create(field, verbose, **create_options)
#         elif canonical_resource[:4] == "node":
#             Node.create(field, verbose, **create_options)
#         elif canonical_resource[:4] == "user":
#             User.create(field, verbose, **create_options)
#         elif canonical_resource[:3] == "qos":
#             Qos.create(field, verbose, **create_options)
#         elif canonical_resource[:3] == "acc":
#             Account.create(field, verbose, **create_options)
#         elif canonical_resource[:3] == "res":
#             Reservation.create(field, verbose, **create_options)
#         elif canonical_resource[:5] == "coord":
#             Coordinator.create(field, verbose, **create_options)
#         else:
#             console.print(
#                 f"[red]Resource '{canonical_resource}' not found.[/red]"
#             )

# # Delete command aliases
# @click.command(context_settings=CONTEXT_SETTINGS, name="del")
# @click.argument("resource", type=click.Choice(get_resource_choices()))
# @click.argument("names", nargs=-1, required=False)
# @click.option(
#     "--name",
#     "-n",
#     help="Name of the resource to delete "
#          "(alternative to positional argument)",
# )
# @click.option(
#     "--force",
#     "-f",
#     is_flag=True,
#     help="Force deletion without confirmation",
# )
# @click.option(
#     "--dry-run",
#     is_flag=True,
#     help="Show what would be deleted without making changes",
# )
# @click.option(
#     "--verbose", "-v", is_flag=True, help="Enable verbose output"
# )
# @click.option(
#     "--help",
#     "-h",
#     is_flag=True,
#     is_eager=True,
#     callback=show_command_help_with_resources,
#     help="Show this message and exit.",
# )
# def delete_alias_del(
#     resource: str,
#     names: tuple,
#     name: Optional[str],
#     force: bool,
#     dry_run: bool,
#     verbose: bool,
#     **kwargs,
# ) -> None:
#     """Delete Slurm resources (alias for delete)."""
#     # Resolve resource alias to canonical name
#     canonical_resource = resolve_resource_alias(resource)

#     # Handle multiple names - prioritize positional names over --name option
#     if names:
#         resource_names = names
#     elif name:
#         resource_names = [name]
#     else:
#         resource_names = [None]

#     for resource_name in resource_names:
#         if dry_run:
#             if resource_name:
#                 console.print(
#                     "[yellow]DRY RUN:[/yellow] "
#                     f"Would delete {canonical_resource} '{resource_name}'"
#                 )
#             else:
#                 console.print(
#                     "[yellow]DRY RUN:[/yellow] "
#                     f"Would delete {canonical_resource}"
#                 )
#         else:
#             if not force and not click.confirm(
#                 f"Are you sure you want to delete {canonical_resource}"
#                 + (f" '{resource_name}'" if resource_name else "")
#                 + "?"
#             ):
#                 console.print("[red]Operation cancelled.[/red]")
#                 raise click.Abort()

#             if resource_name:
#                 if verbose:
#                     console.print(
#                         f"Deleting {canonical_resource} '{resource_name}'"
#                     )
#                 else:
#                     console.print(
#                         f"Deleting {canonical_resource} '{resource_name}'"
#                     )
#                 console.print(
#                     f"Deleting {canonical_resource} '{resource_name}'"
#                 )
#             else:
#                 console.print(f"Deleting {canonical_resource}")


# @click.command(context_settings=CONTEXT_SETTINGS, name="d")
# @click.argument("resource", type=click.Choice(get_resource_choices()))
# @click.argument("names", nargs=-1, required=False)
# @click.option(
#     "--name",
#     "-n",
#     help="Name of the resource to delete "
#          "(alternative to positional argument)",
# )
# @click.option(
#     "--force",
#     "-f",
#     is_flag=True,
#     help="Force deletion without confirmation",
# )
# @click.option(
#     "--dry-run",
#     is_flag=True,
#     help="Show what would be deleted without making changes",
# )
# @click.option(
#     "--verbose", "-v", is_flag=True, help="Enable verbose output"
# )
# @click.option(
#     "--help",
#     "-h",
#     is_flag=True,
#     is_eager=True,
#     callback=show_command_help_with_resources,
#     help="Show this message and exit.",
# )
# def delete_alias_d(
#     resource: str,
#     names: tuple,
#     name: Optional[str],
#     force: bool,
#     dry_run: bool,
#     verbose: bool,
#     **kwargs,
# ) -> None:
#     """Delete Slurm resources (alias for delete)."""
#     # Resolve resource alias to canonical name
#     canonical_resource = resolve_resource_alias(resource)

#     # Handle multiple names - prioritize positional names over --name option
#     if names:
#         resource_names = names
#     elif name:
#         resource_names = [name]
#     else:
#         resource_names = [None]

#     for resource_name in resource_names:
#         if dry_run:
#             if resource_name:
#                 console.print(
#                     "[yellow]DRY RUN:[/yellow] "
#                     f"Would delete {canonical_resource} '{resource_name}'"
#                 )
#             else:
#                 console.print(
#                     "[yellow]DRY RUN:[/yellow] "
#                     f"Would delete {canonical_resource}"
#                 )
#         else:
#             if not force and not click.confirm(
#                 f"Are you sure you want to delete {canonical_resource}"
#                 + (f" '{resource_name}'" if resource_name else "")
#                 + "?"
#             ):
#                 console.print("[red]Operation cancelled.[/red]")
#                 raise click.Abort()

#             if resource_name:
#                 if verbose:
#                     console.print(
#                         f"Deleting {canonical_resource} '{resource_name}'"
#                     )
#                 else:
#                     console.print(
#                         f"Deleting {canonical_resource} '{resource_name}'"
#                     )
#                 console.print(
#                     f"Deleting {canonical_resource} '{resource_name}'"
#                 )
#             else:
#                 console.print(f"Deleting {canonical_resource}")


# @click.command(context_settings=CONTEXT_SETTINGS, name="remove")
# @click.argument("resource", type=click.Choice(get_resource_choices()))
# @click.argument("names", nargs=-1, required=False)
# @click.option(
#     "--name",
#     "-n",
#     help="Name of the resource to delete "
#          "(alternative to positional argument)",
# )
# @click.option(
#     "--force",
#     "-f",
#     is_flag=True,
#     help="Force deletion without confirmation",
# )
# @click.option(
#     "--dry-run",
#     is_flag=True,
#     help="Show what would be deleted without making changes",
# )
# @click.option(
#     "--verbose", "-v", is_flag=True, help="Enable verbose output"
# )
# @click.option(
#     "--help",
#     "-h",
#     is_flag=True,
#     is_eager=True,
#     callback=show_command_help_with_resources,
#     help="Show this message and exit.",
# )
# def delete_alias_remove(
#     resource: str,
#     names: tuple,
#     name: Optional[str],
#     force: bool,
#     dry_run: bool,
#     verbose: bool,
#     **kwargs,
# ) -> None:
#     """Delete Slurm resources (alias for delete)."""
#     # Resolve resource alias to canonical name
#     canonical_resource = resolve_resource_alias(resource)

#     # Handle multiple names - prioritize positional names over --name option
#     if names:
#         resource_names = names
#     elif name:
#         resource_names = [name]
#     else:
#         resource_names = [None]

#     for resource_name in resource_names:
#         if dry_run:
#             if resource_name:
#                 console.print(
#                     "[yellow]DRY RUN:[/yellow] "
#                     f"Would delete {canonical_resource} '{resource_name}'"
#                 )
#             else:
#                 console.print(
#                     "[yellow]DRY RUN:[/yellow] "
#                     f"Would delete {canonical_resource}"
#                 )
#         else:
#             if not force and not click.confirm(
#                 f"Are you sure you want to delete {canonical_resource}"
#                 + (f" '{resource_name}'" if resource_name else "")
#                 + "?"
#             ):
#                 console.print("[red]Operation cancelled.[/red]")
#                 raise click.Abort()

#             if resource_name:
#                 if verbose:
#                     console.print(
#                         f"Deleting {canonical_resource} '{resource_name}'"
#                     )
#                 else:
#                     console.print(
#                         f"Deleting {canonical_resource} '{resource_name}'"
#                     )
#                 console.print(
#                     f"Deleting {canonical_resource} '{resource_name}'"
#                 )
#             else:
#                 console.print(f"Deleting {canonical_resource}")


# @click.command(context_settings=CONTEXT_SETTINGS, name="rem")
# @click.argument("resource", type=click.Choice(get_resource_choices()))
# @click.argument("names", nargs=-1, required=False)
# @click.option(
#     "--name",
#     "-n",
#     help="Name of the resource to delete "
#          "(alternative to positional argument)",
# )
# @click.option(
#     "--force",
#     "-f",
#     is_flag=True,
#     help="Force deletion without confirmation",
# )
# @click.option(
#     "--dry-run",
#     is_flag=True,
#     help="Show what would be deleted without making changes",
# )
# @click.option(
#     "--verbose", "-v", is_flag=True, help="Enable verbose output"
# )
# @click.option(
#     "--help",
#     "-h",
#     is_flag=True,
#     is_eager=True,
#     callback=show_command_help_with_resources,
#     help="Show this message and exit.",
# )
# def delete_alias_rem(
#     resource: str,
#     names: tuple,
#     name: Optional[str],
#     force: bool,
#     dry_run: bool,
#     verbose: bool,
#     **kwargs,
# ) -> None:
#     """Delete Slurm resources (alias for delete)."""
#     # Resolve resource alias to canonical name
#     canonical_resource = resolve_resource_alias(resource)

#     # Handle multiple names - prioritize positional names
#     # over --name option
#     if names:
#         resource_names = names
#     elif name:
#         resource_names = [name]
#     else:
#         resource_names = [None]

#     for resource_name in resource_names:
#         if dry_run:
#             if resource_name:
#                 console.print(
#                     "[yellow]DRY RUN:[/yellow] "
#                     f"Would delete {canonical_resource} '{resource_name}'"
#                 )
#             else:
#                 console.print(
#                     "[yellow]DRY RUN:[/yellow] "
#                     f"Would delete {canonical_resource}"
#                 )
#         else:
#             if not force and not click.confirm(
#                 f"Are you sure you want to delete {canonical_resource}"
#                 + (f" '{resource_name}'" if resource_name else "")
#                 + "?"
#             ):
#                 console.print("[red]Operation cancelled.[/red]")
#                 raise click.Abort()

#             if resource_name:
#                 if verbose:
#                     console.print(
#                         f"Deleting {canonical_resource} '{resource_name}'"
#                     )
#                 else:
#                     console.print(
#                         f"Deleting {canonical_resource} '{resource_name}'"
#                     )
#                 console.print(
#                     f"Deleting {canonical_resource} '{resource_name}'"
#                 )
#             else:
#                 console.print(f"Deleting {canonical_resource}")


# @click.command(context_settings=CONTEXT_SETTINGS, name="rm")
# @click.argument("resource", type=click.Choice(get_resource_choices()))
# @click.argument("names", nargs=-1, required=False)
# @click.option(
#     "--name",
#     "-n",
#     help="Name of the resource to delete "
#          "(alternative to positional argument)",
# )
# @click.option(
#     "--force",
#     "-f",
#     is_flag=True,
#     help="Force deletion without confirmation",
# )
# @click.option(
#     "--dry-run",
#     is_flag=True,
#     help="Show what would be deleted without making changes",
# )
# @click.option(
#     "--verbose", "-v", is_flag=True, help="Enable verbose output"
# )
# @click.option(
#     "--help",
#     "-h",
#     is_flag=True,
#     is_eager=True,
#     callback=show_command_help_with_resources,
#     help="Show this message and exit.",
# )
# def delete_alias_rm(
#     resource: str,
#     names: tuple,
#     name: Optional[str],
#     force: bool,
#     dry_run: bool,
#     verbose: bool,
#     **kwargs,
# ) -> None:
#     """Delete Slurm resources (alias for delete)."""
#     # Resolve resource alias to canonical name
#     canonical_resource = resolve_resource_alias(resource)

#     # Handle multiple names - prioritize positional names over --name option
#     if names:
#         resource_names = names
#     elif name:
#         resource_names = [name]
#     else:
#         resource_names = [None]

#     for resource_name in resource_names:
#         if dry_run:
#             if resource_name:
#                 console.print(
#                     "[yellow]DRY RUN:[/yellow] "
#                     f"Would delete {canonical_resource} '{resource_name}'"
#                 )
#             else:
#                 console.print(
#                     "[yellow]DRY RUN:[/yellow] "
#                     f"Would delete {canonical_resource}"
#                 )
#         else:
#             if not force and not click.confirm(
#                 f"Are you sure you want to delete {canonical_resource}"
#                 + (f" '{resource_name}'" if resource_name else "")
#                 + "?"
#             ):
#                 console.print("[red]Operation cancelled.[/red]")
#                 raise click.Abort()

#             if resource_name:
#                 if verbose:
#                     console.print(
#                         f"Deleting {canonical_resource} '{resource_name}'"
#                     )
#                 else:
#                     console.print(
#                         f"Deleting {canonical_resource} '{resource_name}'"
#                     )
#                 console.print(
#                     f"Deleting {canonical_resource} '{resource_name}'"
#                 )
#             else:
#                 console.print(f"Deleting {canonical_resource}")


# # List-resources command aliases
# @click.command(context_settings=CONTEXT_SETTINGS, name="list")
# def list_resources_alias_list() -> None:
#     """List all available resource types and their fields
#     (alias for list-resources)."""
#     table = Table(title="Available Slurm Resources")
#     table.add_column("Resource Type", style="cyan", no_wrap=True)
#     table.add_column("Available Fields", style="green")
#     table.add_column("Operations", style="yellow")

#     routes = ROUTES["get-set"]
#     if isinstance(routes, dict):
#         for resource_type, fields in routes.items():
#             if isinstance(fields, dict):
#                 field_list = (
#                     ", ".join(fields.keys()) if fields else "N/A"
#                 )
#             else:
#                 field_list = "N/A"
#             operations: List[str] = []
#             if (
#                 isinstance(ROUTES["get-set"], dict)
#                 and resource_type in ROUTES["get-set"]
#             ):
#                 operations.append("get/set")
#             if (
#                 isinstance(ROUTES["create"], dict)
#                 and resource_type in ROUTES["create"]
#             ):
#                 operations.append("create")
#             if (
#                 isinstance(ROUTES["create"], dict)
#                 and resource_type in ROUTES["create"]
#             ):
#                 operations.append("delete")

#             table.add_row(
#                 resource_type, field_list, ", ".join(operations)
#             )
#         for field in ["problems", "stats",  "events",
#                       "runawayjobs", "transactions"]:
#             table.add_row(field, "N/A", "get/set")

#     console.print(table)


# @click.command(context_settings=CONTEXT_SETTINGS, name="ls")
# def list_resources_alias_ls() -> None:
#     """List all available resource types and their fields
#     (alias for list-resources)."""
#     table = Table(title="Available Slurm Resources")
#     table.add_column("Resource Type", style="cyan", no_wrap=True)
#     table.add_column("Available Fields", style="green")
#     table.add_column("Operations", style="yellow")

#     routes = ROUTES["get-set"]
#     if isinstance(routes, dict):
#         for resource_type, fields in routes.items():
#             if isinstance(fields, dict):
#                 field_list = (
#                     ", ".join(fields.keys()) if fields else "N/A"
#                 )
#             else:
#                 field_list = "N/A"
#             operations: List[str] = []
#             if (
#                 isinstance(ROUTES["get-set"], dict)
#                 and resource_type in ROUTES["get-set"]
#             ):
#                 operations.append("get, mod")
#             if (
#                 isinstance(ROUTES["create"], dict)
#                 and resource_type in ROUTES["create"]
#             ):
#                 operations.append("create")
#             if (
#                 isinstance(ROUTES["create"], dict)
#                 and resource_type in ROUTES["create"]
#             ):
#                 operations.append("delete")

#             table.add_row(
#                 resource_type, field_list, ", ".join(operations)
#             )
#         for field in ["problems", "stats",  "events",
#                       "runawayjobs", "transactions"]:
#             table.add_row(field, "N/A", "get")
#             # "associations", "dump", "licenses", "tres", "archive"

#     console.print(table)


# @click.command(context_settings=CONTEXT_SETTINGS, name="l")
# def list_resources_alias_l() -> None:
#     """List all available resource types and their fields
#     (alias for list-resources)."""
#     table = Table(title="Available Slurm Resources")
#     table.add_column("Resource Type", style="cyan", no_wrap=True)
#     table.add_column("Available Fields", style="green")
#     table.add_column("Operations", style="yellow")

#     routes = ROUTES["get-set"]
#     if isinstance(routes, dict):
#         for resource_type, fields in routes.items():
#             if isinstance(fields, dict):
#                 field_list = (
#                     ", ".join(fields.keys()) if fields else "N/A"
#                 )
#             else:
#                 field_list = "N/A"
#             operations: List[str] = []
#             if (
#                 isinstance(ROUTES["get-set"], dict)
#                 and resource_type in ROUTES["get-set"]
#             ):
#                 operations.append("get/set")
#             if (
#                 isinstance(ROUTES["create"], dict)
#                 and resource_type in ROUTES["create"]
#             ):
#                 operations.append("create")
#             if (
#                 isinstance(ROUTES["create"], dict)
#                 and resource_type in ROUTES["create"]
#             ):
#                 operations.append("delete")

#             table.add_row(
#                 resource_type, field_list, ", ".join(operations)
#             )

#     console.print(table)
