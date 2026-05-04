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

import json
import os
import subprocess
from typing import Any, Dict, List, Optional, Tuple, Union

import click  # pyright: ignore[reportMissingImports]
from fast_autocomplete import AutoComplete  # pyright: ignore
from rich.box import (
    SIMPLE_HEAVY,
)  # pyright: ignore[reportMissingImports]
from rich.table import Table  # pyright: ignore[reportMissingImports]

from .utils.accounts import Account
from .utils.associations import Association
from .utils.autocomplete_helpers import (
    get_common_autocomplete_functions,
)
from .utils.config import ROUTES, VERBS
from .utils.coordinators import Coordinator
from .utils.events import Event
from .utils.job_filter import (
    is_job_filter,
    resolve_job_filters,
    resolve_job_ids,
)
from .utils.jobs import Job
from .utils.node_filter import (
    is_node_filter,
    resolve_node_filters,
    resolve_nodes_value,
)
from .utils.nodes import Node
from .utils.partitions import Partition
from .utils.prefix_utils import (  # get_all_resource_names,
    COMMANDS,
    RESOURCES,
    generate_bash_command_case,
    generate_bash_resource_case,
    get_all_command_names,
    get_cached_command_matcher,
    get_cached_resource_matcher,
    get_resource_help,
    get_resources_epilog,
)
from .utils.profiles import (
    is_profile_help,
    show_all_profile_fields,
    show_profile_help,
)
from .utils.qos import Qos
from .utils.reservations import Reservation
from .utils.resources import Resource
from .utils.slurm_config import Config
from .utils.users import User
from .utils.utils import console


def list_fields_callback(ctx, param, value):
    """Callback for --list-fields option."""
    if not value:
        return
    if value == "all":
        show_all_profile_fields()
    else:
        show_profile_help(value)
    ctx.exit(0)


def confirm_single_key(message: str, default: bool = False) -> bool:
    """Single-key confirmation (y/n) without requiring Enter.

    Args:
        message: The confirmation message to display
        default: Default value if Enter is pressed (False = No)

    Returns:
        True if user confirmed, False otherwise
    """
    suffix = " [y/N]: " if not default else " [Y/n]: "
    click.echo(message + suffix, nl=False)
    char = click.getchar()
    click.echo()  # New line after keypress
    if char in ("y", "Y"):
        return True
    if char in ("n", "N"):
        return False
    # Enter or other key = default
    return default


CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])
# Context settings without automatic help
# (for commands with custom help callback)
CONTEXT_SETTINGS_NO_HELP = dict(help_option_names=[])
STYLE_OPTIONS = ["pretty", "json", "csv"]


def resolve_node_filters_in_options(
    options: Dict[str, Any], verbose: bool = False
) -> Optional[Dict[str, Any]]:
    """Resolve node filter expressions in options dict.

    Looks for 'nodes', 'nodes+', 'nodes-' keys and resolves any filter
    expressions like:
    - partition=<name>
    - state=<state>
    - user=<username>
    - reservation=<name>

    Args:
        options: Dictionary of options
        verbose: Print debug information

    Returns:
        Options dict with resolved node filters, or None if filter matched
        no nodes (command should abort)
    """
    if not options:
        return options

    # Check for nodes-related keys (nodes, nodes+, nodes-)
    nodes_keys = []
    for key in options:
        key_lower = key.lower()
        if key_lower in ("nodes", "nodes+", "nodes-"):
            nodes_keys.append(key)

    for nodes_key in nodes_keys:
        if options[nodes_key]:
            value = options[nodes_key]
            if is_node_filter(value):
                resolved = resolve_nodes_value(value, verbose)
                if resolved:
                    options[nodes_key] = resolved
                else:
                    # Empty result - abort command
                    console.print(
                        f"[red]Error: Node filter '{value}' "
                        f"matched no nodes. Aborting.[/red]"
                    )
                    return None

    return options


# Resource help now centralized in prefix_utils.RESOURCES


def get_resource_choices() -> List[str]:
    """Get all valid resource names including aliases."""
    # matcher = get_cached_resource_matcher()
    routes = ROUTES["get-set"]
    if isinstance(routes, dict):
        # Include canonical names from routes and all aliases
        choices = list(routes.keys())
        for res in routes.keys():
            if res in RESOURCES:
                choices.extend(RESOURCES[res]["aliases"])
        return list(sorted(set(choices)))
    return []


def get_show_resource_choices() -> List[str]:
    """Get all valid resource names for show command."""
    ret = get_resource_choices()
    # Add additional show-only resources
    additional = [
        "config",
        "problems",
        "stats",
        "associations",
        "dumps",
        "events",
        "licenses",
        "resources",
        "bads",
        "runawayjobs",
        "transactions",
        "tres",
        "archive",
    ]
    ret.extend(additional)
    # Also add aliases for additional resources
    for res in additional:
        if res in RESOURCES:
            ret.extend(RESOURCES[res]["aliases"])
    return list(sorted(set(ret)))


def resolve_resource_alias(resource: str) -> str:
    """Resolve resource alias/prefix to canonical name."""
    matcher = get_cached_resource_matcher()
    canonical, _ = matcher.match(resource)
    return canonical


def resolve_command_alias(command: str) -> str:
    """Resolve command alias/prefix to canonical name."""
    matcher = get_cached_command_matcher()
    canonical, exact = matcher.match(command)
    if canonical == command and not exact:
        # No match found - check for ambiguous prefix
        all_names = matcher.get_all_names()
        matches = [
            n for n in all_names if n.startswith(command.lower())
        ]
        if len(matches) > 1:
            raise click.ClickException(
                f"Ambiguous command: {command}. "
                f"Could be: {', '.join(matches)}"
            )
    return canonical


def common_options(func):
    """Decorator to add common options to commands.

    This allows command-level overrides of global options.
    """
    func = click.option(
        "--profile-str",
        "--format",
        "-o",
        "profile_str",
        default=None,
        help="Inline profile string (overrides --profile)",
    )(func)
    func = click.option(
        "--profile",
        "-P",
        default=None,
        help="Output profile name (overrides global)",
    )(func)
    func = click.option(
        "--delimiter",
        "-d",
        default=None,
        help="Delimiter for CSV output (overrides global)",
    )(func)
    func = click.option(
        "--zebra",
        "-z",
        is_flag=True,
        default=None,
        help="Use zebra-striped rows (overrides global)",
    )(func)
    func = click.option(
        "--csv",
        is_flag=True,
        help="Use CSV output format (overrides global)",
    )(func)
    func = click.option(
        "--json",
        "-j",
        is_flag=True,
        help="Use JSON output format (overrides global)",
    )(func)
    func = click.option(
        "--pretty",
        "-p",
        is_flag=True,
        help="Use pretty output format (overrides global)",
    )(func)
    func = click.option(
        "--style",
        type=click.Choice(["pretty", "json", "csv"]),
        default=None,
        help="Output style (overrides global)",
    )(func)
    return func


def get_output_style(
    ctx: click.Context, style_override: str = None
) -> str:
    """Get the output style from context or override."""
    if style_override:
        return style_override
    return ctx.obj.get("style", "pretty")


def get_delimiter(
    ctx: click.Context, delimiter_override: str = None
) -> str:
    """Get the CSV delimiter from context or override."""
    if delimiter_override:
        return delimiter_override
    return ctx.obj.get("delimiter", ";")


def get_zebra(ctx: click.Context, zebra_override: bool = None) -> bool:
    """Get the zebra striping flag from context or override."""
    if zebra_override is not None:
        return zebra_override
    return ctx.obj.get("zebra", False)


def get_row_styles(zebra: bool = False):
    """Get row styles for tables based on zebra flag."""
    if zebra:
        return ["", "on rgb(30,40,60)"]  # Alternate with light blue bg
    return None


def get_force_update(ctx: click.Context) -> bool:
    """Get the force update flag from context."""
    return ctx.obj.get("force_update", False)


def get_dry_run(
    ctx: click.Context, dry_run_override: bool = None
) -> bool:
    """Get the dry-run flag from context or override.

    Priority:
    1. Command-level --dry-run flag (if True)
    2. Global --no-dry-run flag (if set, forces False)
    3. Global --dry-run flag
    4. SLURM_CLI_DRYRUN env var
    """
    # Command-level override takes highest priority
    if dry_run_override is True:
        return True

    # Check if --no-dry-run was explicitly set
    if ctx.obj.get("no_dry_run", False):
        return False

    # Global --dry-run or env var
    return ctx.obj.get("dry_run", False)


def get_skip_confirm(
    ctx: click.Context, yes: bool = False, force: bool = False
) -> bool:
    """Get skip confirmation flag from context and local options.

    Combines global --yes (-y) flag with command-level --yes or --force.

    Args:
        ctx: Click context
        yes: Command-level --yes flag
        force: Command-level --force flag

    Returns:
        True if confirmation should be skipped
    """
    global_yes = ctx.obj.get("yes", False) if ctx.obj else False
    return yes or force or global_yes


def get_profile(
    ctx: click.Context, profile_override: str = None
) -> str:
    """Get the profile name from context or override."""
    if profile_override:
        return profile_override
    return ctx.obj.get("profile", "default")


def get_profile_str(
    ctx: click.Context, profile_str_override: str = None
) -> str:
    """Get the profile string from context or override."""
    if profile_str_override:
        return profile_str_override
    return ctx.obj.get("profile_str")


# CLI options per action
ACTION_OPTIONS = {
    "create": [
        ("-v, --verbose", "Enable verbose output"),
        ("-y, --yes", "Skip confirmation prompts"),
        ("-f, --force", "Skip confirmation prompts"),
        (
            "-L, --list-fields",
            "List available fields for this resource",
        ),
    ],
    "update": [
        ("-v, --verbose", "Enable verbose output"),
        (
            "-L, --list-fields",
            "List available fields for this resource",
        ),
    ],
    "delete": [
        ("-v, --verbose", "Enable verbose output"),
        ("-y, --yes", "Skip confirmation prompts"),
        ("-f, --force", "Skip confirmation prompts"),
        (
            "-L, --list-fields",
            "List available fields for this resource",
        ),
    ],
    "show": [
        ("-j, --json", "Output in JSON format"),
        ("--csv", "Output in CSV format"),
        ("-p, --pretty", "Output in pretty format (default)"),
        ("-z, --zebra", "Use zebra-striped rows"),
        ("-P, --profile NAME", "Use output profile"),
        ("-o, --format, --profile-str STR", "Inline profile string"),
        (
            "-L, --list-fields",
            "List available fields for this resource",
        ),
        ("-T, --tree", "Tree view (accounts, associations)"),
    ],
}

# Global options available for all commands
GLOBAL_OPTIONS = [
    ("-h, --help", "Show this help message"),
    ("--dry-run", "Show what would be done (or SLURM_CLI_DRYRUN=y)"),
    ("--no-dry-run", "Override SLURM_CLI_DRYRUN and disable dry-run"),
]


def show_resource_help(action: str, resource: str) -> bool:
    """Show resource-specific help for an action.

    Args:
        action: The action (create, update, delete, show)
        resource: The resource name or alias

    Returns:
        True if help was shown, False if no help available
    """
    # Get help info for this resource (handles alias resolution)
    help_info = get_resource_help(resource)
    if not help_info:
        return False

    # Resolve canonical name for display
    canonical = resolve_resource_alias(resource)

    # Get action-specific help
    action_help = get_resource_help(resource, action)
    if not action_help:
        # Show general resource description only
        console.print(
            f"\n[bold]{help_info.get('description', canonical)}[/bold]"
        )
        console.print(
            f"\n[yellow]No '{action}' action available"
            f" for {canonical}[/yellow]"
        )
        return True

    # Show help
    console.print(
        f"\n[bold]{help_info.get('description', canonical)}[/bold]"
    )
    console.print(
        f"\n[cyan]Syntax:[/cyan] {action_help.get('syntax', '')}"
    )

    if action_help.get("examples"):
        console.print("\n[cyan]Examples:[/cyan]")
        for example in action_help["examples"]:
            console.print(f"  {example}")

    if action_help.get("options"):
        console.print("\n[cyan]Resource Options:[/cyan]")
        options = ", ".join(action_help["options"])
        console.print(f"  {options}")

    # Show CLI options for this action
    cli_options = ACTION_OPTIONS.get(action, [])
    if cli_options:
        console.print("\n[cyan]Command Options:[/cyan]")
        for opt, desc in cli_options:
            console.print(f"  {opt:<22} {desc}")

    # Show global options
    console.print("\n[cyan]Global Options:[/cyan]")
    for opt, desc in GLOBAL_OPTIONS:
        console.print(f"  {opt:<22} {desc}")

    console.print()
    return True


def print_help(command: str, ctx: click.Context) -> None:
    """Print help for a command (legacy function)."""
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
    field: Union[str, Tuple[str, ...]] = None,
    force_update: bool = False,
) -> Tuple[str, Union[str, Tuple[str, ...]], dict]:
    """
    Ensure the resource name is a valid resource name.
    Return the resource type, field (may be tuple), and cached resource data.
    """
    if resource[:4] == "prob":
        return "problems", field, []
    elif resource[:4] == "stat":
        return "stats", field, []
    elif resource[:5] == "assoc":
        return "associations", field, []
    elif resource[:4] == "dump":
        return "dump", field, []
    elif resource[:2] == "ev":
        return "events", field, []
    elif resource[:3] == "lic" or resource[:4] == "reso":
        return "`licens`es", field, []
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
        # Jobs are fetched directly, not cached
        return "jobs", field, None
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

    # Check if we have a resource argument to show resource-specific help
    # Parse the raw arguments to find the resource
    import sys

    args = sys.argv[1:]

    # Find the action (command name from context)
    action = None
    resource = None
    command_name = ctx.info_name if ctx else None

    # Map command names to actions
    action_map = {
        "create": "create",
        "add": "create",
        "new": "create",
        "update": "update",
        "modify": "update",
        "mod": "update",
        "edit": "update",
        "set": "update",
        "delete": "delete",
        "del": "delete",
        "remove": "delete",
        "rm": "delete",
        "show": "show",
        "sh": "show",
        "list": "show",
        "ls": "show",
    }

    if command_name:
        action = action_map.get(command_name, command_name)

    # Find resource in args (skip options starting with -)
    for arg in args:
        if arg.startswith("-"):
            continue
        if arg in action_map:
            continue
        # This might be the resource
        resource = arg
        break

    # Try to show resource-specific help
    if action and resource:
        if show_resource_help(action, resource):
            ctx.exit()
            return

    # Show the standard command help
    click.echo(ctx.get_help())
    ctx.exit()


