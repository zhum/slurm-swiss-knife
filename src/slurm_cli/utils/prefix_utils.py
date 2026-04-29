"""Utilities for computing shortest unique prefixes.

This module provides functions for computing the shortest unique prefix
for each string in a collection, which is useful for:
1. Command-line argument prefix matching
2. Bash autocompletion pattern generation
"""

from typing import Dict, List, Optional, Set, Tuple


def compute_shortest_unique_prefixes(
    items: List[str], min_length: int = 1
) -> Dict[str, str]:
    """Compute the shortest unique prefix for each item.

    For a list of strings, finds the shortest prefix that uniquely
    identifies each string from all others in the list.

    Args:
        items: List of strings to compute prefixes for
        min_length: Minimum prefix length (default: 1)

    Returns:
        Dictionary mapping each item to its shortest unique prefix

    Example:
        >>> compute_shortest_unique_prefixes(['show', 'create', 'cancel'])
        {'show': 'sh', 'create': 'cr', 'cancel': 'ca'}
    """
    if not items:
        return {}

    result: Dict[str, str] = {}
    items_set = set(items)

    for item in items:
        # Start with minimum length prefix
        for length in range(min_length, len(item) + 1):
            prefix = item[:length]
            # Check if this prefix uniquely identifies this item
            matches = [s for s in items_set if s.startswith(prefix)]
            if len(matches) == 1:
                result[item] = prefix
                break
        else:
            # Full string needed (shouldn't happen with unique items)
            result[item] = item

    return result


def compute_prefix_conflicts(items: List[str]) -> Dict[str, Set[str]]:
    """Find items that share prefixes with other items.

    Args:
        items: List of strings to analyze

    Returns:
        Dictionary mapping each item to set of items it conflicts with
    """
    conflicts: Dict[str, Set[str]] = {item: set() for item in items}

    for i, item1 in enumerate(items):
        for item2 in items[i + 1 :]:
            # Check if one is a prefix of the other
            if item1.startswith(item2) or item2.startswith(item1):
                conflicts[item1].add(item2)
                conflicts[item2].add(item1)

    return conflicts


def generate_bash_prefix_pattern(prefix: str, full_name: str) -> str:
    """Generate a bash case pattern for prefix matching.

    Args:
        prefix: The shortest unique prefix
        full_name: The full command/resource name

    Returns:
        Bash glob pattern that matches the prefix and optionally more

    Example:
        >>> generate_bash_prefix_pattern('sh', 'show')
        'sh*'
        >>> generate_bash_prefix_pattern('show', 'show')
        'show'
    """
    if prefix == full_name:
        return full_name
    return f"{prefix}*"


def generate_bash_case_patterns(
    items_with_prefixes: Dict[str, str],
    aliases: Dict[str, List[str]] = None,
) -> Dict[str, str]:
    """Generate bash case patterns for all items.

    Args:
        items_with_prefixes: Dict mapping items to their shortest prefixes
        aliases: Optional dict mapping items to their aliases

    Returns:
        Dict mapping canonical names to bash pattern strings

    Example:
        >>> prefixes = {'show': 'sh', 'create': 'cr'}
        >>> aliases = {'show': ['get', 'list']}
        >>> generate_bash_case_patterns(prefixes, aliases)
        {'show': 'sh*|get*|list*', 'create': 'cr*'}
    """
    aliases = aliases or {}
    result: Dict[str, str] = {}

    for item, prefix in items_with_prefixes.items():
        patterns = [generate_bash_prefix_pattern(prefix, item)]

        # Add alias patterns
        if item in aliases:
            alias_prefixes = compute_shortest_unique_prefixes(
                aliases[item], min_length=1
            )
            for alias, alias_prefix in alias_prefixes.items():
                patterns.append(
                    generate_bash_prefix_pattern(alias_prefix, alias)
                )

        result[item] = "|".join(patterns)

    return result