def show_command_help_with_resources(
    zebra_override: Optional[bool] = None,
) -> None:
    """Custom help callback that shows command help plus resource list.

    Args:
        zebra_override: Optional zebra striping override
    """
    # Add the resource list
    console.print("\n[bold]Available Slurm Resources:[/bold]")

    # Get zebra value from override or context
    if zebra_override is not None:
        zebra = zebra_override
    else:
        # Try to get zebra from context, default to False if not available
        try:
            ctx = click.get_current_context()
            zebra = get_zebra(ctx)
        except RuntimeError:
            zebra = False

    table = Table(
        box=SIMPLE_HEAVY,
        pad_edge=False,
        padding=(0, 0),
        row_styles=get_row_styles(zebra),
    )
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
    type=click.Choice(STYLE_OPTIONS),
    default="pretty",
    help="Output style: pretty (default), json, or csv",
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
    "--csv",
    is_flag=True,
    help="Use CSV output format (equivalent to --style csv)",
)
@click.option(
    "--delimiter",
    "-d",
    default=";",
    help="Delimiter for CSV output (default: ';')",
)
@click.option(
    "--zebra",
    "-z",
    is_flag=True,
    help="Use zebra-striped rows in tables (alternating colors)",
)
@click.option(
    "--force-update",
    "-f",
    is_flag=True,
    help="Force update of SLURM data, bypassing cache timeout",
)
@click.option(
    "--yes",
    "-y",
    is_flag=True,
    help="Skip confirmation prompts in delete/update operations",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=None,
    help="Show what would be done without making changes "
    "(also enabled by SLURM_CLI_DRYRUN=y)",
)
@click.option(
    "--no-dry-run",
    is_flag=True,
    help="Override SLURM_CLI_DRYRUN env var and disable dry-run",
)
@click.option(
    "--cache-timeout",
    "-t",
    type=int,
    default=Resource.CACHE_TIMEOUT,
    help=f"SLURM cache timeout in seconds (default: {Resource.CACHE_TIMEOUT})",
)
@click.option(
    "--profile",
    "-P",
    default="default",
    help="Output profile name (default: 'default'). "
    "Profiles are loaded from /etc/slurm/cli.profiles "
    "or ~/.config/slurm-cli.profiles",
)
@click.option(
    "--profile-str",
    "--format",
    "-o",
    "profile_str",
    default=None,
    help="Inline profile string (overrides --profile). "
    "Format: resource.columns=col1,col2;resource.styles.field=style",
)
@click.option(
    "--list-fields",
    default=None,
    is_flag=False,
    flag_value="all",
    is_eager=True,
    expose_value=False,
    callback=list_fields_callback,
    help="List available profile fields. "
    "Optionally specify resource type (e.g., --list-fields=jobs)",
)
@click.pass_context
def main(
    ctx: click.Context,
    style: str,
    pretty: bool,
    json: bool,
    csv: bool,
    delimiter: str,
    zebra: bool,
    force_update: bool,
    yes: bool,
    dry_run: bool,
    no_dry_run: bool,
    cache_timeout: int,
    profile: str,
    profile_str: str,
) -> None:
    """Slurm Swiss Knife - A CLI tool for Slurm cluster management."""
    # Handle convenience flags
    if pretty:
        style = "pretty"
    elif json:
        style = "json"
    elif csv:
        style = "csv"

    # Handle dry-run from env var if not explicitly set
    if dry_run is None:
        env_dry_run = os.environ.get("SLURM_CLI_DRYRUN", "").lower()
        dry_run = env_dry_run in ("y", "yes", "1", "true")

    # Store style, delimiter, zebra, profile, and cache update flag in context
    # for subcommands to access
    ctx.ensure_object(dict)
    ctx.obj["style"] = style
    ctx.obj["delimiter"] = delimiter
    ctx.obj["zebra"] = zebra
    ctx.obj["force_update"] = force_update
    ctx.obj["yes"] = yes
    ctx.obj["dry_run"] = dry_run
    ctx.obj["no_dry_run"] = no_dry_run
    ctx.obj["profile"] = profile
    ctx.obj["profile_str"] = profile_str

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

        command = resolve_command_alias(cmd_name)
        return super().get_command(ctx, command)

    def format_commands(self, ctx, formatter):
        """Custom command formatter that filters out aliases."""
        commands = []
        for name in sorted(COMMANDS.keys()):
            if COMMANDS[name].get("aliases"):
                aliases = f"({', '.join(COMMANDS[name]['aliases'])}) "
            else:
                aliases = ""
            commands.append(
                (name, f"{aliases}{COMMANDS[name]['description']}")
            )

        with formatter.section("Commands"):
            formatter.write_dl(commands)


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
    main.add_command(reconfigure, name="reconfigure")
    main.add_command(ping, name="ping")
    main.add_command(takeover, name="takeover")
    main.add_command(write_config, name="write-config")
    main.add_command(schedloglevel, name="schedloglevel")
    main.add_command(setdebug, name="setdebug")
    main.add_command(bbstat, name="bbstat")
    main.add_command(batch_script, name="batch-script")
    main.add_command(token, name="token")
    main.add_command(assoc_mgr, name="assoc_mgr")
    main.add_command(drain, name="drain")
    main.add_command(undrain, name="undrain")
    main.add_command(reboot, name="reboot")
    main.add_command(cancel_reboot, name="cancel-reboot")
    main.add_command(hold, name="hold")
    main.add_command(release, name="release")
    main.add_command(top, name="top")
    main.add_command(requeue, name="requeue")
    main.add_command(suspend, name="suspend")

    # Modify help text to show aliases inline
    show.help = "Show information about Slurm resources (aliases: get)"
    update.help = (
        "Update Slurm resource fields "
        "(aliases: edit, change, modify)"
    )
    create.help = "Create Slurm resources (aliases: new, add)"
    delete.help = "Delete Slurm resources (aliases: remove, rm)"
    list_resources.help = "List available Slurm resources (aliases: ls)"
    version.help = "Show slurm-cli and slurmctld version (aliases: ver)"
    reconfigure.help = (
        "Reconfigure slurmctld (aliases: reconf, confreload)"
    )
    ping.help = "Ping slurmctld"
    takeover.help = "Take over as primary slurmctld"
    write_config.help = (
        "Write Slurm configuration file (aliases: wconf)"
    )
    batch_script.help = (
        "Run scontrol write batch_script for a job (aliases: bscript)"
    )
    token.help = "Generate JWT authentication token (aliases: tok)"
    drain.help = (
        "Drain nodes (aliases: dr). Reason: -r, --reason, or reason="
    )
    undrain.help = "Undrain/resume nodes (aliases: undr, resume)"
    reboot.help = "Reboot nodes (aliases: reb)"
    cancel_reboot.help = "Cancel pending reboot (aliases: cancel-reb)"
    hold.help = (
        "Hold jobs (aliases: hol). Reason: -r, --reason, or reason="
    )
    release.help = "Release held jobs (aliases: rel)"
    top.help = "Move jobs to top of queue"
    requeue.help = "Requeue jobs (aliases: req)"
    setdebug.help = "Set slurmctld/slurmd debug level (aliases: sd)"
    bbstat.help = "Show burst buffer status (aliases: bbs)"
    suspend.help = "Suspend running jobs (aliases: sus)"
    help.help = "Show help information"


# Show command
@click.command(
    context_settings=CONTEXT_SETTINGS_NO_HELP,
    epilog=get_resources_epilog("show"),
)
@click.argument(
    "resource",
    required=False,
    metavar="RESOURCE",
)
@click.argument("field", required=False, nargs=-1)
@click.option(
    "--verbose", "-v", is_flag=True, help="Enable verbose output"
)
@click.option(
    "--tree",
    "-T",
    is_flag=True,
    help="Show associations in hierarchical tree format",
)
@click.option(
    "--indent",
    default="  ",
    help="Indentation string for tree mode (default: two spaces)",
)
@click.option(
    "--help",
    "-h",
    is_flag=True,
    is_eager=True,
    callback=show_command_help,
    help="Show this message and exit.",
)
@click.option(
    "--list-fields",
    "-L",
    is_flag=True,
    help="List available profile fields for the resource",
)
@common_options
@click.pass_context
def show(
    ctx: click.Context,
    resource: Optional[str],
    field: Tuple[str, ...],
    verbose: bool,
    tree: bool = False,
    indent: str = "  ",
    list_fields: bool = False,
    style: Optional[str] = None,
    pretty: bool = False,
    json: bool = False,
    csv: bool = False,
    zebra: Optional[bool] = None,
    delimiter: Optional[str] = None,
    profile: Optional[str] = None,
    profile_str: Optional[str] = None,
    **kwargs,
) -> None:
    """Show information about Slurm resources (aliases: sh, s)."""
    # Handle --list-fields option
    if list_fields:
        if resource:
            canonical = resolve_resource_alias(resource)
            show_profile_help(canonical)
        else:
            show_all_profile_fields()
        return

    # Convert tuple to first element for backward compatibility
    # (for resources that expect a single field)
    first_field = field[0] if field else None
    if not resource:
        show_command_help(ctx, None, True)
        return

    # Handle command-level style overrides
    if pretty:
        style = "pretty"
    elif json:
        style = "json"
    elif csv:
        style = "csv"

    # Get final values (command-level overrides global)
    style = get_output_style(ctx, style)
    delimiter = get_delimiter(ctx, delimiter)
    zebra = get_zebra(ctx, zebra)
    force_update = get_force_update(ctx)
    profile = get_profile(ctx, profile)
    profile_str = get_profile_str(ctx, profile_str)
    canonical_resource, field, data = ensure_resource_name(
        resource, field, force_update
    )

    # Normalize field to tuple and recompute first_field
    # (ensure_resource_name may return a string when guessing resource type)
    if isinstance(field, str):
        field = (field,)
    first_field = field[0] if field else None

    # Check for --profile-str=help
    if is_profile_help(profile_str):
        show_profile_help(canonical_resource)
        return

    # TODO: eliminate double checking of cached resource
    if canonical_resource[:4] == "conf":
        Config.show(
            data=data,
            style=style,
            delimiter=delimiter,
            profile=profile,
            profile_str=profile_str,
        )
    elif canonical_resource[:3] == "res":
        if first_field:
            Reservation.show(
                name=first_field,
                data=data,
                style=style,
                delimiter=delimiter,
                zebra=zebra,
                profile=profile,
                profile_str=profile_str,
            )
        else:
            Reservation.show(
                data=data,
                style=style,
                delimiter=delimiter,
                zebra=zebra,
                profile=profile,
                profile_str=profile_str,
            )
    elif canonical_resource[:4] == "part":
        if first_field:
            Partition.show(
                name=first_field,
                data=data,
                style=style,
                delimiter=delimiter,
                zebra=zebra,
                profile=profile,
                profile_str=profile_str,
            )
        else:
            Partition.show(
                data=data,
                style=style,
                delimiter=delimiter,
                zebra=zebra,
                profile=profile,
                profile_str=profile_str,
            )
    elif canonical_resource[:4] == "node":
        if field:
            # Check if any field is a node filter (partition=, state=, etc.)
            has_filters = any(is_node_filter(f) for f in field)
            if has_filters:
                # Use resolve_node_filters for all fields (supports exclusions)
                resolved_nodes, _ = resolve_node_filters(
                    list(field), verbose
                )
                if not resolved_nodes:
                    console.print(
                        "[yellow]No nodes matched filters[/yellow]"
                    )
                    return
                # Filter data to only include resolved nodes
                filtered_data = {
                    k: v for k, v in data.items() if k in resolved_nodes
                }
                Node.show(
                    data=filtered_data,
                    style=style,
                    delimiter=delimiter,
                    zebra=zebra,
                    profile=profile,
                    profile_str=profile_str,
                )
            else:
                # Single node name
                Node.show(
                    name=first_field,
                    data=data,
                    style=style,
                    verbose=verbose,
                    delimiter=delimiter,
                    zebra=zebra,
                    profile=profile,
                    profile_str=profile_str,
                )
        else:
            Node.show(
                data=data,
                style=style,
                delimiter=delimiter,
                zebra=zebra,
                profile=profile,
                profile_str=profile_str,
            )
    elif canonical_resource[:4] == "user":
        if first_field:
            User.show(
                name=first_field,
                data=data,
                style=style,
                delimiter=delimiter,
                zebra=zebra,
                profile=profile,
                profile_str=profile_str,
            )
        else:
            User.show(
                data=data,
                style=style,
                delimiter=delimiter,
                zebra=zebra,
                profile=profile,
                profile_str=profile_str,
            )
    elif canonical_resource[:3] == "qos":
        if first_field:
            Qos.show(
                field=first_field,
                style=style,
                delimiter=delimiter,
                zebra=zebra,
                profile=profile,
                profile_str=profile_str,
            )
        else:
            Qos.show(
                style=style,
                delimiter=delimiter,
                zebra=zebra,
                profile=profile,
                profile_str=profile_str,
            )
    elif canonical_resource[:3] == "acc":
        if first_field:
            Account.show(
                field=first_field,
                style=style,
                delimiter=delimiter,
                zebra=zebra,
                profile=profile,
                profile_str=profile_str,
                tree=tree,
            )
        else:
            Account.show(
                style=style,
                delimiter=delimiter,
                zebra=zebra,
                profile=profile,
                profile_str=profile_str,
                tree=tree,
            )
    elif canonical_resource[:5] == "assoc":
        if first_field:
            Association.show(
                field=first_field,
                style=style,
                delimiter=delimiter,
                zebra=zebra,
                profile=profile,
                profile_str=profile_str,
                tree=tree,
                indent=indent,
            )
        else:
            Association.show(
                style=style,
                delimiter=delimiter,
                zebra=zebra,
                profile=profile,
                profile_str=profile_str,
                tree=tree,
                indent=indent,
            )
    elif canonical_resource[:5] == "coord":
        if first_field:
            Coordinator.show(
                field=first_field,
                style=style,
                delimiter=delimiter,
                zebra=zebra,
                profile=profile,
                profile_str=profile_str,
            )
        else:
            Coordinator.show(
                style=style,
                delimiter=delimiter,
                zebra=zebra,
                profile=profile,
                profile_str=profile_str,
            )
    elif canonical_resource[:5] == "event":
        # Events support node filters (like nodes command)
        if field:
            has_filters = any(is_node_filter(f) for f in field)
            if has_filters:
                resolved_nodes, _ = resolve_node_filters(
                    list(field), verbose
                )
                if not resolved_nodes:
                    console.print(
                        "[yellow]No nodes matched filters[/yellow]"
                    )
                    return
                # Pass the resolved nodes as comma-separated list
                Event.show(
                    field=",".join(resolved_nodes),
                    style=style,
                    force_cache_update=force_update,
                    delimiter=delimiter,
                    zebra=zebra,
                    profile=profile,
                    profile_str=profile_str,
                )
            else:
                Event.show(
                    field=first_field,
                    style=style,
                    force_cache_update=force_update,
                    delimiter=delimiter,
                    zebra=zebra,
                    profile=profile,
                    profile_str=profile_str,
                )
        else:
            Event.show(
                field=None,
                style=style,
                force_cache_update=force_update,
                delimiter=delimiter,
                zebra=zebra,
                profile=profile,
                profile_str=profile_str,
            )
    elif canonical_resource[:3] == "job":
        # Jobs support job filters
        if field:
            has_filters = any(is_job_filter(f) for f in field)
            if has_filters:
                resolved_jobs, _ = resolve_job_ids(list(field), verbose)
                if not resolved_jobs:
                    console.print(
                        "[yellow]No jobs matched filters[/yellow]"
                    )
                    return
                # Pass resolved job IDs
                for job_id in resolved_jobs:
                    Job.show(
                        field=job_id,
                        style=style,
                        force_cache_update=force_update,
                        delimiter=delimiter,
                        zebra=zebra,
                        profile=profile,
                        profile_str=profile_str,
                    )
            else:
                Job.show(
                    field=first_field,
                    style=style,
                    force_cache_update=force_update,
                    delimiter=delimiter,
                    zebra=zebra,
                    profile=profile,
                    profile_str=profile_str,
                )
        else:
            Job.show(
                field=None,
                style=style,
                force_cache_update=force_update,
                delimiter=delimiter,
                zebra=zebra,
                profile=profile,
                profile_str=profile_str,
            )
    else:
        console.print(f"[red]Resource '{resource}' not found.[/red]")