class PrefixMatcher:
    """Efficient prefix matcher for command/resource names.

    This class precomputes prefix mappings for fast lookups.
    """

    def __init__(
        self,
        items: List[str],
        aliases: Dict[str, List[str]] = None,
        min_prefix_length: int = 1,
    ):
        """Initialize the prefix matcher.

        Args:
            items: List of canonical names
            aliases: Optional dict mapping canonical names to aliases
            min_prefix_length: Minimum prefix length to accept
        """
        self.items = list(items)
        self.aliases = aliases or {}
        self.min_prefix_length = min_prefix_length

        # Build all possible names (canonical + aliases)
        self._all_names: Dict[str, str] = {}  # name -> canonical
        for item in items:
            self._all_names[item] = item
            for alias in self.aliases.get(item, []):
                self._all_names[alias] = item

        # Compute shortest unique prefixes
        all_names_list = list(self._all_names.keys())
        self._prefixes = compute_shortest_unique_prefixes(
            all_names_list, min_prefix_length
        )

        # Build prefix lookup table
        self._prefix_to_canonical: Dict[str, str] = {}
        for name, canonical in self._all_names.items():
            # Add all prefixes from shortest unique to full name
            shortest = self._prefixes.get(name, name)
            for length in range(len(shortest), len(name) + 1):
                prefix = name[:length]
                if prefix not in self._prefix_to_canonical:
                    self._prefix_to_canonical[prefix] = canonical

    def match(self, input_str: str) -> Tuple[str, bool]:
        """Match an input string to a canonical name.

        Args:
            input_str: User input to match

        Returns:
            Tuple of (canonical_name, is_exact_match)
            Returns (input_str, False) if no match found
        """
        input_lower = input_str.lower()

        # Try exact match first
        if input_lower in self._all_names:
            return self._all_names[input_lower], True

        # Try prefix match
        if input_lower in self._prefix_to_canonical:
            return self._prefix_to_canonical[input_lower], False

        # Try finding items that start with input
        matches = [
            name
            for name in self._all_names.keys()
            if name.startswith(input_lower)
        ]
        if len(matches) == 1:
            return self._all_names[matches[0]], False

        return input_str, False

    def get_shortest_prefix(self, name: str) -> str:
        """Get the shortest unique prefix for a name.

        Args:
            name: Canonical name or alias

        Returns:
            Shortest unique prefix
        """
        return self._prefixes.get(name, name)

    def get_bash_patterns(self) -> Dict[str, str]:
        """Get bash case patterns for all canonical names.

        Returns:
            Dict mapping canonical names to bash pattern strings
        """
        return generate_bash_case_patterns(self._prefixes, self.aliases)

    def get_all_names(self) -> List[str]:
        """Get all valid names (canonical + aliases)."""
        return list(self._all_names.keys())


# Pre-defined command configuration
COMMANDS = {
    "show": {"aliases": ["get"], "description": "Show/list resources"},
    "create": {
        "aliases": ["new", "add"],
        "description": "Create new resources",
    },
    "update": {
        "aliases": ["edit", "change", "modify", "set"],
        "description": "Update existing resources",
    },
    "delete": {
        "aliases": ["remove", "rm"],
        "description": "Delete resources",
    },
    "list-resources": {
        "aliases": ["ls", "list"],
        "description": "List available resources",
    },
    "autocomplete": {
        "aliases": [],
        "description": "Print bash autocomplete function",
    },
    "help": {"aliases": [], "description": "Show help"},
    "version": {"aliases": [], "description": "Show version"},
    "reconfigure": {
        "aliases": ["confreload"],
        "description": "Reconfigure Slurm controller",
    },
    "ping": {"aliases": [], "description": "Ping Slurm controller"},
    "takeover": {
        "aliases": [],
        "description": "Takeover as primary controller",
    },
    "write_config": {
        "aliases": ["wconf", "w_conf"],  # Include both hyphen and underscore variants
        "description": "Write Slurm configuration file",
    },
    "token": {"aliases": [], "description": "Generate auth token"},
    "assoc_mgr": {
        "aliases": [],
        "description": "Display slurmctld's internal cache",
    },
    "drain": {"aliases": [], "description": "Drain nodes"},
    "undrain": {
        "aliases": ["resume"],
        "description": "Undrain/resume nodes",
    },
    "reboot": {"aliases": [], "description": "Reboot nodes"},
    "cancel_reboot": {
        "aliases": [],
        "description": "Cancel node reboot",
    },
    "hold": {"aliases": [], "description": "Hold jobs"},
    "release": {"aliases": [], "description": "Release held jobs"},
    "top": {"aliases": [], "description": "Move jobs to top of queue"},
    "requeue": {"aliases": [], "description": "Requeue jobs"},
    "suspend": {"aliases": [], "description": "Suspend jobs"},
}

# Pre-defined resource configuration with help info
# Each resource has: aliases, description, and actions
# (create/update/delete/show)
# Each action has: syntax, examples, options
RESOURCES = {
    "partitions": {
        "aliases": ["part", "parts"],
        "description": "Manage Slurm partitions",
        "actions": {
            "create": {
                "syntax": "slurm-cli add part NAME [OPTIONS]",
                "examples": [
                    "slurm-cli add part batch nodes=node[01-10]",
                    "slurm-cli add part gpu nodes=gpu[01-04] state=up",
                ],
                "options": [
                    "name",
                    "nodes",
                    "state",
                    "maxtime",
                    "default",
                    "hidden",
                ],
            },
            "update": {
                "syntax": "slurm-cli mod part NAME set KEY=VALUE",
                "examples": [
                    "slurm-cli mod part batch set state=drain",
                    "slurm-cli mod part gpu set maxtime=24:00:00",
                ],
                "options": [
                    "state",
                    "maxtime",
                    "nodes",
                    "default",
                    "hidden",
                ],
            },
            "delete": {
                "syntax": "slurm-cli del part NAME",
                "examples": ["slurm-cli del part oldpartition"],
                "options": ["name"],
            },
            "show": {
                "syntax": "slurm-cli show part [NAME]",
                "examples": [
                    "slurm-cli show part",
                    "slurm-cli show part batch",
                ],
                "options": ["name", "state"],
            },
        },
    },
    "nodes": {
        "aliases": ["node"],
        "description": "Manage Slurm compute nodes",
        "actions": {
            "update": {
                "syntax": "slurm-cli mod nodes NAME set KEY=VALUE",
                "examples": [
                    "slurm-cli mod nodes node01 set state=drain"
                    " reason='Maintenance'",
                    "slurm-cli mod nodes gpu[01-04] set state=resume",
                ],
                "options": ["state", "reason", "weight", "features"],
            },
            "show": {
                "syntax": "slurm-cli show nodes [NAME]",
                "examples": [
                    "slurm-cli show nodes",
                    "slurm-cli show nodes node01",
                    "slurm-cli show nodes state=idle",
                ],
                "options": ["name", "state", "partition"],
            },
        },
    },
    "jobs": {
        "aliases": ["job", "j"],
        "description": "View and manage Slurm jobs",
        "actions": {
            "show": {
                "syntax": "slurm-cli show jobs [FILTER]",
                "examples": [
                    "slurm-cli show jobs",
                    "slurm-cli show jobs user=john",
                    "slurm-cli show jobs state=running",
                ],
                "options": ["user", "account", "partition", "state"],
            },
            "delete": {
                "syntax": "slurm-cli del jobs JOBID [JOBID...] [FILTER]",
                "examples": [
                    "slurm-cli del jobs 12345",
                    "slurm-cli del jobs 12345 12346 12347",
                    "slurm-cli del jobs user=john",
                    "slurm-cli del jobs state=pending partition=batch",
                ],
                "options": [
                    "user",
                    "account",
                    "partition",
                    "state",
                    "name",
                    "jobname",
                ],
            },
        },
    },
    "users": {
        "aliases": ["user"],
        "description": "Manage Slurm user accounts",
        "actions": {
            "create": {
                "syntax": "slurm-cli add users USERNAME [OPTIONS]",
                "examples": [
                    "slurm-cli add users john account=research",
                    "slurm-cli add users name=jane account=eng"
                    " defaultaccount=eng",
                ],
                "options": [
                    "name",
                    "account",
                    "adminlevel",
                    "cluster",
                    "defaultaccount",
                    "defaultwckey",
                    "partition",
                ],
            },
            "delete": {
                "syntax": "slurm-cli del users USERNAME",
                "examples": [
                    "slurm-cli del users john",
                    "slurm-cli del users -y john",
                ],
                "options": ["name"],
            },
            "update": {
                "syntax": "slurm-cli mod users USERNAME set KEY=VALUE",
                "examples": [
                    "slurm-cli mod users john set adminlevel=operator",
                    "slurm-cli mod users defaultaccount=old set"
                    " defaultaccount=new",
                ],
                "options": [
                    "adminlevel",
                    "defaultaccount",
                    "defaultwckey",
                    "newname",
                    "partition",
                ],
            },
            "show": {
                "syntax": "slurm-cli show users [FILTER]",
                "examples": [
                    "slurm-cli show users",
                    "slurm-cli show users adminlevel=Admin",
                ],
                "options": ["name", "account", "adminlevel", "cluster"],
            },
        },
    },
    "qos": {
        "aliases": ["q"],
        "description": "Manage Slurm Quality of Service settings",
        "actions": {
            "create": {
                "syntax": "slurm-cli add qos NAME [OPTIONS]",
                "examples": [
                    "slurm-cli add qos highprio priority=1000",
                    "slurm-cli add qos express maxwall=1:00:00"
                    " preemptmode=cancel",
                ],
                "options": [
                    "name",
                    "priority",
                    "maxwall",
                    "maxjobspu",
                    "grpjobs",
                    "preemptmode",
                    "flags",
                ],
            },
            "update": {
                "syntax": "slurm-cli mod qos NAME set KEY=VALUE",
                "examples": [
                    "slurm-cli mod qos normal set priority=500",
                    "slurm-cli mod qos batch set maxjobspu=10"
                    " preemptmode=requeue",
                ],
                "options": [
                    "priority",
                    "maxwall",
                    "maxjobspu",
                    "grpjobs",
                    "preemptmode",
                ],
            },
            "delete": {
                "syntax": "slurm-cli del qos NAME",
                "examples": ["slurm-cli del qos oldqos"],
                "options": ["name"],
            },
            "show": {
                "syntax": "slurm-cli show qos [NAME]",
                "examples": [
                    "slurm-cli show qos",
                    "slurm-cli show qos normal",
                ],
                "options": ["name"],
            },
        },
    },
    "accounts": {
        "aliases": ["acc", "account"],
        "description": "Manage Slurm accounts hierarchy",
        "actions": {
            "create": {
                "syntax": "slurm-cli add accounts NAME [OPTIONS]",
                "examples": [
                    "slurm-cli add accounts research organization=university",
                    "slurm-cli add accounts eng parent=root"
                    " description='Engineering'",
                ],
                "options": [
                    "name",
                    "organization",
                    "parent",
                    "description",
                    "defaultqos",
                ],
            },
            "update": {
                "syntax": "slurm-cli mod accounts NAME set KEY=VALUE",
                "examples": [
                    "slurm-cli mod accounts research set "
                    "description='New desc'",
                    "slurm-cli mod accounts parent=old set parent=new",
                ],
                "options": [
                    "description",
                    "organization",
                    "parent",
                    "defaultqos",
                ],
            },
            "delete": {
                "syntax": "slurm-cli del accounts NAME",
                "examples": ["slurm-cli del accounts oldaccount"],
                "options": ["name"],
            },
            "show": {
                "syntax": "slurm-cli show accounts [FILTER]",
                "examples": [
                    "slurm-cli show accounts",
                    "slurm-cli show accounts organization=nvidia",
                ],
                "options": [
                    "name",
                    "organization",
                    "parent",
                    "description",
                ],
            },
        },
    },
    "associations": {
        "aliases": ["assoc"],
        "description": "Manage Slurm user-account associations",
        "actions": {
            "create": {
                "syntax": "slurm-cli add assoc user=USERNAME account=ACCOUNT"
                " [OPTIONS]",
                "examples": [
                    "slurm-cli add assoc user=john account=research",
                    "slurm-cli add assoc name=jane account=eng "
                    "qos=normal,high",
                ],
                "options": [
                    "name/user",
                    "account",
                    "cluster",
                    "partition",
                    "fairshare",
                    "qos",
                    "defaultqos",
                    "maxjobs",
                    "maxsubmit",
                ],
            },
            "update": {
                "syntax": "slurm-cli mod assoc user=USER account=ACCOUNT"
                " set KEY=VALUE",
                "examples": [
                    "slurm-cli mod assoc user=john account=research set"
                    " fairshare=100",
                    "slurm-cli mod assoc account=eng set defaultqos=normal",
                ],
                "options": [
                    "fairshare",
                    "qos",
                    "defaultqos",
                    "grpjobs",
                    "grpsubmit",
                    "maxjobs",
                    "maxsubmit",
                    "maxwall",
                ],
            },
            "show": {
                "syntax": "slurm-cli show assoc [FILTER] [--tree]",
                "examples": [
                    "slurm-cli show assoc",
                    "slurm-cli show assoc user=john",
                    "slurm-cli show assoc account=research --tree",
                ],
                "options": [
                    "user",
                    "account",
                    "cluster",
                    "partition",
                    "--tree",
                    "--indent",
                ],
            },
        },
    },
    "reservations": {
        "aliases": ["reservation"],
        "description": "Manage Slurm reservations",
        "actions": {
            "create": {
                "syntax": "slurm-cli add res NAME [OPTIONS]",
                "examples": [
                    "slurm-cli add res maint starttime=now duration=2:00:00"
                    " nodes=ALL",
                    "slurm-cli add res team users=john,jane nodes=node[01-04]",
                ],
                "options": [
                    "name",
                    "starttime",
                    "duration",
                    "endtime",
                    "nodes",
                    "users",
                    "accounts",
                ],
            },
            "update": {
                "syntax": "slurm-cli mod res NAME set KEY=VALUE",
                "examples": [
                    "slurm-cli mod res maint set duration=4:00:00",
                    "slurm-cli mod res team set users+=newuser",
                ],
                "options": [
                    "duration",
                    "endtime",
                    "nodes",
                    "users",
                    "accounts",
                ],
            },
            "delete": {
                "syntax": "slurm-cli del res NAME",
                "examples": ["slurm-cli del res oldreservation"],
                "options": ["name"],
            },
            "show": {
                "syntax": "slurm-cli show res [NAME]",
                "examples": [
                    "slurm-cli show res",
                    "slurm-cli show res maint",
                ],
                "options": ["name"],
            },
        },
    },
    "coordinators": {
        "aliases": ["coord"],
        "description": "Manage Slurm account coordinators",
        "actions": {
            "create": {
                "syntax": "slurm-cli add coord USER account=ACCOUNT",
                "examples": [
                    "slurm-cli add coord john account=research",
                    "slurm-cli add coord user=jane account=engineering",
                ],
                "options": ["user", "name", "account"],
            },
            "delete": {
                "syntax": "slurm-cli del coord user=USER account=ACCOUNT",
                "examples": [
                    "slurm-cli del coord user=john account=research",
                    "slurm-cli del coord account=eng user=alice -y",
                ],
                "options": ["user", "name", "account"],
            },
            "show": {
                "syntax": "slurm-cli show coord [account=ACCOUNT] [user=USER]",
                "examples": [
                    "slurm-cli show coord",
                    "slurm-cli show coord account=research",
                    "slurm-cli show coord user=john",
                ],
                "options": ["account", "user", "name"],
            },
        },
    },
    "events": {
        "aliases": ["event", "ev"],
        "description": "View Slurm cluster events",
        "actions": {
            "show": {
                "syntax": "slurm-cli show events [FILTER]",
                "examples": [
                    "slurm-cli show events",
                    "slurm-cli show events node=node01",
                    "slurm-cli show events state=down",
                ],
                "options": ["node", "state", "user", "cluster"],
            },
        },
    },
    "problems": {
        "aliases": ["prob"],
        "description": "Show problematic Slurm entities",
    },
    "stats": {
        "aliases": ["stat"],
        "description": "Show Slurm scheduler statistics",
    },
    "config": {
        "aliases": ["conf", "cfg"],
        "description": "Show Slurm configuration",
    },
    "licenses": {
        "aliases": ["lic", "license"],
        "description": "View Slurm license usage",
    },
    "dumps": {
        "aliases": ["dump"],
        "description": "Show Slurm database dumps",
    },
    "resources": {
        "aliases": ["reso"],
        "description": "Show Slurm cluster resources",
    },
    "bads": {
        "aliases": ["bad", "b"],
        "description": "Show problematic jobs",
    },
    "runawayjobs": {
        "aliases": ["runaway", "runa"],
        "description": "Show runaway jobs",
    },
    "tres": {
        "aliases": ["tr"],
        "description": "Show trackable resources",
    },
    "archive": {
        "aliases": ["ar"],
        "description": "Show archive information",
    },
    "transactions": {
        "aliases": ["tra", "trans"],
        "description": "Show database transactions",
    },
}