# Update command
@click.command(
    context_settings=CONTEXT_SETTINGS_NO_HELP,
    epilog=get_resources_epilog("update"),
)
@click.argument(
    "resource",
    type=click.Choice(get_resource_choices(), case_sensitive=False),
    required=False,
    metavar="RESOURCE",
)
@click.argument("field", required=False)
@click.argument("value", required=False)
@click.argument("names", nargs=-1, required=False)
@click.option(
    "--verbose", "-v", is_flag=True, help="Enable verbose output"
)
@click.option(
    "--yes",
    "-y",
    is_flag=True,
    help="Skip confirmation prompts (same as global -y)",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be updated without making changes",
)
@click.option(
    "--list-fields",
    "-L",
    is_flag=True,
    help="List available fields for the resource",
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
    yes: bool,
    dry_run: bool,
    list_fields: bool = False,
    **kwargs,
) -> None:
    """Update Slurm resource fields (aliases: u, edit, mod, modify)."""
    # Handle --list-fields option
    if list_fields:
        if resource:
            canonical = resolve_resource_alias(resource)
            show_profile_help(canonical)
        else:
            show_all_profile_fields()
        return

    # Combine local and global dry-run settings
    dry_run = get_dry_run(ctx, dry_run)

    # Combine local and global --yes options
    # skip_confirm = get_skip_confirm(
    #     ctx, yes
    # )  # noqa: F841 - for future use

    # Show help if no resource, field, or value is provided
    if not resource or not field or not value:
        show_command_help(ctx, None, True)
        return

    # Resolve resource alias to canonical name
    canonical_resource = resolve_resource_alias(resource)

    # Coordinators do not support update operation
    if canonical_resource[:5] == "coord":
        Coordinator.update()
        return

    # Parse additional arguments into key-value pairs
    update_options = {}
    # Include value if it's a key=value format
    if value and "=" in value:
        key, value_part = value.split("=", 1)
        update_options[key] = value_part
    if names:
        for arg in names:
            if "=" in arg:
                # Handle key=value format
                key, value_part = arg.split("=", 1)
                update_options[key] = value_part
            else:
                # Treat as a simple value
                update_options[arg] = None

    # Resolve node filters in options (e.g., nodes=partition=cpu)
    update_options = resolve_node_filters_in_options(
        update_options, verbose
    )
    if update_options is None:
        return  # Node filter matched nothing, abort

    # Special handling for accounts/associations/users/qos
    # with WHERE/SET syntax
    # Format: modify accounts key=value [...] set newkey=newvalue [...]
    if (
        canonical_resource[:3] == "acc"
        or canonical_resource[:5] == "assoc"
        or canonical_resource[:4] == "user"
        or canonical_resource[:3] == "qos"
    ) and "=" in field:
        # WHERE mode - collect all args and split on "set"
        all_args = [field, value] + list(names) if value else [field]
        where_conditions = []
        set_values = []
        found_set = False

        for arg in all_args:
            if arg and arg.lower() == "set":
                found_set = True
                continue
            if arg:
                if found_set:
                    set_values.append(arg)
                else:
                    where_conditions.append(arg)

        if not found_set or not set_values:
            console.print(
                "[red]WHERE mode requires 'set' keyword followed by "
                "values to set.[/red]"
            )
            console.print(
                f"Usage: modify {canonical_resource} key=value [...] set "
                "newkey=newvalue [...]"
            )
            return

        if canonical_resource[:5] == "assoc":
            Association.update(
                "",
                verbose,
                dry_run=dry_run,
                where_conditions=where_conditions,
                set_values=set_values,
            )
        elif canonical_resource[:4] == "user":
            User.update(
                "",
                verbose,
                dry_run=dry_run,
                where_conditions=where_conditions,
                set_values=set_values,
            )
        elif canonical_resource[:3] == "qos":
            Qos.update(
                "",
                verbose,
                dry_run=dry_run,
                where_conditions=where_conditions,
                set_values=set_values,
            )
        else:
            Account.update(
                "",
                verbose,
                dry_run=dry_run,
                where_conditions=where_conditions,
                set_values=set_values,
            )
        return

    # Build the update message
    if names:
        additional_args = " ".join(f"'{arg}'" for arg in names)
        if verbose and not dry_run:
            console.print(
                f"Updating {canonical_resource} {field} '{value}' "
                f"{additional_args}"
            )

        if canonical_resource[:4] == "part":
            Partition.update(
                field, verbose, dry_run=dry_run, **update_options
            )
        elif canonical_resource[:4] == "node":
            # Resolve node filter if field is a filter expression
            if is_node_filter(field):
                resolved = resolve_nodes_value(field, verbose)
                if not resolved:
                    console.print(
                        f"[red]Error: Node filter '{field}' "
                        f"matched no nodes. Aborting.[/red]"
                    )
                    return
                field = resolved
            Node.update(
                field, verbose, dry_run=dry_run, **update_options
            )
        elif canonical_resource[:4] == "user":
            User.update(
                field, verbose, dry_run=dry_run, **update_options
            )
        elif canonical_resource[:3] == "qos":
            Qos.update(
                field, verbose, dry_run=dry_run, **update_options
            )
        elif canonical_resource[:3] == "acc":
            Account.update(
                field, verbose, dry_run=dry_run, **update_options
            )
        elif canonical_resource[:5] == "assoc":
            Association.update(
                field, verbose, dry_run=dry_run, **update_options
            )
        elif canonical_resource[:3] == "res":
            Reservation.update(
                field, verbose, dry_run=dry_run, **update_options
            )
        elif canonical_resource[:5] == "coord":
            Coordinator.update(
                field, verbose, dry_run=dry_run, **update_options
            )
        elif canonical_resource[:4] == "conf":
            Config.update(
                field, verbose, dry_run=dry_run, **update_options
            )
        elif canonical_resource[:3] == "job":
            # Resolve job filter if field is a filter expression
            if is_job_filter(field):
                job_ids, _ = resolve_job_ids([field], verbose)
                if not job_ids:
                    console.print(
                        f"[red]Error: Job filter '{field}' "
                        f"matched no jobs. Aborting.[/red]"
                    )
                    return
                for job_id in job_ids:
                    Job.update(
                        job_id,
                        verbose,
                        dry_run=dry_run,
                        **update_options,
                    )
            else:
                Job.update(
                    field, verbose, dry_run=dry_run, **update_options
                )
        else:
            console.print(
                f"[red]Resource '{canonical_resource}' not found.[/red]"
            )
    else:
        # Simple mode: modify accounts/associations NAME key=value
        if canonical_resource[:3] == "acc":
            Account.update(
                field,
                verbose,
                dry_run=dry_run,
                **{value.split("=")[0]: value.split("=")[1]}
                if "=" in value
                else {},
            )
        elif canonical_resource[:5] == "assoc":
            Association.update(
                field,
                verbose,
                dry_run=dry_run,
                **{value.split("=")[0]: value.split("=")[1]}
                if "=" in value
                else {},
            )
        elif canonical_resource[:3] == "qos":
            Qos.update(
                field,
                verbose,
                dry_run=dry_run,
                **{value.split("=")[0]: value.split("=")[1]}
                if "=" in value
                else {},
            )
        elif canonical_resource[:4] == "user":
            User.update(
                field,
                verbose,
                dry_run=dry_run,
                **{value.split("=")[0]: value.split("=")[1]}
                if "=" in value
                else {},
            )
        elif canonical_resource[:4] == "node":
            # Resolve node filter if field is a filter expression
            if is_node_filter(field):
                resolved = resolve_nodes_value(field, verbose)
                if not resolved:
                    console.print(
                        f"[red]Error: Node filter '{field}' "
                        f"matched no nodes. Aborting.[/red]"
                    )
                    return
                field = resolved
            Node.update(
                field, verbose, dry_run=dry_run, **update_options
            )
        elif canonical_resource[:4] == "part":
            Partition.update(
                field, verbose, dry_run=dry_run, **update_options
            )
        elif canonical_resource[:3] == "res":
            Reservation.update(
                field, verbose, dry_run=dry_run, **update_options
            )
        elif canonical_resource[:3] == "job":
            # Resolve job filter if field is a filter expression
            if is_job_filter(field):
                job_ids, _ = resolve_job_ids([field], verbose)
                if not job_ids:
                    console.print(
                        f"[red]Error: Job filter '{field}' "
                        f"matched no jobs. Aborting.[/red]"
                    )
                    return
                for job_id in job_ids:
                    Job.update(
                        job_id,
                        verbose,
                        dry_run=dry_run,
                        **update_options,
                    )
            else:
                Job.update(
                    field, verbose, dry_run=dry_run, **update_options
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


# Create command
@click.command(
    context_settings=CONTEXT_SETTINGS_NO_HELP,
    epilog=get_resources_epilog("create"),
)
@click.argument(
    "resource",
    type=click.Choice(get_resource_choices(), case_sensitive=False),
    required=False,
    metavar="RESOURCE",
)
@click.argument("field", required=False)
# @click.argument("value", required=False)
@click.argument("names", nargs=-1, required=False)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be updated without making changes",
)
@click.option(
    "--verbose", "-v", is_flag=True, help="Enable verbose output"
)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="Skip confirmation prompts",
)
@click.option(
    "--yes",
    "-y",
    is_flag=True,
    help="Skip confirmation prompts (alias for --force)",
)
@click.option(
    "--list-fields",
    "-L",
    is_flag=True,
    help="List available fields for the resource",
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
    force: bool,
    yes: bool,
    list_fields: bool = False,
    **kwargs,
) -> None:
    """Create Slurm resource fields (aliases: c, new, add)."""
    # Handle --list-fields option
    if list_fields:
        if resource:
            canonical = resolve_resource_alias(resource)
            show_profile_help(canonical)
        else:
            show_all_profile_fields()
        return

    # Show help if no resource, field, or value is provided
    if not resource or not field:
        # or not value:
        show_command_help(ctx, None, True)
        return

    # Combine local and global dry-run settings
    dry_run = get_dry_run(ctx, dry_run)

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

    # Resolve node filters in options (e.g., nodes=partition=cpu)
    create_options = resolve_node_filters_in_options(
        create_options, verbose
    )
    if create_options is None:
        return  # Node filter matched nothing, abort

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
            # Support name= syntax: if field contains =, parse it as option
            user_name = field
            if "=" in field:
                key, value_part = field.split("=", 1)
                create_options[key] = value_part
                # Get name from options
                user_name = create_options.pop("name", None)
                if not user_name:
                    console.print(
                        "[red]Error: User name required. Use 'name=' or "
                        "provide name as first argument.[/red]"
                    )
                    return

            # Check if account or wckey is specified
            skip_confirm = get_skip_confirm(ctx, yes, force)
            has_account = any(
                k.lower() in ("account", "defaultaccount")
                for k in create_options
            )
            has_wckey = any(
                k.lower() in ("wckey", "defaultwckey")
                for k in create_options
            )
            if not has_account and not has_wckey:
                console.print(
                    "[yellow]Warning: Neither 'account' nor 'wckey' "
                    "is specified.[/yellow]"
                )
                console.print(
                    "[yellow]User creation will likely fail without "
                    "an account association.[/yellow]"
                )
                if not skip_confirm:
                    if not confirm_single_key(
                        "Do you want to continue?"
                    ):
                        console.print("Aborted.")
                        return

            User.create(user_name, verbose, **create_options)
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
            # Parse first arg if it's a key=value
            if "=" in field:
                key, value_part = field.split("=", 1)
                create_options[key] = value_part
                user_name = None
            else:
                user_name = field

            # Get user from options if not set from positional arg
            # Handle name= or user= keys
            if not user_name:
                user_name = create_options.pop(
                    "name", None
                ) or create_options.pop("user", None)

            Coordinator.create(user_name, verbose, **create_options)
        elif canonical_resource[:5] == "assoc":
            # Parse first arg if it's a key=value
            if "=" in field:
                key, value_part = field.split("=", 1)
                create_options[key] = value_part
                user_name = None
            else:
                user_name = field

            # Get name from options if not set from positional arg
            # Accept both name= and user= as the username
            if not user_name:
                user_name = create_options.pop(
                    "name", None
                ) or create_options.pop("user", None)

            if not user_name:
                console.print(
                    "[red]Error: User name required. Use 'name=' or 'user=' "
                    "or provide name as first argument.[/red]"
                )
                return
            Association.create(user_name, verbose, **create_options)
        else:
            console.print(
                f"[red]Resource '{canonical_resource}' not found.[/red]"
            )


# delete command
@click.command(
    context_settings=CONTEXT_SETTINGS_NO_HELP,
    epilog=get_resources_epilog("delete"),
)
@click.argument(
    "resource",
    type=click.Choice(get_resource_choices(), case_sensitive=False),
    required=False,
    metavar="RESOURCE",
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
    "--yes",
    "-y",
    is_flag=True,
    help="Skip confirmation prompts (same as global -y)",
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
    "--list-fields",
    "-L",
    is_flag=True,
    help="List available fields for the resource",
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
    yes: bool,
    dry_run: bool,
    verbose: bool,
    list_fields: bool = False,
    **kwargs,
) -> None:  # noqa: E501
    """Delete Slurm resources (aliases: del, d, remove, rem, rm)."""
    # Handle --list-fields option
    if list_fields:
        if resource:
            canonical = resolve_resource_alias(resource)
            show_profile_help(canonical)
        else:
            show_all_profile_fields()
        return

    # Resolve resource alias to canonical name
    if not resource:
        show_command_help(ctx, None, True)
        return

    # Combine local and global dry-run settings
    dry_run = get_dry_run(ctx, dry_run)

    # Combine local and global --yes/--force options
    skip_confirm = get_skip_confirm(ctx, yes, force)

    canonical_resource = resolve_resource_alias(resource)

    # Handle multiple names - prioritize positional names over --name option
    if names:
        resource_names = list(names)
    elif name:
        resource_names = [name]
    else:
        resource_names = []

    # Special handling for associations - all args are filter conditions
    if canonical_resource == "associations":
        if not resource_names:
            console.print(
                "[red]No conditions specified. Use key=value pairs "
                "(e.g., user=john partition=batch)[/red]"
            )
            return

        # All names are filter conditions for associations
        conditions_str = " ".join(resource_names)

        if dry_run:
            console.print(
                f"[yellow]DRY RUN:[/yellow] Would delete associations "
                f"where {conditions_str}"
            )
            return

        if not skip_confirm and not confirm_single_key(
            f"Are you sure you want to delete associations "
            f"where {conditions_str}?"
        ):
            console.print("[red]Operation cancelled.[/red]")
            raise click.Abort()

        Association.delete(resource_names, dry_run=dry_run, force=True)
        return

    # Special handling for coordinators - require name= and account=
    if canonical_resource[:5] == "coord":
        if not resource_names:
            show_resource_help("delete", "coordinators")
            return

        # Parse coordinator delete options from all args
        coord_opts = {}
        for arg in resource_names:
            if arg and "=" in arg:
                k, v = arg.split("=", 1)
                coord_opts[k] = v

        account = coord_opts.get("account")
        user = coord_opts.get("name") or coord_opts.get("user")

        if not account or not user:
            show_resource_help("delete", "coordinators")
            return

        if dry_run:
            console.print(
                f"[yellow]DRY RUN:[/yellow] Would delete coordinator "
                f"'{user}' from account '{account}'"
            )
            return

        if not skip_confirm and not confirm_single_key(
            f"Delete coordinator '{user}' from account '{account}'?"
        ):
            console.print("[red]Operation cancelled.[/red]")
            raise click.Abort()

        Coordinator.delete(
            account=account,
            names=[user],
            verbose=verbose,
        )
        return

    # Special handling for jobs - collect all job IDs first
    if canonical_resource[:3] == "job":
        if not resource_names or resource_names == [None]:
            # No job IDs or filters specified - show help
            show_resource_help("delete", "jobs")
            return

        # Use job_filter to resolve all arguments to job IDs
        args = [n for n in resource_names if n]
        job_ids, user_filters = resolve_job_ids(args, verbose)

        # Sort job IDs for consistent display
        sorted_job_ids = sorted(
            job_ids, key=lambda x: int(x.split("_")[0])
        )

        # Check if any jobs were found
        if not sorted_job_ids and not user_filters:
            console.print(
                "[yellow]No jobs found matching the specified filter(s).[/yellow]"
            )
            return

        if dry_run:
            for user in user_filters:
                console.print(
                    f"[yellow]DRY RUN:[/yellow] "
                    f"Would cancel ALL jobs for user: {user}"
                )
            if sorted_job_ids:
                console.print(
                    f"[yellow]DRY RUN:[/yellow] "
                    f"Would cancel {len(sorted_job_ids)} job(s): "
                    f"{', '.join(sorted_job_ids)}"
                )
            return

        # Confirmation
        if not skip_confirm:
            confirm_parts = []
            if user_filters:
                confirm_parts.append(
                    f"ALL jobs for user(s): {', '.join(user_filters)}"
                )
            if sorted_job_ids:
                confirm_parts.append(
                    f"{len(sorted_job_ids)} job(s): "
                    f"{', '.join(sorted_job_ids)}"
                )
            if confirm_parts:
                if not confirm_single_key(
                    f"Cancel {' and '.join(confirm_parts)}?"
                ):
                    console.print("[red]Operation cancelled.[/red]")
                    raise click.Abort()

        # Cancel by user (scancel -u USER)
        for user in user_filters:
            console.print(
                f"[yellow]Cancelling ALL jobs for user: {user}[/yellow]"
            )
            Job._cancel_by_user(user, verbose=verbose)

        # Cancel specific job IDs
        if sorted_job_ids:
            Job._cancel_jobs(sorted_job_ids, verbose=verbose)
        return

    # Standard handling for other resources
    if not resource_names:
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
        if not skip_confirm and not confirm_single_key(
            f"Are you sure you want to delete {canonical_resource}"
            + (f" '{resource_name}'" if resource_name else "")
            + "?"
        ):
            console.print("[red]Operation cancelled.[/red]")
            raise click.Abort()

        if resource_name:
            # Call the appropriate resource delete method
            if canonical_resource[:3] == "qos":
                Qos.delete(resource_name, verbose=verbose)
            elif canonical_resource[:4] == "user":
                User.delete(resource_name, verbose=verbose)
            elif canonical_resource[:3] == "acc":
                Account.delete(resource_name)
            elif canonical_resource[:3] == "res":
                Reservation.delete(resource_name)
            elif canonical_resource[:4] == "part":
                Partition.delete(resource_name)
            elif canonical_resource[:4] == "node":
                Node.delete(resource_name, verbose=verbose)
            # Note: coordinators handled above with special logic
            else:
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
    """Print bash autocomplete function."""
    # Dynamically extract options from the main CLI group
    main_cmd = main
    short_opts = []
    long_opts = []
    option_handlers = []

    # Extract all options from the main command
    for param in main_cmd.params:
        if isinstance(param, click.Option):
            opts = param.opts
            param_name = param.name

            # Collect short and long option names
            for opt in opts:
                if opt.startswith("--"):
                    long_opts.append(opt)
                elif opt.startswith("-"):
                    short_opts.append(opt)

            # Generate handler cases
            opts_pattern = "|".join(opts)

            # Special handling for options with arguments
            if isinstance(param.type, click.Choice):
                choices = " ".join(param.type.choices)
                option_handlers.append(
                    f"""        {opts_pattern})
            if [[ $((i+1)) -lt ${{#COMP_WORDS[@]}} ]]; then
                opts[{param_name}]="${{COMP_WORDS[$((i+1))]}}"
                ((i++))
            else
                COMPREPLY=($(compgen -W "{choices}" -- "$cur"))
                return
            fi
            ;;"""
                )
            elif param.is_flag:
                option_handlers.append(
                    f"""        {opts_pattern})
            opts[{param_name}]="1"
            ;;"""
                )
            elif param.type.name in ["text", "int", "float"]:
                option_handlers.append(
                    f"""        {opts_pattern})
            if [[ $((i+1)) -lt ${{#COMP_WORDS[@]}} ]]; then
                opts[{param_name}]="${{COMP_WORDS[$((i+1))]}}"
                ((i++))
            fi
            ;;"""
                )

    # Build the options string for completion
    all_opts_str = " ".join(short_opts + long_opts)

    # Generate the handler switch case
    handlers_str = "\n".join(option_handlers)

    # Generate command case patterns from COMMANDS config
    command_case_patterns = generate_bash_command_case()
    all_commands_str = get_all_command_names()

    # Generate resource case patterns from RESOURCES config
    resource_case_patterns = generate_bash_resource_case()
    # all_resources_str = get_all_resource_names()

    # Print the script with proper escaping for bash variables
    print(
        f"""
# Reservation autocomplete function
_slurm_cli_initialize_autocomplete() {{

    # Check for optional CLI options and print their values for debugging
    local -A opts=()
    local i=1
    local cur="${{COMP_WORDS[COMP_CWORD]}}"
    local prev="${{COMP_WORDS[COMP_CWORD-1]}}"

    while [[ $i -lt ${{COMP_CWORD}} ]]; do
        arg="${{COMP_WORDS[$i]}}"
        case "$arg" in
{handlers_str}
        *)
            break
            ;;
        esac
        ((i++))
    done

    if [[ ${{COMP_WORDS[COMP_CWORD]:0:1}} == "-" ]]; then
        COMPREPLY=($(compgen -W "{all_opts_str}" -- "$cur"))
        return
    fi

    # Get command and resource name if any
    local cmd=""
    local resource=""
    cmd="${{COMP_WORDS[$i]}}"

    # Find resource by skipping over any options (words starting with -)
    local j=$((i+1))
    while [[ $j -lt ${{#COMP_WORDS[@]}} ]]; do
        local word="${{COMP_WORDS[$j]}}"
        if [[ "$word" != -* ]]; then
            resource="$word"
            break
        fi
        # Skip option value if this option takes an argument
        case "$word" in
            --style|--delimiter|-d|-t|--cache-timeout)
                ((j++))
                ;;
        esac
        ((j++))
    done
    # echo -e "\\nCOMP_CWORD=$COMP_CWORD; i=$i j=$j \\
    # COMP_WORDS=${{COMP_WORDS[@]}} \\
    # Current=${{COMP_WORDS[COMP_CWORD]}} cmd=$cmd resource=$resource"

    # Guess the command by prefix - generated from COMMANDS config
    local guessed="no"
    case "$cmd" in
{command_case_patterns}
        *)
            ;;
    esac
    if [[ $i == $((COMP_CWORD)) ]]; then
        if [[ $guessed != "no" ]]; then
            COMPREPLY=($(compgen -W "$guessed" -- "$cur"))
            return
        else
            COMPREPLY=($(compgen -W "{all_commands_str} {all_opts_str}" -- "$cur"))
            return
        fi
    fi

    # Handle standalone commands that don't take resource arguments
    case "$cmd" in
        version|ping|reconfigure|takeover)
            # These commands take -v/--verbose and -h/--help options
            COMPREPLY=($(compgen -W "-v --verbose -h --help" -- "$cur"))
            return
            ;;
        token)
            # Token command takes lifespan= and username= options
            if [[ "$cur" == *=* ]]; then
                local key="${{cur%%=*}}"
                local val="${{cur#*=}}"
                case "$key" in
                    lifespan)
                        COMPREPLY=($(compgen -W "lifespan=1h lifespan=30m lifespan=1:00:00 lifespan=infinite" -- "$cur"))
                        ;;
                    username)
                        local users="$(_slurm_cache_users)"
                        COMPREPLY=($(compgen -W "${{users// / username=}}" -- "$cur"))
                        [[ ${{#COMPREPLY[@]}} -gt 0 ]] && COMPREPLY=("${{COMPREPLY[@]/#/username=}}")
                        ;;
                esac
            else
                COMPREPLY=($(compgen -W "lifespan= username= -v --verbose -h --help" -- "$cur"))
            fi
            return
            ;;
        assoc_mgr)
            # assoc_mgr command takes users=, accounts=, qos=, flags= options
            local assoc_flags="users assoc qos"
            if [[ "$cur" == --* ]]; then
                COMPREPLY=($(compgen -W "--verbose --dry-run --help" -- "$cur"))
            # Handle users=account= filter - only when cur is part of the filter
            elif [[ "$cur" == users=account=* ]]; then
                # cur contains full users=account=... pattern
                local cached_accounts="$(_slurm_cache_accounts)"
                local acct_val="${{cur#users=account=}}"
                COMPREPLY=($(compgen -W "$cached_accounts" -- "$acct_val"))
                [[ ${{#COMPREPLY[@]}} -gt 0 ]] && COMPREPLY=("${{COMPREPLY[@]/#/users=account=}}")
            elif [[ "$prev" == "=" && "${{COMP_WORDS[COMP_CWORD-2]}}" == "account" && "$COMP_LINE" == *users=account=* ]]; then
                # Bash split: users = account = <value>
                local cached_accounts="$(_slurm_cache_accounts)"
                COMPREPLY=($(compgen -W "$cached_accounts" -- "$cur"))
            elif _slurm_parse_keyval "$cur" "$prev"; then
                case "$_key" in
                    flags)
                        _slurm_complete_value "$assoc_flags" "$_key" "$_val" "$cur"
                        ;;
                    users)
                        # Show account= filter first, then users
                        local cached_users="$(_slurm_cache_users)"
                        COMPREPLY=($(compgen -W "account= $cached_users" -- "$_val"))
                        [[ $cur == *=* && ${{#COMPREPLY[@]}} -gt 0 ]] && COMPREPLY=("${{COMPREPLY[@]/#/users=}}")
                        ;;
                    accounts)
                        _slurm_complete_value "$(_slurm_cache_accounts)" "$_key" "$_val" "$cur"
                        ;;
                    qos)
                        _slurm_complete_value "$(_slurm_cache_qos)" "$_key" "$_val" "$cur"
                        ;;
                esac
            else
                COMPREPLY=($(compgen -W "users= accounts= qos= flags= -v --verbose --dry-run -h --help" -- "$cur"))
            fi
            return
            ;;
        drain)
            # Drain command takes nodes, filters (with optional - prefix for exclusion),
            # and optional --reason/-r or reason=
            local node_filters="partition= state= user= reservation= drainreason="
            local neg_filters="not:partition= not:state= not:user= not:reservation= not:drainreason="
            local node_states="idle alloc drain down mixed comp"
            if [[ "$cur" == --* ]]; then
                COMPREPLY=($(compgen -W "--reason --verbose --help" -- "$cur"))
            elif [[ "$prev" == "-r" || "$prev" == "--reason" ]]; then
                # Reason value - no completion
                return
            elif [[ "$cur" == reason=* ]] || [[ "$prev" == "reason" && "${{COMP_WORDS[COMP_CWORD-1]}}" == "=" ]]; then
                # reason= value - no completion
                return
            # Exclusion filters with not: prefix (handle both "cur=not:filter=val" and bash splitting on =)
            elif [[ "$cur" == not:partition=* ]] || [[ "$prev" == "=" && "${{COMP_WORDS[COMP_CWORD-2]}}" == "not:partition" ]]; then
                local val="${{cur#not:partition=}}"
                [[ "$prev" == "=" ]] && val="$cur"
                local cached_partitions="$(_slurm_cache_partitions)"
                COMPREPLY=($(compgen -W "$cached_partitions" -- "$val"))
                [[ ${{#COMPREPLY[@]}} -gt 0 ]] && COMPREPLY=("${{COMPREPLY[@]/#/not:partition=}}")
            elif [[ "$cur" == not:state=* ]] || [[ "$prev" == "=" && "${{COMP_WORDS[COMP_CWORD-2]}}" == "not:state" ]]; then
                local val="${{cur#not:state=}}"
                [[ "$prev" == "=" ]] && val="$cur"
                COMPREPLY=($(compgen -W "$node_states" -- "$val"))
                [[ ${{#COMPREPLY[@]}} -gt 0 ]] && COMPREPLY=("${{COMPREPLY[@]/#/not:state=}}")
            elif [[ "$cur" == not:user=* ]] || [[ "$prev" == "=" && "${{COMP_WORDS[COMP_CWORD-2]}}" == "not:user" ]]; then
                local val="${{cur#not:user=}}"
                [[ "$prev" == "=" ]] && val="$cur"
                local users="$(_slurm_cache_users)"
                COMPREPLY=($(compgen -W "$users" -- "$val"))
                [[ ${{#COMPREPLY[@]}} -gt 0 ]] && COMPREPLY=("${{COMPREPLY[@]/#/not:user=}}")
            elif [[ "$cur" == not:reservation=* ]] || [[ "$prev" == "=" && "${{COMP_WORDS[COMP_CWORD-2]}}" == "not:reservation" ]]; then
                local val="${{cur#not:reservation=}}"
                [[ "$prev" == "=" ]] && val="$cur"
                local reservations="$(_slurm_cache_reservations)"
                COMPREPLY=($(compgen -W "$reservations" -- "$val"))
                [[ ${{#COMPREPLY[@]}} -gt 0 ]] && COMPREPLY=("${{COMPREPLY[@]/#/not:reservation=}}")
            # Positive filters
            elif [[ "$cur" == partition=* ]] || [[ "$prev" == "=" && "${{COMP_WORDS[COMP_CWORD-2]}}" == "partition" ]]; then
                local val="${{cur#partition=}}"
                [[ "$prev" == "=" ]] && val="$cur"
                local cached_partitions="$(_slurm_cache_partitions)"
                COMPREPLY=($(compgen -W "$cached_partitions" -- "$val"))
                [[ ${{#COMPREPLY[@]}} -gt 0 && "$cur" == *=* ]] && COMPREPLY=("${{COMPREPLY[@]/#/partition=}}")
            elif [[ "$cur" == state=* ]] || [[ "$prev" == "=" && "${{COMP_WORDS[COMP_CWORD-2]}}" == "state" ]]; then
                local val="${{cur#state=}}"
                [[ "$prev" == "=" ]] && val="$cur"
                COMPREPLY=($(compgen -W "$node_states" -- "$val"))
                [[ ${{#COMPREPLY[@]}} -gt 0 && "$cur" == *=* ]] && COMPREPLY=("${{COMPREPLY[@]/#/state=}}")
            elif [[ "$cur" == user=* ]] || [[ "$prev" == "=" && "${{COMP_WORDS[COMP_CWORD-2]}}" == "user" ]]; then
                local val="${{cur#user=}}"
                [[ "$prev" == "=" ]] && val="$cur"
                local users="$(_slurm_cache_users)"
                COMPREPLY=($(compgen -W "$users" -- "$val"))
                [[ ${{#COMPREPLY[@]}} -gt 0 && "$cur" == *=* ]] && COMPREPLY=("${{COMPREPLY[@]/#/user=}}")
            elif [[ "$cur" == reservation=* ]] || [[ "$prev" == "=" && "${{COMP_WORDS[COMP_CWORD-2]}}" == "reservation" ]]; then
                local val="${{cur#reservation=}}"
                [[ "$prev" == "=" ]] && val="$cur"
                local reservations="$(_slurm_cache_reservations)"
                COMPREPLY=($(compgen -W "$reservations" -- "$val"))
                [[ ${{#COMPREPLY[@]}} -gt 0 && "$cur" == *=* ]] && COMPREPLY=("${{COMPREPLY[@]/#/reservation=}}")
            else
                local cached_nodes="$(_slurm_cache_nodes)"
                COMPREPLY=($(compgen -W "$node_filters $neg_filters reason= -r --reason -v --verbose -h --help $cached_nodes" -- "$cur"))
            fi
            return
            ;;
        undrain)
            # Undrain command takes nodes and filters (with optional - prefix for exclusion)
            local node_filters="partition= state= user= reservation= drainreason="
            local neg_filters="not:partition= not:state= not:user= not:reservation= not:drainreason="
            local node_states="idle alloc drain down mixed comp"
            if [[ "$cur" == --* ]]; then
                COMPREPLY=($(compgen -W "--verbose --help" -- "$cur"))
            # Exclusion filters with not: prefix (handle both "cur=not:filter=val" and bash splitting on =)
            elif [[ "$cur" == not:partition=* ]] || [[ "$prev" == "=" && "${{COMP_WORDS[COMP_CWORD-2]}}" == "not:partition" ]]; then
                local val="${{cur#not:partition=}}"
                [[ "$prev" == "=" ]] && val="$cur"
                local cached_partitions="$(_slurm_cache_partitions)"
                COMPREPLY=($(compgen -W "$cached_partitions" -- "$val"))
                [[ ${{#COMPREPLY[@]}} -gt 0 ]] && COMPREPLY=("${{COMPREPLY[@]/#/not:partition=}}")
            elif [[ "$cur" == not:state=* ]] || [[ "$prev" == "=" && "${{COMP_WORDS[COMP_CWORD-2]}}" == "not:state" ]]; then
                local val="${{cur#not:state=}}"
                [[ "$prev" == "=" ]] && val="$cur"
                COMPREPLY=($(compgen -W "$node_states" -- "$val"))
                [[ ${{#COMPREPLY[@]}} -gt 0 ]] && COMPREPLY=("${{COMPREPLY[@]/#/not:state=}}")
            elif [[ "$cur" == not:user=* ]] || [[ "$prev" == "=" && "${{COMP_WORDS[COMP_CWORD-2]}}" == "not:user" ]]; then
                local val="${{cur#not:user=}}"
                [[ "$prev" == "=" ]] && val="$cur"
                local users="$(_slurm_cache_users)"
                COMPREPLY=($(compgen -W "$users" -- "$val"))
                [[ ${{#COMPREPLY[@]}} -gt 0 ]] && COMPREPLY=("${{COMPREPLY[@]/#/not:user=}}")
            elif [[ "$cur" == not:reservation=* ]] || [[ "$prev" == "=" && "${{COMP_WORDS[COMP_CWORD-2]}}" == "not:reservation" ]]; then
                local val="${{cur#not:reservation=}}"
                [[ "$prev" == "=" ]] && val="$cur"
                local reservations="$(_slurm_cache_reservations)"
                COMPREPLY=($(compgen -W "$reservations" -- "$val"))
                [[ ${{#COMPREPLY[@]}} -gt 0 ]] && COMPREPLY=("${{COMPREPLY[@]/#/not:reservation=}}")
            # Positive filters
            elif [[ "$cur" == partition=* ]] || [[ "$prev" == "=" && "${{COMP_WORDS[COMP_CWORD-2]}}" == "partition" ]]; then
                local val="${{cur#partition=}}"
                [[ "$prev" == "=" ]] && val="$cur"
                local cached_partitions="$(_slurm_cache_partitions)"
                COMPREPLY=($(compgen -W "$cached_partitions" -- "$val"))
                [[ ${{#COMPREPLY[@]}} -gt 0 && "$cur" == *=* ]] && COMPREPLY=("${{COMPREPLY[@]/#/partition=}}")
            elif [[ "$cur" == state=* ]] || [[ "$prev" == "=" && "${{COMP_WORDS[COMP_CWORD-2]}}" == "state" ]]; then
                local val="${{cur#state=}}"
                [[ "$prev" == "=" ]] && val="$cur"
                COMPREPLY=($(compgen -W "$node_states" -- "$val"))
                [[ ${{#COMPREPLY[@]}} -gt 0 && "$cur" == *=* ]] && COMPREPLY=("${{COMPREPLY[@]/#/state=}}")
            elif [[ "$cur" == user=* ]] || [[ "$prev" == "=" && "${{COMP_WORDS[COMP_CWORD-2]}}" == "user" ]]; then
                local val="${{cur#user=}}"
                [[ "$prev" == "=" ]] && val="$cur"
                local users="$(_slurm_cache_users)"
                COMPREPLY=($(compgen -W "$users" -- "$val"))
                [[ ${{#COMPREPLY[@]}} -gt 0 && "$cur" == *=* ]] && COMPREPLY=("${{COMPREPLY[@]/#/user=}}")
            elif [[ "$cur" == reservation=* ]] || [[ "$prev" == "=" && "${{COMP_WORDS[COMP_CWORD-2]}}" == "reservation" ]]; then
                local val="${{cur#reservation=}}"
                [[ "$prev" == "=" ]] && val="$cur"
                local reservations="$(_slurm_cache_reservations)"
                COMPREPLY=($(compgen -W "$reservations" -- "$val"))
                [[ ${{#COMPREPLY[@]}} -gt 0 && "$cur" == *=* ]] && COMPREPLY=("${{COMPREPLY[@]/#/reservation=}}")
            else
                local cached_nodes="$(_slurm_cache_nodes)"
                COMPREPLY=($(compgen -W "$node_filters $neg_filters -v --verbose -h --help $cached_nodes" -- "$cur"))
            fi
            return
            ;;
        reboot)
            # Reboot command takes nodes, filters, asap, nextstate=, reason=
            local node_filters="partition= state= user= reservation= drainreason="
            local neg_filters="not:partition= not:state= not:user= not:reservation= not:drainreason="
            local node_states="idle alloc drain down mixed comp"
            local nextstates="RESUME DOWN"
            if [[ "$cur" == --* ]]; then
                COMPREPLY=($(compgen -W "--verbose --help" -- "$cur"))
            elif [[ "$cur" == nextstate=* ]] || [[ "$prev" == "=" && "${{COMP_WORDS[COMP_CWORD-2]}}" == "nextstate" ]]; then
                local val="${{cur#nextstate=}}"
                [[ "$prev" == "=" ]] && val="$cur"
                COMPREPLY=($(compgen -W "$nextstates" -- "$val"))
                [[ ${{#COMPREPLY[@]}} -gt 0 && "$cur" == *=* ]] && COMPREPLY=("${{COMPREPLY[@]/#/nextstate=}}")
            elif [[ "$cur" == reason=* ]] || [[ "$prev" == "reason" && "${{COMP_WORDS[COMP_CWORD-1]}}" == "=" ]]; then
                # reason= value - no completion
                return
            # Exclusion filters with not: prefix
            elif [[ "$cur" == not:partition=* ]] || [[ "$prev" == "=" && "${{COMP_WORDS[COMP_CWORD-2]}}" == "not:partition" ]]; then
                local val="${{cur#not:partition=}}"
                [[ "$prev" == "=" ]] && val="$cur"
                local cached_partitions="$(_slurm_cache_partitions)"
                COMPREPLY=($(compgen -W "$cached_partitions" -- "$val"))
                [[ ${{#COMPREPLY[@]}} -gt 0 ]] && COMPREPLY=("${{COMPREPLY[@]/#/not:partition=}}")
            elif [[ "$cur" == not:state=* ]] || [[ "$prev" == "=" && "${{COMP_WORDS[COMP_CWORD-2]}}" == "not:state" ]]; then
                local val="${{cur#not:state=}}"
                [[ "$prev" == "=" ]] && val="$cur"
                COMPREPLY=($(compgen -W "$node_states" -- "$val"))
                [[ ${{#COMPREPLY[@]}} -gt 0 ]] && COMPREPLY=("${{COMPREPLY[@]/#/not:state=}}")
            elif [[ "$cur" == not:user=* ]] || [[ "$prev" == "=" && "${{COMP_WORDS[COMP_CWORD-2]}}" == "not:user" ]]; then
                local val="${{cur#not:user=}}"
                [[ "$prev" == "=" ]] && val="$cur"
                local users="$(_slurm_cache_users)"
                COMPREPLY=($(compgen -W "$users" -- "$val"))
                [[ ${{#COMPREPLY[@]}} -gt 0 ]] && COMPREPLY=("${{COMPREPLY[@]/#/not:user=}}")
            elif [[ "$cur" == not:reservation=* ]] || [[ "$prev" == "=" && "${{COMP_WORDS[COMP_CWORD-2]}}" == "not:reservation" ]]; then
                local val="${{cur#not:reservation=}}"
                [[ "$prev" == "=" ]] && val="$cur"
                local reservations="$(_slurm_cache_reservations)"
                COMPREPLY=($(compgen -W "$reservations" -- "$val"))
                [[ ${{#COMPREPLY[@]}} -gt 0 ]] && COMPREPLY=("${{COMPREPLY[@]/#/not:reservation=}}")
            # Positive filters
            elif [[ "$cur" == partition=* ]] || [[ "$prev" == "=" && "${{COMP_WORDS[COMP_CWORD-2]}}" == "partition" ]]; then
                local val="${{cur#partition=}}"
                [[ "$prev" == "=" ]] && val="$cur"
                local cached_partitions="$(_slurm_cache_partitions)"
                COMPREPLY=($(compgen -W "$cached_partitions" -- "$val"))
                [[ ${{#COMPREPLY[@]}} -gt 0 && "$cur" == *=* ]] && COMPREPLY=("${{COMPREPLY[@]/#/partition=}}")
            elif [[ "$cur" == state=* ]] || [[ "$prev" == "=" && "${{COMP_WORDS[COMP_CWORD-2]}}" == "state" ]]; then
                local val="${{cur#state=}}"
                [[ "$prev" == "=" ]] && val="$cur"
                COMPREPLY=($(compgen -W "$node_states" -- "$val"))
                [[ ${{#COMPREPLY[@]}} -gt 0 && "$cur" == *=* ]] && COMPREPLY=("${{COMPREPLY[@]/#/state=}}")
            elif [[ "$cur" == user=* ]] || [[ "$prev" == "=" && "${{COMP_WORDS[COMP_CWORD-2]}}" == "user" ]]; then
                local val="${{cur#user=}}"
                [[ "$prev" == "=" ]] && val="$cur"
                local users="$(_slurm_cache_users)"
                COMPREPLY=($(compgen -W "$users" -- "$val"))
                [[ ${{#COMPREPLY[@]}} -gt 0 && "$cur" == *=* ]] && COMPREPLY=("${{COMPREPLY[@]/#/user=}}")
            elif [[ "$cur" == reservation=* ]] || [[ "$prev" == "=" && "${{COMP_WORDS[COMP_CWORD-2]}}" == "reservation" ]]; then
                local val="${{cur#reservation=}}"
                [[ "$prev" == "=" ]] && val="$cur"
                local reservations="$(_slurm_cache_reservations)"
                COMPREPLY=($(compgen -W "$reservations" -- "$val"))
                [[ ${{#COMPREPLY[@]}} -gt 0 && "$cur" == *=* ]] && COMPREPLY=("${{COMPREPLY[@]/#/reservation=}}")
            else
                local cached_nodes="$(_slurm_cache_nodes)"
                COMPREPLY=($(compgen -W "ALL asap nextstate= reason= $node_filters $neg_filters -v --verbose -h --help $cached_nodes" -- "$cur"))
            fi
            return
            ;;
        cancel-reboot)
            # Cancel reboot command takes nodes and filters
            local node_filters="partition= state= user= reservation= drainreason="
            local neg_filters="not:partition= not:state= not:user= not:reservation= not:drainreason="
            local node_states="idle alloc drain down mixed comp"
            if [[ "$cur" == --* ]]; then
                COMPREPLY=($(compgen -W "--verbose --help" -- "$cur"))
            # Exclusion filters with not: prefix
            elif [[ "$cur" == not:partition=* ]] || [[ "$prev" == "=" && "${{COMP_WORDS[COMP_CWORD-2]}}" == "not:partition" ]]; then
                local val="${{cur#not:partition=}}"
                [[ "$prev" == "=" ]] && val="$cur"
                local cached_partitions="$(_slurm_cache_partitions)"
                COMPREPLY=($(compgen -W "$cached_partitions" -- "$val"))
                [[ ${{#COMPREPLY[@]}} -gt 0 ]] && COMPREPLY=("${{COMPREPLY[@]/#/not:partition=}}")
            elif [[ "$cur" == not:state=* ]] || [[ "$prev" == "=" && "${{COMP_WORDS[COMP_CWORD-2]}}" == "not:state" ]]; then
                local val="${{cur#not:state=}}"
                [[ "$prev" == "=" ]] && val="$cur"
                COMPREPLY=($(compgen -W "$node_states" -- "$val"))
                [[ ${{#COMPREPLY[@]}} -gt 0 ]] && COMPREPLY=("${{COMPREPLY[@]/#/not:state=}}")
            elif [[ "$cur" == not:user=* ]] || [[ "$prev" == "=" && "${{COMP_WORDS[COMP_CWORD-2]}}" == "not:user" ]]; then
                local val="${{cur#not:user=}}"
                [[ "$prev" == "=" ]] && val="$cur"
                local users="$(_slurm_cache_users)"
                COMPREPLY=($(compgen -W "$users" -- "$val"))
                [[ ${{#COMPREPLY[@]}} -gt 0 ]] && COMPREPLY=("${{COMPREPLY[@]/#/not:user=}}")
            elif [[ "$cur" == not:reservation=* ]] || [[ "$prev" == "=" && "${{COMP_WORDS[COMP_CWORD-2]}}" == "not:reservation" ]]; then
                local val="${{cur#not:reservation=}}"
                [[ "$prev" == "=" ]] && val="$cur"
                local reservations="$(_slurm_cache_reservations)"
                COMPREPLY=($(compgen -W "$reservations" -- "$val"))
                [[ ${{#COMPREPLY[@]}} -gt 0 ]] && COMPREPLY=("${{COMPREPLY[@]/#/not:reservation=}}")
            # Positive filters
            elif [[ "$cur" == partition=* ]] || [[ "$prev" == "=" && "${{COMP_WORDS[COMP_CWORD-2]}}" == "partition" ]]; then
                local val="${{cur#partition=}}"
                [[ "$prev" == "=" ]] && val="$cur"
                local cached_partitions="$(_slurm_cache_partitions)"
                COMPREPLY=($(compgen -W "$cached_partitions" -- "$val"))
                [[ ${{#COMPREPLY[@]}} -gt 0 && "$cur" == *=* ]] && COMPREPLY=("${{COMPREPLY[@]/#/partition=}}")
            elif [[ "$cur" == state=* ]] || [[ "$prev" == "=" && "${{COMP_WORDS[COMP_CWORD-2]}}" == "state" ]]; then
                local val="${{cur#state=}}"
                [[ "$prev" == "=" ]] && val="$cur"
                COMPREPLY=($(compgen -W "$node_states" -- "$val"))
                [[ ${{#COMPREPLY[@]}} -gt 0 && "$cur" == *=* ]] && COMPREPLY=("${{COMPREPLY[@]/#/state=}}")
            elif [[ "$cur" == user=* ]] || [[ "$prev" == "=" && "${{COMP_WORDS[COMP_CWORD-2]}}" == "user" ]]; then
                local val="${{cur#user=}}"
                [[ "$prev" == "=" ]] && val="$cur"
                local users="$(_slurm_cache_users)"
                COMPREPLY=($(compgen -W "$users" -- "$val"))
                [[ ${{#COMPREPLY[@]}} -gt 0 && "$cur" == *=* ]] && COMPREPLY=("${{COMPREPLY[@]/#/user=}}")
            elif [[ "$cur" == reservation=* ]] || [[ "$prev" == "=" && "${{COMP_WORDS[COMP_CWORD-2]}}" == "reservation" ]]; then
                local val="${{cur#reservation=}}"
                [[ "$prev" == "=" ]] && val="$cur"
                local reservations="$(_slurm_cache_reservations)"
                COMPREPLY=($(compgen -W "$reservations" -- "$val"))
                [[ ${{#COMPREPLY[@]}} -gt 0 && "$cur" == *=* ]] && COMPREPLY=("${{COMPREPLY[@]/#/reservation=}}")
            else
                local cached_nodes="$(_slurm_cache_nodes)"
                COMPREPLY=($(compgen -W "$node_filters $neg_filters -v --verbose -h --help $cached_nodes" -- "$cur"))
            fi
            return
            ;;
        hold)
            # Hold command takes job IDs and job filters, with optional reason
            local job_filters="user= account= partition= state= name="
            local neg_job_filters="not:user= not:account= not:partition= not:state= not:name="
            local job_states="pending running suspended"
            if [[ "$cur" == --* ]]; then
                COMPREPLY=($(compgen -W "--user --reason --verbose --help" -- "$cur"))
            elif [[ "$cur" == -* && "${{#cur}}" -eq 2 ]]; then
                COMPREPLY=($(compgen -W "-u -r -v -h" -- "$cur"))
            elif [[ "$cur" == reason=* ]] || [[ "$prev" == "reason" && "${{COMP_WORDS[COMP_CWORD-1]}}" == "=" ]]; then
                # reason= value - no completion
                return
            # Exclusion filters with not: prefix
            elif [[ "$cur" == not:user=* ]] || [[ "$prev" == "=" && "${{COMP_WORDS[COMP_CWORD-2]}}" == "not:user" ]]; then
                local val="${{cur#not:user=}}"
                [[ "$prev" == "=" ]] && val="$cur"
                local cached_users="$(_slurm_cache_users)"
                COMPREPLY=($(compgen -W "$cached_users" -- "$val"))
                [[ ${{#COMPREPLY[@]}} -gt 0 ]] && COMPREPLY=("${{COMPREPLY[@]/#/not:user=}}")
            elif [[ "$cur" == not:account=* ]] || [[ "$prev" == "=" && "${{COMP_WORDS[COMP_CWORD-2]}}" == "not:account" ]]; then
                local val="${{cur#not:account=}}"
                [[ "$prev" == "=" ]] && val="$cur"
                local cached_accounts="$(_slurm_cache_accounts)"
                COMPREPLY=($(compgen -W "$cached_accounts" -- "$val"))
                [[ ${{#COMPREPLY[@]}} -gt 0 ]] && COMPREPLY=("${{COMPREPLY[@]/#/not:account=}}")
            elif [[ "$cur" == not:partition=* ]] || [[ "$prev" == "=" && "${{COMP_WORDS[COMP_CWORD-2]}}" == "not:partition" ]]; then
                local val="${{cur#not:partition=}}"
                [[ "$prev" == "=" ]] && val="$cur"
                local cached_partitions="$(_slurm_cache_partitions)"
                COMPREPLY=($(compgen -W "$cached_partitions" -- "$val"))
                [[ ${{#COMPREPLY[@]}} -gt 0 ]] && COMPREPLY=("${{COMPREPLY[@]/#/not:partition=}}")
            elif [[ "$cur" == not:state=* ]] || [[ "$prev" == "=" && "${{COMP_WORDS[COMP_CWORD-2]}}" == "not:state" ]]; then
                local val="${{cur#not:state=}}"
                [[ "$prev" == "=" ]] && val="$cur"
                COMPREPLY=($(compgen -W "$job_states" -- "$val"))
                [[ ${{#COMPREPLY[@]}} -gt 0 ]] && COMPREPLY=("${{COMPREPLY[@]/#/not:state=}}")
            # Positive filters
            elif [[ "$cur" == user=* ]] || [[ "$prev" == "=" && "${{COMP_WORDS[COMP_CWORD-2]}}" == "user" ]]; then
                local val="${{cur#user=}}"
                [[ "$prev" == "=" ]] && val="$cur"
                local cached_users="$(_slurm_cache_users)"
                COMPREPLY=($(compgen -W "$cached_users" -- "$val"))
                [[ ${{#COMPREPLY[@]}} -gt 0 && "$cur" == *=* ]] && COMPREPLY=("${{COMPREPLY[@]/#/user=}}")
            elif [[ "$cur" == account=* ]] || [[ "$prev" == "=" && "${{COMP_WORDS[COMP_CWORD-2]}}" == "account" ]]; then
                local val="${{cur#account=}}"
                [[ "$prev" == "=" ]] && val="$cur"
                local cached_accounts="$(_slurm_cache_accounts)"
                COMPREPLY=($(compgen -W "$cached_accounts" -- "$val"))
                [[ ${{#COMPREPLY[@]}} -gt 0 && "$cur" == *=* ]] && COMPREPLY=("${{COMPREPLY[@]/#/account=}}")
            elif [[ "$cur" == partition=* ]] || [[ "$prev" == "=" && "${{COMP_WORDS[COMP_CWORD-2]}}" == "partition" ]]; then
                local val="${{cur#partition=}}"
                [[ "$prev" == "=" ]] && val="$cur"
                local cached_partitions="$(_slurm_cache_partitions)"
                COMPREPLY=($(compgen -W "$cached_partitions" -- "$val"))
                [[ ${{#COMPREPLY[@]}} -gt 0 && "$cur" == *=* ]] && COMPREPLY=("${{COMPREPLY[@]/#/partition=}}")
            elif [[ "$cur" == state=* ]] || [[ "$prev" == "=" && "${{COMP_WORDS[COMP_CWORD-2]}}" == "state" ]]; then
                local val="${{cur#state=}}"
                [[ "$prev" == "=" ]] && val="$cur"
                COMPREPLY=($(compgen -W "$job_states" -- "$val"))
                [[ ${{#COMPREPLY[@]}} -gt 0 && "$cur" == *=* ]] && COMPREPLY=("${{COMPREPLY[@]/#/state=}}")
            else
                local cached_jobs="$(_slurm_cache_jobs)"
                COMPREPLY=($(compgen -W "$job_filters $neg_job_filters reason= -r --reason -v --verbose -h --help $cached_jobs" -- "$cur"))
            fi
            return
            ;;
        release|top|requeue|suspend)
            # Job control commands take job IDs and job filters
            local job_filters="user= account= partition= state= name="
            local neg_job_filters="not:user= not:account= not:partition= not:state= not:name="
            local job_states="pending running suspended"
            if [[ "$cur" == --* ]]; then
                COMPREPLY=($(compgen -W "--verbose --help" -- "$cur"))
            # Exclusion filters with not: prefix
            elif [[ "$cur" == not:user=* ]] || [[ "$prev" == "=" && "${{COMP_WORDS[COMP_CWORD-2]}}" == "not:user" ]]; then
                local val="${{cur#not:user=}}"
                [[ "$prev" == "=" ]] && val="$cur"
                local cached_users="$(_slurm_cache_users)"
                COMPREPLY=($(compgen -W "$cached_users" -- "$val"))
                [[ ${{#COMPREPLY[@]}} -gt 0 ]] && COMPREPLY=("${{COMPREPLY[@]/#/not:user=}}")
            elif [[ "$cur" == not:account=* ]] || [[ "$prev" == "=" && "${{COMP_WORDS[COMP_CWORD-2]}}" == "not:account" ]]; then
                local val="${{cur#not:account=}}"
                [[ "$prev" == "=" ]] && val="$cur"
                local cached_accounts="$(_slurm_cache_accounts)"
                COMPREPLY=($(compgen -W "$cached_accounts" -- "$val"))
                [[ ${{#COMPREPLY[@]}} -gt 0 ]] && COMPREPLY=("${{COMPREPLY[@]/#/not:account=}}")
            elif [[ "$cur" == not:partition=* ]] || [[ "$prev" == "=" && "${{COMP_WORDS[COMP_CWORD-2]}}" == "not:partition" ]]; then
                local val="${{cur#not:partition=}}"
                [[ "$prev" == "=" ]] && val="$cur"
                local cached_partitions="$(_slurm_cache_partitions)"
                COMPREPLY=($(compgen -W "$cached_partitions" -- "$val"))
                [[ ${{#COMPREPLY[@]}} -gt 0 ]] && COMPREPLY=("${{COMPREPLY[@]/#/not:partition=}}")
            elif [[ "$cur" == not:state=* ]] || [[ "$prev" == "=" && "${{COMP_WORDS[COMP_CWORD-2]}}" == "not:state" ]]; then
                local val="${{cur#not:state=}}"
                [[ "$prev" == "=" ]] && val="$cur"
                COMPREPLY=($(compgen -W "$job_states" -- "$val"))
                [[ ${{#COMPREPLY[@]}} -gt 0 ]] && COMPREPLY=("${{COMPREPLY[@]/#/not:state=}}")
            # Positive filters
            elif [[ "$cur" == user=* ]] || [[ "$prev" == "=" && "${{COMP_WORDS[COMP_CWORD-2]}}" == "user" ]]; then
                local val="${{cur#user=}}"
                [[ "$prev" == "=" ]] && val="$cur"
                local cached_users="$(_slurm_cache_users)"
                COMPREPLY=($(compgen -W "$cached_users" -- "$val"))
                [[ ${{#COMPREPLY[@]}} -gt 0 && "$cur" == *=* ]] && COMPREPLY=("${{COMPREPLY[@]/#/user=}}")
            elif [[ "$cur" == account=* ]] || [[ "$prev" == "=" && "${{COMP_WORDS[COMP_CWORD-2]}}" == "account" ]]; then
                local val="${{cur#account=}}"
                [[ "$prev" == "=" ]] && val="$cur"
                local cached_accounts="$(_slurm_cache_accounts)"
                COMPREPLY=($(compgen -W "$cached_accounts" -- "$val"))
                [[ ${{#COMPREPLY[@]}} -gt 0 && "$cur" == *=* ]] && COMPREPLY=("${{COMPREPLY[@]/#/account=}}")
            elif [[ "$cur" == partition=* ]] || [[ "$prev" == "=" && "${{COMP_WORDS[COMP_CWORD-2]}}" == "partition" ]]; then
                local val="${{cur#partition=}}"
                [[ "$prev" == "=" ]] && val="$cur"
                local cached_partitions="$(_slurm_cache_partitions)"
                COMPREPLY=($(compgen -W "$cached_partitions" -- "$val"))
                [[ ${{#COMPREPLY[@]}} -gt 0 && "$cur" == *=* ]] && COMPREPLY=("${{COMPREPLY[@]/#/partition=}}")
            elif [[ "$cur" == state=* ]] || [[ "$prev" == "=" && "${{COMP_WORDS[COMP_CWORD-2]}}" == "state" ]]; then
                local val="${{cur#state=}}"
                [[ "$prev" == "=" ]] && val="$cur"
                COMPREPLY=($(compgen -W "$job_states" -- "$val"))
                [[ ${{#COMPREPLY[@]}} -gt 0 && "$cur" == *=* ]] && COMPREPLY=("${{COMPREPLY[@]/#/state=}}")
            else
                local cached_jobs="$(_slurm_cache_jobs)"
                COMPREPLY=($(compgen -W "$job_filters $neg_job_filters -v --verbose -h --help $cached_jobs" -- "$cur"))
            fi
            return
            ;;
        schedloglevel)
            # schedloglevel takes an optional level value
            COMPREPLY=($(compgen -W "0 1 yes no y n on off --dry-run -v --verbose -h --help" -- "$cur"))
            return
            ;;
        setdebug|sd)
            local debug_levels="quiet fatal error info verbose debug debug2 debug3 debug4 debug5"
            local level_set="no"
            for ((k=2; k<COMP_CWORD; k++)); do
                local w="${{COMP_WORDS[k]}}"
                case "$w" in
                    quiet|fatal|error|info|verbose|debug|debug2|debug3|debug4|debug5)
                        level_set="yes" ;;
                esac
            done
            if [[ "$level_set" == "no" ]]; then
                COMPREPLY=($(compgen -W "$debug_levels --dry-run -v --verbose -h --help" -- "$cur"))
            elif _slurm_parse_keyval "$cur" "$prev"; then
                case "$_key" in
                    nodes)
                        _slurm_complete_nodes_value "$_val" "$cur" "$_key" ;;
                    state|partition|user|reservation)
                        if [[ "${{COMP_WORDS[COMP_CWORD-4]}}" == "nodes" ]] || \\
                           [[ "$cur" == "=" && "${{COMP_WORDS[COMP_CWORD-3]}}" == "nodes" ]]; then
                            _slurm_complete_nodes_value "$_key=$_val" "" "nodes"
                        fi ;;
                esac
            else
                COMPREPLY=($(compgen -W "nodes= --dry-run -v --verbose -h --help" -- "$cur"))
                compopt -o nospace 2>/dev/null
            fi
            return
            ;;
        bbstat)
            COMPREPLY=($(compgen -W "--dry-run -v --verbose -h --help" -- "$cur"))
            return
            ;;
        autocomplete|help|list-resources)
            # These commands take -h/--help option
            COMPREPLY=($(compgen -W "-h --help" -- "$cur"))
            return
            ;;
    esac

    i=$((i+1))
    guessed="no"
    # Resource matching - generated from RESOURCES config
    case "$resource" in
{resource_case_patterns}
    esac

    # echo "i=$i j=$j COMP_CWORD=$COMP_CWORD \\
    # guessed=$guessed resource=$resource"

    # If resource is empty or we're completing the resource position,
    # show resource list
    if [[ -z "$resource" ]] || [[ $j -ge $COMP_CWORD ]]; then
        if [[ $guessed != "no" ]]; then
            # Events are read-only, don't suggest for update/delete
            if [[ "$guessed" == "events" ]] && [[ "$cmd" == "update" || "$cmd" == "delete" ]]; then
                return
            fi
            COMPREPLY=($(compgen -W "$guessed" -- "$cur"))
            return
        else
            # Base resources for all commands
            local all_resources="reservations nodes partitions accounts \\
                qos users coordinators problems stats associations dumps \\
                licenses bad runawayjobs tres archives transactions jobs"
            # Events are read-only, only available for show command
            if [[ "$cmd" == "show" ]]; then
                all_resources="$all_resources events"
            fi
            COMPREPLY=($(compgen -W "$all_resources" -- "$cur"))
            return
        fi
    fi

    # Handle options that come after the resource
    # Check if previous word needs a value
    case "$prev" in
        --style)
            COMPREPLY=($(compgen -W "{' '.join(STYLE_OPTIONS)}" -- "$cur"))
            return
            ;;
        --profile|-P)
            # Profile names - built-in plus any from config files
            local profiles="default compact minimal oneline detailed"
            if [ -f "$HOME/.config/slurm-cli.profiles" ]; then
                local user_profiles=$(grep -oE '^[a-z_]+:' "$HOME/.config/slurm-cli.profiles" 2>/dev/null | tr -d ':' | tr '\\n' ' ')
                profiles="$profiles $user_profiles"
            fi
            if [ -f "/etc/slurm/cli.profiles" ]; then
                local sys_profiles=$(grep -oE '^[a-z_]+:' "/etc/slurm/cli.profiles" 2>/dev/null | tr -d ':' | tr '\\n' ' ')
                profiles="$profiles $sys_profiles"
            fi
            COMPREPLY=($(compgen -W "$profiles" -- "$cur"))
            return
            ;;
        =)
            # Handle --profile=value format (when = is a separate word)
            if [[ ${{COMP_CWORD}} -ge 2 ]]; then
                local opt="${{COMP_WORDS[COMP_CWORD-2]}}"
                if [[ "$opt" == "--profile" || "$opt" == "-P" ]]; then
                    local profiles="default compact minimal oneline detailed"
                    if [ -f "$HOME/.config/slurm-cli.profiles" ]; then
                        local user_profiles=$(grep -oE '^[a-z_]+:' "$HOME/.config/slurm-cli.profiles" 2>/dev/null | tr -d ':' | tr '\\n' ' ')
                        profiles="$profiles $user_profiles"
                    fi
                    if [ -f "/etc/slurm/cli.profiles" ]; then
                        local sys_profiles=$(grep -oE '^[a-z_]+:' "/etc/slurm/cli.profiles" 2>/dev/null | tr -d ':' | tr '\\n' ' ')
                        profiles="$profiles $sys_profiles"
                    fi
                    COMPREPLY=($(compgen -W "$profiles" -- "$cur"))
                    return
                fi
            fi
            ;;
        --delimiter|-d|--cache-timeout|-t)
            # These options need a value, no completion
            return
            ;;
        --profile-str|--format|-o)
            # Complete with available fields for the resource
            local fields=""
            case "$guessed" in
                jobs) fields="job_id name user_name account partition job_state time_limit endlimit node_count nodes cpus gres submit_time start_time end_time priority reason command working_directory" ;;
                nodes) fields="name state cpus real_memory gres partitions features reason alloc_cpus alloc_memory" ;;
                partitions) fields="partitionname state nodes totalnodes totalcpus maxtime default defaulttime defmempercpu defmempernode allowgroups allowaccounts allowqos denyaccounts denyqos maxnodes minnodes maxcpuspernode maxcpuspersocket maxmempercpu maxmempernode prioritytier priorityjobfactor preemptmode gracetime oversubscribe overtimelimit qos alternate allocnodes cpubind disablerootjobs exclusiveuser hidden jobdefaults lln powerdownonidle reqresv rootonly shared tresbillingweights" ;;
                accounts) fields="name description organization coordinators flags" ;;
                users) fields="name default_account admin_level coordinators" ;;
                qos) fields="name id priority max_wall max_jobs max_submit flags preempt preempt_mode grace_time" ;;
                reservations) fields="name start_time end_time nodes users accounts partition state flags" ;;
                associations) fields="account user cluster partition parent_account qos default_qos shares grp_jobs grp_submit" ;;
                coordinators) fields="account name" ;;
                events) fields="time cluster node state reason user" ;;
            esac
            if [[ -n "$fields" ]]; then
                # Handle comma-separated fields: filter out already selected ones
                local prefix="" partial=""
                if [[ "$cur" == *,* ]]; then
                    prefix="${{cur%,*}},"
                    partial="${{cur##*,}}"
                    # Filter out already selected fields
                    local selected="${{cur%,*}}"
                    local remaining=""
                    for f in $fields; do
                        if [[ ",$selected," != *",$f,"* ]]; then
                            remaining="$remaining $f"
                        fi
                    done
                    fields="$remaining"
                else
                    partial="$cur"
                fi
                COMPREPLY=($(compgen -W "$fields" -- "$partial"))
                # Add prefix to each completion
                if [[ -n "$prefix" ]]; then
                    COMPREPLY=("${{COMPREPLY[@]/#/$prefix}}")
                fi
            fi
            return
            ;;
    esac

    # If current word starts with -, show options
    if [[ "$cur" == -* ]]; then
        COMPREPLY=($(compgen -W "{all_opts_str}" -- "$cur"))
        return
    fi

    # command current_autocomplete_word_index
    # Use guessed (full name) instead of resource (partial name)
    # Check if the autocomplete function exists before calling it
    if type "_slurm_cli_${{guessed}}_autocomplete" &>/dev/null; then
        _slurm_cli_${{guessed}}_autocomplete "$cmd" "$j"
    fi

    # echo "${{COMP_REPLY[@]}}"
}}
"""  # noqa: E501
    )  # noqa: E501
    # Print common helper functions first
    print(get_common_autocomplete_functions())
    # Print resource-specific autocomplete functions
    print(Reservation.generate_autocomplete_options())
    print(Qos.generate_autocomplete_options())
    print(Account.generate_autocomplete_options())
    print(Association.generate_autocomplete_options())
    print(Coordinator.generate_autocomplete_options())
    print(Event.generate_autocomplete_options())
    print(Job.generate_autocomplete_options())
    print(User.generate_autocomplete_options())
    print(Partition.generate_autocomplete_options())
    print(Node.generate_autocomplete_options())
    print(
        """
# Register the completion function for various invocation methods
complete -o default -o bashdefault -o nosort -F _slurm_cli_initialize_autocomplete slurm-cli
complete -o default -o bashdefault -o nosort -F _slurm_cli_initialize_autocomplete ./slurm-cli
    """  # noqa: E501
    )
    return