def get_resource_help(
    resource: str, action: str = None
) -> Optional[Dict]:
    """Get help info for a resource and optionally a specific action.

    Args:
        resource: Resource name (canonical or alias)
        action: Optional action name (create, update, delete, show)

    Returns:
        Help dict with description, syntax, examples, options or None
    """
    # Resolve alias to canonical name
    canonical = None
    for res, info in RESOURCES.items():
        if resource == res or resource in info.get("aliases", []):
            canonical = res
            break

    if not canonical:
        return None

    res_info = RESOURCES[canonical]
    if action:
        actions = res_info.get("actions", {})
        return actions.get(action)
    return res_info


def get_command_matcher() -> PrefixMatcher:
    """Get a PrefixMatcher for CLI commands."""
    items = list(COMMANDS.keys())
    aliases = {cmd: info["aliases"] for cmd, info in COMMANDS.items()}
    return PrefixMatcher(items, aliases, min_prefix_length=1)


def get_resource_matcher() -> PrefixMatcher:
    """Get a PrefixMatcher for resource types."""
    items = list(RESOURCES.keys())
    aliases = {res: info["aliases"] for res, info in RESOURCES.items()}
    return PrefixMatcher(items, aliases, min_prefix_length=1)


# Singleton instances for reuse
_command_matcher: PrefixMatcher = None
_resource_matcher: PrefixMatcher = None


def get_cached_command_matcher() -> PrefixMatcher:
    """Get cached command matcher (singleton)."""
    global _command_matcher
    if _command_matcher is None:
        _command_matcher = get_command_matcher()
    return _command_matcher


def get_cached_resource_matcher() -> PrefixMatcher:
    """Get cached resource matcher (singleton)."""
    global _resource_matcher
    if _resource_matcher is None:
        _resource_matcher = get_resource_matcher()
    return _resource_matcher


def generate_bash_command_case() -> str:
    """Generate bash case statement for command matching.

    Returns:
        Bash script fragment with case patterns for all commands
    """
    lines = []

    # Collect all names (commands + aliases) to compute global unique prefixes
    all_names = []
    name_to_cmd = {}
    for cmd, info in COMMANDS.items():
        all_names.append(cmd)
        name_to_cmd[cmd] = cmd
        for alias in info["aliases"]:
            all_names.append(alias)
            name_to_cmd[alias] = cmd

    # Compute shortest unique prefixes across all names
    prefixes = compute_shortest_unique_prefixes(all_names)

    # Group patterns by canonical command
    cmd_patterns: Dict[str, List[str]] = {cmd: [] for cmd in COMMANDS}
    for name, prefix in prefixes.items():
        canonical = name_to_cmd[name]
        if prefix == name:
            cmd_patterns[canonical].append(name)
        else:
            cmd_patterns[canonical].append(f"{prefix}*")

    for cmd, patterns in cmd_patterns.items():
        if not patterns:
            continue
        pattern = "|".join(patterns)
        lines.append(f"        {pattern})")
        lines.append(f'            guessed="{cmd}"')
        lines.append(f'            cmd="{cmd}"')
        lines.append("            ;;")

    return "\n".join(lines)