# list-resources command
@click.command(context_settings=CONTEXT_SETTINGS)
@common_options
@click.pass_context
def list_resources(
    ctx: click.Context,
    style: Optional[str] = None,
    pretty: bool = False,
    json: bool = False,
    csv: bool = False,
    zebra: Optional[bool] = None,
    delimiter: Optional[str] = None,
    **kwargs,
) -> None:
    """List all available resource types and their fields
    (aliases: list, ls, l)."""
    zebra = get_zebra(ctx, zebra)
    table = Table(
        title="Available Slurm Resources",
        box=SIMPLE_HEAVY,
        pad_edge=False,
        padding=(0, 0),
        row_styles=get_row_styles(zebra),
    )
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
@click.option(
    "--verbose", "-v", is_flag=True, help="Enable verbose output"
)
def version(verbose: bool = False) -> None:
    """Show version information."""
    console.print("[bold blue]slurm-cli:[/] Slurm Swiss Knife v0.1.0")
    console.print("A CLI tool for Slurm cluster management")

    # Get slurmctld version
    try:
        result = subprocess.run(
            ["scontrol", "version"],
            capture_output=True,
            text=True,
            check=True,
        )
        console.print(f"\n[dim]{result.stdout.strip()}[/dim]")
    except subprocess.CalledProcessError as e:
        if verbose:
            console.print(
                f"[red]Error getting Slurm version: {e}[/red]"
            )
    except FileNotFoundError:
        if verbose:
            console.print("[yellow]scontrol not found[/yellow]")