def get_all_command_names() -> str:
    """Get all command names (canonical + aliases)
    as space-separated string."""
    names = []
    for cmd, info in COMMANDS.items():
        names.append(cmd)
        names.extend(info["aliases"])
    return " ".join(sorted(set(names)))


def generate_bash_resource_case() -> str:
    """Generate bash case statement for resource matching.

    Returns:
        Bash script fragment with case patterns for all resources
    """
    lines = []

    # Collect all names (resources + aliases) to compute global unique prefixes
    all_names = []
    name_to_res = {}
    for res, info in RESOURCES.items():
        all_names.append(res)
        name_to_res[res] = res
        for alias in info["aliases"]:
            all_names.append(alias)
            name_to_res[alias] = res

    # Compute shortest unique prefixes across all names
    prefixes = compute_shortest_unique_prefixes(all_names)

    # Group patterns by canonical resource
    res_patterns: Dict[str, List[str]] = {res: [] for res in RESOURCES}
    for name, prefix in prefixes.items():
        canonical = name_to_res[name]
        if prefix == name:
            res_patterns[canonical].append(name)
        else:
            res_patterns[canonical].append(f"{prefix}*")

    for res, patterns in res_patterns.items():
        if not patterns:
            continue
        pattern = "|".join(patterns)
        lines.append(f"        {pattern})")
        lines.append(f'            guessed="{res}"')
        lines.append("            ;;")

    return "\n".join(lines)