@click.command(context_settings=CONTEXT_SETTINGS)
@click.option(
    "--verbose", "-v", is_flag=True, help="Enable verbose output"
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show command without executing",
)
@click.pass_context
def reconfigure(
    ctx: click.Context, verbose: bool = False, dry_run: bool = False
) -> None:
    """Reconfigure slurmctld (aliases: reconf, confreload).

    Forces slurmctld to re-read its configuration file.
    """
    dry_run = get_dry_run(ctx) or dry_run
    args = ["scontrol", "reconfigure"]

    if dry_run:
        console.print(f"[yellow]DRY RUN:[/yellow] {' '.join(args)}")
        return

    if verbose:
        console.print(f"[dim]Running: {' '.join(args)}[/dim]")

    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            check=True,
        )
        if result.stdout:
            console.print(result.stdout.strip())
        console.print(
            "[green]Reconfigure command sent successfully[/green]"
        )
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error: {e.stderr.strip() or e}[/red]")
    except FileNotFoundError:
        console.print("[red]Error: scontrol not found[/red]")


@click.command(context_settings=CONTEXT_SETTINGS)
@click.option(
    "--verbose", "-v", is_flag=True, help="Enable verbose output"
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show command without executing",
)
@click.pass_context
def ping(
    ctx: click.Context, verbose: bool = False, dry_run: bool = False
) -> None:
    """Ping slurmctld.

    Checks if the Slurm controller is responding.
    """
    dry_run = get_dry_run(ctx) or dry_run
    args = ["scontrol", "ping"]

    if dry_run:
        console.print(f"[yellow]DRY RUN:[/yellow] {' '.join(args)}")
        return

    if verbose:
        console.print(f"[dim]Running: {' '.join(args)}[/dim]")

    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            check=True,
        )
        if result.stdout:
            console.print(result.stdout.strip())
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error: {e.stderr.strip() or e}[/red]")
    except FileNotFoundError:
        console.print("[red]Error: scontrol not found[/red]")


@click.command(context_settings=CONTEXT_SETTINGS)
@click.option(
    "--verbose", "-v", is_flag=True, help="Enable verbose output"
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show command without executing",
)
@click.pass_context
def takeover(
    ctx: click.Context, verbose: bool = False, dry_run: bool = False
) -> None:
    """Take over as primary slurmctld.

    Causes the backup slurmctld to take over as the primary controller.
    This command should only be run on a backup controller.
    """
    dry_run = get_dry_run(ctx) or dry_run
    args = ["scontrol", "takeover"]

    if dry_run:
        console.print(f"[yellow]DRY RUN:[/yellow] {' '.join(args)}")
        return

    if verbose:
        console.print(f"[dim]Running: {' '.join(args)}[/dim]")

    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            check=True,
        )
        if result.stdout:
            console.print(result.stdout.strip())
        console.print(
            "[green]Takeover command sent successfully[/green]"
        )
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error: {e.stderr.strip() or e}[/red]")
    except FileNotFoundError:
        console.print("[red]Error: scontrol not found[/red]")


@click.command(context_settings=CONTEXT_SETTINGS)
@click.option(
    "--verbose", "-v", is_flag=True, help="Enable verbose output"
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show command without executing",
)
@click.argument("filename", required=False, default=None)
@click.pass_context
def write_config(
    ctx: click.Context,
    verbose: bool = False,
    dry_run: bool = False,
    filename: Optional[str] = None,
) -> None:
    """Write Slurm configuration file.

    Generates a new configuration file from the current cluster state.
    The generated file can be reviewed before applying it with scontrol update_config.

    Args:
        filename: Output file path (default: /var/lib/slurmd/cluster.conf)
    """
    dry_run = get_dry_run(ctx) or dry_run
    args = ["scontrol", "write", "config"]

    if filename:
        args.append(filename)

    if verbose:
        console.print(f"[dim]Running: {' '.join(args)}[/dim]")

    if dry_run:
        console.print(f"[yellow]DRY RUN:[/yellow] {' '.join(args)}")
        return

    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            check=True,
        )
        if result.stdout:
            console.print(result.stdout.strip())
        console.print(
            "[green]Write config command sent successfully[/green]"
        )
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error: {e.stderr.strip() or e}[/red]")
    except FileNotFoundError:
        console.print("[red]Error: scontrol not found[/red]")


@click.command(context_settings=CONTEXT_SETTINGS)
@click.option(
    "--verbose", "-v", is_flag=True, help="Enable verbose output"
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show command without executing",
)
@click.argument(
    "level",
    required=False,
    default=None,
    shell_complete=lambda ctx, param, incomplete: [
        click.shell_completion.CompletionItem(v)
        for v in ["0", "1", "yes", "no", "y", "n", "on", "off"]
        if v.startswith(incomplete)
    ],
)
@click.pass_context
def schedloglevel(
    ctx: click.Context,
    verbose: bool = False,
    dry_run: bool = False,
    level: Optional[str] = None,
) -> None:
    """Set scheduler log level.

    Sets the scheduler log level for the cluster.

    \b
    Allowed values: 1, 0, yes, no, y, n, on, off

    Args:
        level: Log level value (default: uses current setting)

    Examples:
      slurm-cli schedloglevel 1
      slurm-cli schedloglevel yes
      slurm-cli schedloglevel --dry-run 0
    """
    dry_run = get_dry_run(ctx, dry_run)

    # Build command arguments
    args = ["scontrol", "schedloglevel"]

    if level is not None:
        args.append(level)

    if dry_run:
        console.print(f"[yellow]DRY RUN:[/yellow] {' '.join(args)}")
        return

    if verbose:
        console.print(f"[dim]Running: {' '.join(args)}[/dim]")

    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            check=True,
        )
        if result.stdout:
            console.print(result.stdout.strip())
        console.print(
            "[green]Scheduler log level command sent successfully[/green]"
        )
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error: {e.stderr.strip() or e}[/red]")
    except FileNotFoundError:
        console.print("[red]Error: scontrol not found[/red]")


@click.command(context_settings=CONTEXT_SETTINGS)
@click.option(
    "--verbose", "-v", is_flag=True, help="Enable verbose output"
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be done without making changes",
)
@click.argument(
    "level",
    required=True,
    shell_complete=lambda ctx, param, incomplete: [
        click.shell_completion.CompletionItem(v)
        for v in [
            "quiet",
            "fatal",
            "error",
            "info",
            "verbose",
            "debug",
            "debug2",
            "debug3",
            "debug4",
            "debug5",
        ]
        if v.startswith(incomplete)
    ],
)
@click.argument("nodes", nargs=-1, required=False)
@click.pass_context
def setdebug(
    ctx: click.Context,
    level: str,
    nodes: Tuple[str, ...] = (),
    verbose: bool = False,
    dry_run: bool = False,
) -> None:
    """Set slurmctld/slurmd debug level (aliases: sd).

    Sets the debug log level for slurmctld or individual slurmd daemons.

    \b
    Allowed levels: quiet fatal error info verbose debug debug2 debug3 debug4 debug5

    \b
    The optional nodes argument accepts a nodelist or node filters:
      nodes=node001          - specific node(s)
      nodes=partition=gpu    - all nodes in partition gpu
      nodes=state=idle       - all idle nodes

    \b
    Examples:
      slurm-cli setdebug debug
      slurm-cli setdebug info nodes=node001
      slurm-cli setdebug verbose nodes=partition=gpu
      slurm-cli setdebug debug --dry-run
    """
    dry_run = get_dry_run(ctx, dry_run)

    valid_levels = {
        "quiet",
        "fatal",
        "error",
        "info",
        "verbose",
        "debug",
        "debug2",
        "debug3",
        "debug4",
        "debug5",
    }
    if level.lower() not in valid_levels:
        console.print(
            f"[red]Error: Invalid level '{level}'. "
            f"Allowed: {', '.join(sorted(valid_levels))}[/red]"
        )
        return

    # Build base command
    args = ["scontrol", "setdebug", level.lower()]

    # Parse optional nodes= argument
    nodes_list = list(nodes)
    nodes_value = None
    for arg in nodes_list:
        if arg.lower().startswith("nodes="):
            nodes_value = arg.split("=", 1)[1]
            break

    if nodes_value:
        # Resolve filter expressions to actual nodelist if needed
        if is_node_filter(nodes_value):
            resolved_nodes, _ = resolve_node_filters(
                [nodes_value], verbose
            )
            if not resolved_nodes:
                console.print(
                    f"[red]Error: Node filter '{nodes_value}' "
                    f"matched no nodes[/red]"
                )
                return
            nodelist = ",".join(sorted(resolved_nodes))
        else:
            nodelist = nodes_value
        args.append(f"nodes={nodelist}")

    if dry_run:
        console.print(f"[yellow]DRY RUN:[/yellow] {' '.join(args)}")
        return

    if verbose:
        console.print(f"[dim]Running: {' '.join(args)}[/dim]")

    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            check=True,
        )
        if result.stdout:
            console.print(result.stdout.strip())
        console.print("[green]Debug level set successfully[/green]")
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error: {e.stderr.strip() or e}[/red]")
    except FileNotFoundError:
        console.print("[red]Error: scontrol not found[/red]")


@click.command(context_settings=CONTEXT_SETTINGS)
@click.option(
    "--verbose", "-v", is_flag=True, help="Enable verbose output"
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show command without executing",
)
@click.pass_context
def bbstat(
    ctx: click.Context, verbose: bool = False, dry_run: bool = False
) -> None:
    """Show burst buffer status (aliases: bbs).

    Displays current burst buffer status from slurmctld.

    Examples:
      slurm-cli bbstat
    """
    dry_run = get_dry_run(ctx) or dry_run
    args = ["scontrol", "show", "bbstat"]

    if dry_run:
        console.print(f"[yellow]DRY RUN:[/yellow] {' '.join(args)}")
        return

    if verbose:
        console.print(f"[dim]Running: {' '.join(args)}[/dim]")

    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            check=True,
        )
        if result.stdout:
            console.print(result.stdout.strip())
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error: {e.stderr.strip() or e}[/red]")
    except FileNotFoundError:
        console.print("[red]Error: scontrol not found[/red]")


@click.command(context_settings=CONTEXT_SETTINGS)
@click.option(
    "--verbose", "-v", is_flag=True, help="Enable verbose output"
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show command without executing",
)
@click.argument("job_id", required=True, default=None)
@click.argument("filename", required=False, default=None)
@click.pass_context
def batch_script(
    ctx: click.Context,
    verbose: bool = False,
    dry_run: bool = False,
    job_id: Optional[str] = None,
    filename: Optional[str] = None,
) -> None:
    """Run scontrol write batch_script for a job.

    Submits the contents of a file as a batch script to the specified job.

    Args:
        job_id: Job ID (required - must be provided)
        filename: Script file path (optional - if not provided, reads from stdin)
    """
    dry_run = get_dry_run(ctx) or dry_run

    ## Check that job_id is required
    # if job_id is None:
    #    console.print("[red]Error: Job ID is required.[/red]")
    #    console.print(
    #        "[yellow]Usage: slurm-cli batch_script JOB_ID [FILENAME][/yellow]"
    #    )
    #    return

    # Build command arguments
    args = ["scontrol", "write", "batch_script"]

    if job_id is not None:
        args.append(str(job_id))

    if filename:
        args.append(filename)

    if dry_run:
        console.print(f"[yellow]DRY RUN:[/yellow] {' '.join(args)}")
        return

    if verbose:
        console.print(f"[dim]Running: {' '.join(args)}[/dim]")

    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            check=True,
        )
        if result.stdout:
            console.print(result.stdout.strip())
        console.print(
            "[green]Batch script command sent successfully[/green]"
        )
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error: {e.stderr.strip() or e}[/red]")
    except FileNotFoundError:
        console.print("[red]Error: scontrol not found[/red]")


def parse_time_to_seconds(time_str: str) -> Optional[int]:
    """Parse time string to seconds.

    Accepts formats:
    - integer (already seconds)
    - HH:MM:SS
    - MM:SS
    - D-HH:MM:SS (days-hours:minutes:seconds)
    - Nh, Nm, Ns (e.g., 1h, 30m, 45s)
    - infinite (returns None)
    """
    import re

    time_str = time_str.strip().lower()

    # Handle infinite
    if time_str in ("infinite", "inf", "unlimited"):
        return None

    # Try integer seconds
    try:
        return int(time_str)
    except ValueError:
        pass

    # Try D-HH:MM:SS or HH:MM:SS
    m = re.match(
        r"^(?:(?P<days>\d+)-)?(?P<h>\d+):(?P<m>\d+):(?P<s>\d+)$",
        time_str,
    )
    if m:
        days = int(m.group("days") or 0)
        hours = int(m.group("h"))
        minutes = int(m.group("m"))
        seconds = int(m.group("s"))
        return days * 86400 + hours * 3600 + minutes * 60 + seconds

    # Try MM:SS (two numbers = minutes:seconds)
    m = re.match(r"^(?P<m>\d+):(?P<s>\d+)$", time_str)
    if m:
        minutes = int(m.group("m"))
        seconds = int(m.group("s"))
        return minutes * 60 + seconds

    # Try Nh, Nm, Ns format
    m = re.match(r"^(\d+)([dhms])$", time_str)
    if m:
        value = int(m.group(1))
        unit = m.group(2)
        if unit == "d":
            return value * 86400
        elif unit == "h":
            return value * 3600
        elif unit == "m":
            return value * 60
        else:  # s
            return value

    raise ValueError(f"Invalid time format: {time_str}")


@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument("options", nargs=-1)
@click.option(
    "--verbose", "-v", is_flag=True, help="Enable verbose output"
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show command without executing",
)
@click.pass_context
def token(
    ctx: click.Context,
    options: Tuple[str, ...],
    verbose: bool = False,
    dry_run: bool = False,
) -> None:
    """Generate JWT authentication token.

    Options can be specified as key=value pairs:
      lifespan=<time>   Token lifespan (e.g., 1h, 30m, 1:00:00, infinite)
      username=<user>   Generate token for specified user (requires admin)

    Examples:
      slurm-cli token
      slurm-cli token lifespan=1h
      slurm-cli token lifespan=30m username=john
      slurm-cli token lifespan=infinite
    """
    dry_run = get_dry_run(ctx) or dry_run
    args = ["scontrol", "token"]

    # Parse options
    for opt in options:
        if "=" not in opt:
            console.print(
                f"[red]Error: Invalid option format: {opt}[/red]"
            )
            console.print("Options must be in key=value format")
            return

        key, value = opt.split("=", 1)
        key = key.lower()

        if key == "lifespan":
            try:
                seconds = parse_time_to_seconds(value)
                if seconds is not None:
                    args.append(f"lifespan={seconds}")
                # If infinite, don't add lifespan (use default/max)
            except ValueError as e:
                console.print(f"[red]Error: {e}[/red]")
                return
        elif key == "username":
            args.append(f"username={value}")
        else:
            console.print(
                f"[yellow]Warning: Unknown option: {key}[/yellow]"
            )
            args.append(f"{key}={value}")

    if dry_run:
        console.print(f"[yellow]DRY RUN:[/yellow] {' '.join(args)}")
        return

    if verbose:
        console.print(f"[dim]Running: {' '.join(args)}[/dim]")

    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            check=True,
        )
        if result.stdout:
            console.print(result.stdout.strip())
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error: {e.stderr.strip() or e}[/red]")
    except FileNotFoundError:
        console.print("[red]Error: scontrol not found[/red]")


def _resolve_user_filter(
    value: str, verbose: bool = False
) -> Optional[str]:
    """Resolve a user filter expression to a comma-separated list of users.

    Supports:
    - Direct user list: "john,jane" -> "john,jane"
    - Account filter: "account=research" -> resolve to users in account

    Args:
        value: User value or filter expression
        verbose: Enable verbose output

    Returns:
        Comma-separated list of users, or None if resolution failed
    """
    if not value:
        return None

    # Check if it's a filter expression
    if "=" in value:
        key, filter_value = value.split("=", 1)
        key = key.lower()

        if key == "account":
            # Get users in the account
            try:
                result = subprocess.run(
                    [
                        "sacctmgr",
                        "show",
                        "users",
                        f"account={filter_value}",
                        "--json",
                    ],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                if result.stdout:
                    data = json.loads(result.stdout)
                    users = data.get("users", [])
                    user_names = [
                        u.get("name") for u in users if u.get("name")
                    ]
                    if user_names:
                        if verbose:
                            console.print(
                                f"[dim]Resolved account={filter_value} to "
                                f"{len(user_names)} users: "
                                f"{', '.join(user_names[:5])}"
                                f"{'...' if len(user_names) > 5 else ''}[/dim]"
                            )
                        return ",".join(user_names)
                    else:
                        console.print(
                            f"[yellow]No users found in account "
                            f"'{filter_value}'[/yellow]"
                        )
                        return None
            except subprocess.CalledProcessError as e:
                console.print(
                    f"[red]Error resolving user filter: "
                    f"{e.stderr.strip() or e}[/red]"
                )
                return None
            except json.JSONDecodeError:
                console.print("[red]Error parsing user data[/red]")
                return None
        else:
            # Unknown filter, return as-is (scontrol might handle it)
            if verbose:
                console.print(
                    f"[dim]Unknown user filter '{key}', "
                    f"passing as-is[/dim]"
                )
            return value

    # Direct user list
    return value


# Valid flags for assoc_mgr command
ASSOC_MGR_FLAGS = ["users", "assoc", "qos"]


@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument("options", nargs=-1)
@click.option(
    "--verbose", "-v", is_flag=True, help="Enable verbose output"
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show command without executing",
)
@click.pass_context
def assoc_mgr(
    ctx: click.Context,
    options: Tuple[str, ...],
    verbose: bool = False,
    dry_run: bool = False,
) -> None:
    """Display slurmctld's internal cache (associations, users, QOS).

    Options can be specified as key=value pairs:

    \b
      users=<list>      Limit to specific users (supports filters)
      accounts=<list>   Limit to specific accounts
      qos=<list>        Limit to specific QOS names
      flags=<type>      Show only: users, assoc, or qos

    User filters:
      users=john,jane          Direct user list
      users=account=research   Users in the 'research' account

    \b
    Examples:
      slurm-cli assoc_mgr
      slurm-cli assoc_mgr flags=users
      slurm-cli assoc_mgr users=john,jane
      slurm-cli assoc_mgr users=account=research
      slurm-cli assoc_mgr accounts=physics,chemistry
      slurm-cli assoc_mgr qos=normal,high flags=qos
    """
    dry_run = get_dry_run(ctx) or dry_run
    args = ["scontrol", "assoc_mgr"]

    # Parse options
    for opt in options:
        if "=" not in opt:
            console.print(
                f"[red]Error: Invalid option format: {opt}[/red]"
            )
            console.print("Options must be in key=value format")
            return

        key, value = opt.split("=", 1)
        key = key.lower()

        if key == "users":
            # Resolve user filter
            resolved = _resolve_user_filter(value, verbose)
            if resolved is None:
                return
            args.append(f"users={resolved}")
        elif key == "accounts":
            args.append(f"accounts={value}")
        elif key == "qos":
            args.append(f"qos={value}")
        elif key == "flags":
            if value.lower() not in ASSOC_MGR_FLAGS:
                console.print(
                    f"[red]Error: Invalid flags value '{value}'. "
                    f"Must be one of: {', '.join(ASSOC_MGR_FLAGS)}[/red]"
                )
                return
            args.append(f"flags={value}")
        else:
            console.print(
                f"[yellow]Warning: Unknown option: {key}[/yellow]"
            )
            args.append(f"{key}={value}")

    if dry_run:
        console.print(f"[yellow]DRY RUN:[/yellow] {' '.join(args)}")
        return

    if verbose:
        console.print(f"[dim]Running: {' '.join(args)}[/dim]")

    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            check=True,
        )
        if result.stdout:
            console.print(result.stdout.strip())
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error: {e.stderr.strip() or e}[/red]")
    except FileNotFoundError:
        console.print("[red]Error: scontrol not found[/red]")


@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument("nodes", nargs=-1, required=True)
@click.option(
    "--reason", "-r", default=None, help="Reason for draining nodes"
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be done without making changes",
)
@click.option(
    "--verbose", "-v", is_flag=True, help="Enable verbose output"
)
@click.pass_context
def drain(
    ctx: click.Context,
    nodes: Tuple[str, ...],
    reason: Optional[str] = None,
    dry_run: bool = False,
    verbose: bool = False,
) -> None:
    """Drain nodes (set state to drain). Reason: --reason, -r, or reason=VALUE.

    Supports node filters with optional exclusion (prefix with not:):
    - partition=NAME, not:partition=NAME
    - state=STATE, not:state=STATE
    - user=USER, not:user=USER
    - reservation=NAME, not:reservation=NAME

    \b
    Examples:
      slurm-cli drain node001
      slurm-cli drain node[001-010]
      slurm-cli drain node001 --reason="Maintenance"
      slurm-cli drain node001 -r "Hardware issue"
      slurm-cli drain node001 reason="Scheduled maintenance"
      slurm-cli drain partition=gpu reason="GPU maintenance"
      slurm-cli drain partition=gpu not:reservation=maint \
          reason="Drain except reserved"
      slurm-cli drain state=idle not:user=admin \
          reason="Idle nodes except admin's"
    """
    dry_run = get_dry_run(ctx, dry_run)
    # Parse reason= from positional arguments
    args_list = list(nodes)
    inline_reason = None
    node_args = []
    for arg in args_list:
        if arg.lower().startswith("reason="):
            inline_reason = arg.split("=", 1)[1]
        else:
            node_args.append(arg)

    # Resolve node filters with exclusions
    resolved_nodes, other_args = resolve_node_filters(
        node_args, verbose
    )

    if not resolved_nodes:
        console.print(
            "[red]Error: No nodes specified or all excluded[/red]"
        )
        return

    # Convert set to sorted list for consistent output
    actual_nodes = sorted(resolved_nodes)

    # Use --reason option if provided, otherwise use inline reason=
    final_reason = reason if reason is not None else inline_reason

    # Join nodes with comma for scontrol
    nodelist = ",".join(actual_nodes)
    args = ["scontrol", "update", f"nodename={nodelist}", "state=drain"]

    if final_reason:
        args.append(f"reason={final_reason}")

    if dry_run:
        console.print(f"[yellow]DRY RUN:[/yellow] {' '.join(args)}")
        return

    if verbose:
        console.print(f"[dim]Running: {' '.join(args)}[/dim]")

    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            check=True,
        )
        if result.stdout:
            console.print(result.stdout.strip())
        console.print(f"[green]Drained node(s): {nodelist}[/green]")
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error: {e.stderr.strip() or e}[/red]")
    except FileNotFoundError:
        console.print("[red]Error: scontrol not found[/red]")


@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument("nodes", nargs=-1, required=True)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be done without making changes",
)
@click.option(
    "--verbose", "-v", is_flag=True, help="Enable verbose output"
)
@click.pass_context
def undrain(
    ctx: click.Context,
    nodes: Tuple[str, ...],
    dry_run: bool = False,
    verbose: bool = False,
) -> None:
    """Undrain nodes (set state to resume).

    Supports node filters with optional exclusion (prefix with not:):
    - partition=NAME, not:partition=NAME
    - state=STATE, not:state=STATE
    - user=USER, not:user=USER
    - reservation=NAME, not:reservation=NAME

    \b
    Examples:
      slurm-cli undrain node001
      slurm-cli undrain node001 node002 node003
      slurm-cli undrain node[001-010]
      slurm-cli undrain partition=gpu
      slurm-cli undrain state=drain
      slurm-cli undrain state=drain not:reservation=maint
    """
    dry_run = get_dry_run(ctx, dry_run)
    # Resolve node filters with exclusions
    resolved_nodes, other_args = resolve_node_filters(
        list(nodes), verbose
    )

    if not resolved_nodes:
        console.print(
            "[red]Error: No nodes specified or all excluded[/red]"
        )
        return

    # Convert set to sorted list for consistent output
    actual_nodes = sorted(resolved_nodes)

    # Join nodes with comma for scontrol
    nodelist = ",".join(actual_nodes)
    args = [
        "scontrol",
        "update",
        f"nodename={nodelist}",
        "state=resume",
    ]

    if dry_run:
        console.print(f"[yellow]DRY RUN:[/yellow] {' '.join(args)}")
        return

    if verbose:
        console.print(f"[dim]Running: {' '.join(args)}[/dim]")

    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            check=True,
        )
        if result.stdout:
            console.print(result.stdout.strip())
        console.print(f"[green]Undrained node(s): {nodelist}[/green]")
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error: {e.stderr.strip() or e}[/red]")
    except FileNotFoundError:
        console.print("[red]Error: scontrol not found[/red]")