def get_all_resource_names() -> str:
    """Get all resource names (canonical + aliases)
    as space-separated string."""
    names = []
    for res, info in RESOURCES.items():
        names.append(res)
        names.extend(info["aliases"])
    return " ".join(sorted(set(names)))


def get_resources_help_list(action: str = None, indent: int = 2) -> str:
    """Generate a formatted list of resources for help text.

    Args:
        action: If provided, only show resources that support this action
        indent: Number of spaces to indent

    Returns:
        Formatted string with resource list
    """
    lines = []
    prefix = " " * indent

    for res, info in sorted(RESOURCES.items()):
        # Skip if action specified and resource doesn't support it
        if action and "actions" in info:
            if action not in info["actions"]:
                continue
        elif action and "actions" not in info:
            # Resource has no actions defined, skip for action-specific lists
            continue

        # Get aliases
        aliases = info.get("aliases", [])
        alias_str = f" ({', '.join(aliases)})" if aliases else ""

        # Get description
        desc = info.get("description", "")

        lines.append(f"{prefix}{res}{alias_str}: {desc}")

    return "\n".join(lines)


def get_resources_epilog(action: str = None) -> str:
    """Generate an epilog string with available resources.

    Args:
        action: If provided, only show resources that support this action

    Returns:
        Epilog string for Click command
    """
    # Build resource list
    resources_list = []
    for res, info in sorted(RESOURCES.items()):
        # Skip if action specified and resource doesn't support it
        if action and "actions" in info:
            if action not in info["actions"]:
                continue
        elif action and "actions" not in info:
            continue

        aliases = info.get("aliases", [])
        alias_str = f" ({', '.join(aliases)})" if aliases else ""
        resources_list.append(f"{res}{alias_str}")

    # Use \b to prevent Click from rewrapping the paragraph
    return "\b\n\nAvailable resources:\n  " + ", ".join(resources_list)