@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument("nodes", nargs=-1, required=True)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be done without making changes",
)
@click.option(
    "--verbose", "-v", is_flag=True, help="Enable verbose output"
)
@click.pass_context
def reboot(
    ctx: click.Context,
    nodes: Tuple[str, ...],
    dry_run: bool = False,
    verbose: bool = False,
) -> None:
    """Reboot nodes.

    Supports optional flags and node filters with exclusions:
    - asap - Reboot as soon as possible
    - nextstate=RESUME|DOWN - State after reboot
    - reason=<reason> - Reason for reboot
    - ALL - Reboot all nodes
    - Node filters: partition=, state=, user=, reservation=
    - Exclusions: not:partition=, not:state=, not:user=, not:reservation=

    \b
    Examples:
      slurm-cli reboot node001
      slurm-cli reboot node[001-010]
      slurm-cli reboot asap node001
      slurm-cli reboot nextstate=DOWN reason="Kernel update" node001
      slurm-cli reboot partition=gpu reason="GPU firmware update"
      slurm-cli reboot ALL
      slurm-cli reboot partition=gpu not:reservation=maint
    """
    dry_run = get_dry_run(ctx, dry_run)
    args_list = list(nodes)
    asap_flag = False
    nextstate = None
    inline_reason = None
    node_args = []

    for arg in args_list:
        arg_lower = arg.lower()
        if arg_lower == "asap":
            asap_flag = True
        elif arg_lower.startswith("nextstate="):
            nextstate = arg.split("=", 1)[1].upper()
            if nextstate not in ("RESUME", "DOWN"):
                console.print(
                    f"[red]Error: nextstate must be RESUME or DOWN, "
                    f"got: {nextstate}[/red]"
                )
                return
        elif arg_lower.startswith("reason="):
            inline_reason = arg.split("=", 1)[1]
        else:
            node_args.append(arg)

    # Check for ALL keyword
    is_all = any(arg.upper() == "ALL" for arg in node_args)
    if is_all:
        nodelist = "ALL"
    else:
        # Resolve node filters with exclusions
        resolved_nodes, other_args = resolve_node_filters(
            node_args, verbose
        )

        if not resolved_nodes:
            console.print(
                "[red]Error: No nodes specified or all excluded[/red]"
            )
            return

        # Convert set to sorted list for consistent output
        actual_nodes = sorted(resolved_nodes)
        nodelist = ",".join(actual_nodes)

    # Build scontrol reboot command
    args = ["scontrol", "reboot"]

    if asap_flag:
        args.append("asap")

    if nextstate:
        args.append(f"nextstate={nextstate}")

    if inline_reason:
        args.append(f"reason={inline_reason}")

    args.append(nodelist)

    if dry_run:
        console.print(f"[yellow]DRY RUN:[/yellow] {' '.join(args)}")
        return

    if verbose:
        console.print(f"[dim]Running: {' '.join(args)}[/dim]")

    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            check=True,
        )
        if result.stdout:
            console.print(result.stdout.strip())
        console.print(f"[green]Rebooting node(s): {nodelist}[/green]")
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error: {e.stderr.strip() or e}[/red]")
    except FileNotFoundError:
        console.print("[red]Error: scontrol not found[/red]")


@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument("nodes", nargs=-1, required=True)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be done without making changes",
)
@click.option(
    "--verbose", "-v", is_flag=True, help="Enable verbose output"
)
@click.pass_context
def cancel_reboot(
    ctx: click.Context,
    nodes: Tuple[str, ...],
    dry_run: bool = False,
    verbose: bool = False,
) -> None:
    """Cancel pending reboot on nodes.

    Supports node filters with optional exclusion (prefix with not:):
    - partition=NAME, not:partition=NAME
    - state=STATE, not:state=STATE
    - user=USER, not:user=USER
    - reservation=NAME, not:reservation=NAME

    \b
    Examples:
      slurm-cli cancel-reboot node001
      slurm-cli cancel-reboot node[001-010]
      slurm-cli cancel-reboot partition=gpu
      slurm-cli cancel-reboot partition=gpu not:reservation=maint
    """
    dry_run = get_dry_run(ctx, dry_run)
    # Resolve node filters with exclusions
    resolved_nodes, other_args = resolve_node_filters(
        list(nodes), verbose
    )

    if not resolved_nodes:
        console.print(
            "[red]Error: No nodes specified or all excluded[/red]"
        )
        return

    # Convert set to sorted list for consistent output
    actual_nodes = sorted(resolved_nodes)
    nodelist = ",".join(actual_nodes)

    args = ["scontrol", "cancel_reboot", nodelist]

    if verbose:
        console.print(f"[dim]Running: {' '.join(args)}[/dim]")

    if dry_run:
        console.print(f"[yellow]DRY RUN:[/yellow] {' '.join(args)}")
        return

    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            check=True,
        )
        if result.stdout:
            console.print(result.stdout.strip())
        console.print(
            f"[green]Cancelled reboot for node(s): {nodelist}[/green]"
        )
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error: {e.stderr.strip() or e}[/red]")
    except FileNotFoundError:
        console.print("[red]Error: scontrol not found[/red]")


@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument("jobs", nargs=-1, required=True)
@click.option(
    "--reason", "-r", default=None, help="Reason for holding jobs"
)
@click.option(
    "--user",
    "-u",
    is_flag=True,
    help="Use user hold (uhold) - only job owner or admin can release",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be done without making changes",
)
@click.option(
    "--verbose", "-v", is_flag=True, help="Enable verbose output"
)
@click.pass_context
def hold(
    ctx: click.Context,
    jobs: Tuple[str, ...],
    reason: Optional[str] = None,
    user: bool = False,
    dry_run: bool = False,
    verbose: bool = False,
) -> None:
    """Hold jobs (prevent them from starting).

    Use --user/-u for user hold (scontrol uhold) which can only be
    released by the job owner or an administrator.

    Supports job filters with optional exclusion (prefix with not:):
    - user=USER, not:user=USER
    - account=ACCOUNT, not:account=ACCOUNT
    - partition=PARTITION, not:partition=PARTITION
    - state=STATE, not:state=STATE
    - name=PATTERN, not:name=PATTERN

    \b
    Examples:
      slurm-cli hold 12345
      slurm-cli hold 12345 12346 12347
      slurm-cli hold user=john
      slurm-cli hold partition=gpu --reason="Maintenance"
      slurm-cli hold 12345 -r "Waiting for data"
      slurm-cli hold 12345 reason="Need review"
      slurm-cli hold partition=gpu not:user=admin
      slurm-cli hold -u 12345              # user hold
      slurm-cli hold --user 12345 -r "Review needed"
    """
    dry_run = get_dry_run(ctx, dry_run)
    args_list = list(jobs)
    inline_reason = None
    job_args = []

    for arg in args_list:
        if arg.lower().startswith("reason="):
            inline_reason = arg.split("=", 1)[1]
        else:
            job_args.append(arg)

    # Resolve job filters with exclusion support
    job_ids_set, other_args = resolve_job_filters(job_args, verbose)
    job_ids = list(job_ids_set)

    if not job_ids:
        console.print("[red]Error: No jobs specified or found[/red]")
        return

    # Use --reason option if provided, otherwise use inline reason=
    final_reason = reason if reason is not None else inline_reason

    # Build scontrol hold/uhold command
    hold_cmd = "uhold" if user else "hold"
    for job_id in job_ids:
        args = ["scontrol", hold_cmd]
        if final_reason:
            args.append(f"reason={final_reason}")
        args.append(job_id)

        if dry_run:
            console.print(f"[yellow]DRY RUN:[/yellow] {' '.join(args)}")
            continue

        if verbose:
            console.print(f"[dim]Running: {' '.join(args)}[/dim]")

        try:
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                check=True,
            )
            if result.stdout:
                console.print(result.stdout.strip())
        except subprocess.CalledProcessError as e:
            console.print(
                f"[red]Error holding job {job_id}: "
                f"{e.stderr.strip() or e}[/red]"
            )
        except FileNotFoundError:
            console.print("[red]Error: scontrol not found[/red]")
            return

    if job_ids and not dry_run:
        hold_type = "User held" if user else "Held"
        console.print(
            f"[green]{hold_type} job(s): {', '.join(job_ids)}[/green]"
        )


@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument("jobs", nargs=-1, required=True)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be done without making changes",
)
@click.option(
    "--verbose", "-v", is_flag=True, help="Enable verbose output"
)
@click.pass_context
def release(
    ctx: click.Context,
    jobs: Tuple[str, ...],
    dry_run: bool = False,
    verbose: bool = False,
) -> None:
    """Release held jobs (allow them to start).

    Supports job filters with optional exclusion (prefix with not:):
    - user=USER, not:user=USER
    - account=ACCOUNT, not:account=ACCOUNT
    - partition=PARTITION, not:partition=PARTITION
    - state=STATE, not:state=STATE
    - name=PATTERN, not:name=PATTERN

    \b
    Examples:
      slurm-cli release 12345
      slurm-cli release 12345 12346 12347
      slurm-cli release user=john
      slurm-cli release state=pending
      slurm-cli release partition=gpu not:user=admin
    """
    dry_run = get_dry_run(ctx, dry_run)
    # Resolve job filters with exclusion support
    job_ids_set, other_args = resolve_job_filters(list(jobs), verbose)
    job_ids = list(job_ids_set)

    if not job_ids:
        console.print("[red]Error: No jobs specified or found[/red]")
        return

    for job_id in job_ids:
        args = ["scontrol", "release", job_id]

        if dry_run:
            console.print(f"[yellow]DRY RUN:[/yellow] {' '.join(args)}")
            continue

        if verbose:
            console.print(f"[dim]Running: {' '.join(args)}[/dim]")

        try:
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                check=True,
            )
            if result.stdout:
                console.print(result.stdout.strip())
        except subprocess.CalledProcessError as e:
            console.print(
                f"[red]Error releasing job {job_id}: "
                f"{e.stderr.strip() or e}[/red]"
            )
        except FileNotFoundError:
            console.print("[red]Error: scontrol not found[/red]")
            return

    if job_ids and not dry_run:
        console.print(
            f"[green]Released job(s): {', '.join(job_ids)}[/green]"
        )


@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument("jobs", nargs=-1, required=True)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be done without making changes",
)
@click.option(
    "--verbose", "-v", is_flag=True, help="Enable verbose output"
)
@click.pass_context
def top(
    ctx: click.Context,
    jobs: Tuple[str, ...],
    dry_run: bool = False,
    verbose: bool = False,
) -> None:
    """Move jobs to the top of the queue.

    Supports job filters with optional exclusion (prefix with not:):
    - user=USER, not:user=USER
    - account=ACCOUNT, not:account=ACCOUNT
    - partition=PARTITION, not:partition=PARTITION
    - state=STATE, not:state=STATE
    - name=PATTERN, not:name=PATTERN

    \b
    Examples:
      slurm-cli top 12345
      slurm-cli top 12345 12346 12347
      slurm-cli top user=john
      slurm-cli top partition=gpu not:user=admin
    """
    dry_run = get_dry_run(ctx, dry_run)
    # Resolve job filters with exclusion support
    job_ids_set, other_args = resolve_job_filters(list(jobs), verbose)
    job_ids = list(job_ids_set)

    if not job_ids:
        console.print("[red]Error: No jobs specified or found[/red]")
        return

    # scontrol top takes comma-separated job list
    job_list = ",".join(job_ids)
    args = ["scontrol", "top", job_list]

    if dry_run:
        console.print(f"[yellow]DRY RUN:[/yellow] {' '.join(args)}")
        return

    if verbose:
        console.print(f"[dim]Running: {' '.join(args)}[/dim]")

    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            check=True,
        )
        if result.stdout:
            console.print(result.stdout.strip())
        console.print(f"[green]Moved to top: {job_list}[/green]")
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error: {e.stderr.strip() or e}[/red]")
    except FileNotFoundError:
        console.print("[red]Error: scontrol not found[/red]")


@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument("jobs", nargs=-1, required=True)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be done without making changes",
)
@click.option(
    "--verbose", "-v", is_flag=True, help="Enable verbose output"
)
@click.pass_context
def requeue(
    ctx: click.Context,
    jobs: Tuple[str, ...],
    dry_run: bool = False,
    verbose: bool = False,
) -> None:
    """Requeue jobs (restart from beginning).

    Supports job filters with optional exclusion (prefix with not:):
    - user=USER, not:user=USER
    - account=ACCOUNT, not:account=ACCOUNT
    - partition=PARTITION, not:partition=PARTITION
    - state=STATE, not:state=STATE
    - name=PATTERN, not:name=PATTERN

    \b
    Examples:
      slurm-cli requeue 12345
      slurm-cli requeue 12345 12346 12347
      slurm-cli requeue user=john
      slurm-cli requeue state=failed
      slurm-cli requeue partition=gpu not:state=running
    """
    dry_run = get_dry_run(ctx, dry_run)
    # Resolve job filters with exclusion support
    job_ids_set, other_args = resolve_job_filters(list(jobs), verbose)
    job_ids = list(job_ids_set)

    if not job_ids:
        console.print("[red]Error: No jobs specified or found[/red]")
        return

    for job_id in job_ids:
        args = ["scontrol", "requeue", job_id]

        if dry_run:
            console.print(f"[yellow]DRY RUN:[/yellow] {' '.join(args)}")
            continue

        if verbose:
            console.print(f"[dim]Running: {' '.join(args)}[/dim]")

        try:
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                check=True,
            )
            if result.stdout:
                console.print(result.stdout.strip())
        except subprocess.CalledProcessError as e:
            console.print(
                f"[red]Error requeuing job {job_id}: "
                f"{e.stderr.strip() or e}[/red]"
            )
        except FileNotFoundError:
            console.print("[red]Error: scontrol not found[/red]")
            return

    if job_ids and not dry_run:
        console.print(
            f"[green]Requeued job(s): {', '.join(job_ids)}[/green]"
        )


@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument("jobs", nargs=-1, required=True)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be done without making changes",
)
@click.option(
    "--verbose", "-v", is_flag=True, help="Enable verbose output"
)
@click.pass_context
def suspend(
    ctx: click.Context,
    jobs: Tuple[str, ...],
    dry_run: bool = False,
    verbose: bool = False,
) -> None:
    """Suspend running jobs.

    Supports job filters with optional exclusion (prefix with not:):
    - user=USER, not:user=USER
    - account=ACCOUNT, not:account=ACCOUNT
    - partition=PARTITION, not:partition=PARTITION
    - state=STATE, not:state=STATE
    - name=PATTERN, not:name=PATTERN

    \b
    Examples:
      slurm-cli suspend 12345
      slurm-cli suspend 12345 12346 12347
      slurm-cli suspend user=john
      slurm-cli suspend partition=gpu
      slurm-cli suspend partition=gpu not:user=admin
    """
    dry_run = get_dry_run(ctx, dry_run)
    # Resolve job filters with exclusion support
    job_ids_set, other_args = resolve_job_filters(list(jobs), verbose)
    job_ids = list(job_ids_set)

    if not job_ids:
        console.print("[red]Error: No jobs specified or found[/red]")
        return

    for job_id in job_ids:
        args = ["scontrol", "suspend", job_id]

        if dry_run:
            console.print(f"[yellow]DRY RUN:[/yellow] {' '.join(args)}")
            continue

        if verbose:
            console.print(f"[dim]Running: {' '.join(args)}[/dim]")

        try:
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                check=True,
            )
            if result.stdout:
                console.print(result.stdout.strip())
        except subprocess.CalledProcessError as e:
            console.print(
                f"[red]Error suspending job {job_id}: "
                f"{e.stderr.strip() or e}[/red]"
            )
        except FileNotFoundError:
            console.print("[red]Error: scontrol not found[/red]")
            return

    if job_ids and not dry_run:
        console.print(
            f"[green]Suspended job(s): {', '.join(job_ids)}[/green]"
        )


@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument("word", required=False)
@click.argument("subcommand", required=False)
@common_options
@click.pass_context
def help(
    ctx: click.Context,
    word: Optional[str] = None,
    subcommand: Optional[str] = None,
    style: Optional[str] = None,
    pretty: bool = False,
    json: bool = False,
    csv: bool = False,
    zebra: Optional[bool] = None,
    delimiter: Optional[str] = None,
    **kwargs,
) -> None:
    """Show FULL help information and available resources."""
    if subcommand:
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
            zebra_val = get_zebra(ctx, zebra)
            table = Table(
                title=f"Autocomplete results for '{word}'",
                box=SIMPLE_HEAVY,
                pad_edge=False,
                padding=(0, 0),
                row_styles=get_row_styles(zebra_val),
            )
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
        # Show the main CLI help (from parent context)
        parent_ctx = ctx.parent
        if parent_ctx:
            click.echo(parent_ctx.get_help())
        else:
            # Fallback to current context if no parent
            click.echo(ctx.get_help())

        # Add resource list below with zebra option
        zebra_val = get_zebra(ctx, zebra)
        show_command_help_with_resources(zebra_override=zebra_val)


# Register commands when module is imported
register_commands()


if __name__ == "__main__":
    main()
