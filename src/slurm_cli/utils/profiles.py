"""Profile management for Slurm CLI output formatting.

Profiles define custom output templates for different resource types.
They can be loaded from:
  - /etc/slurm/cli.profiles (system-wide)
  - ~/.config/slurm-cli.profiles (user-specific)
  - CLI option --profile-str (inline)
  - CLI option --profile (named profile from file)

Profile file format (YAML-like):

```
[profile:compact]
# Column-based format (table output)
accounts.columns = name,description
accounts.styles.name = cyan bold

# Template-based format (free-form output)
# Use {field} for field values, Rich markup for colors, \\n for newlines
accounts.template = [cyan]{name}[/cyan] - {description}

qos.template = [bold]{name}[/bold] Priority: [green]{priority}[/green]

reservations.template = [cyan bold]{name}[/cyan bold]\\n\
    Time: {start_time} -> {end_time}\\n\
    Users: [hot_pink]{users}[/hot_pink]
```

Inline profile string format:
  accounts.template=[cyan]{name}[/] - {description}

Template syntax:
  - {field_name} - replaced with field value
  - [color]text[/color] - Rich markup for styling
  - \\n - newline (separates records visually)

"""

import os
import re
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

# Profile file locations (in order of precedence, later overrides earlier)
PROFILE_FILES = [
    "/etc/slurm/cli.profiles",
    str(Path.home() / ".config" / "slurm-cli.profiles"),
]

# Available fields for each resource type (for autocomplete)
RESOURCE_FIELDS: Dict[str, List[str]] = {
    "jobs": [
        "job_id",
        "name",
        "user_name",
        "account",
        "partition",
        "job_state",
        "time_limit",
        "endlimit",
        "node_count",
        "nodes",
        "cpus",
        "gres",
        "submit_time",
        "start_time",
        "end_time",
        "priority",
        "reason",
        "command",
        "working_directory",
        "standard_output",
        "standard_error",
    ],
    "nodes": [
        "name",
        "state",
        "cpus",
        "real_memory",
        "gres",
        "partitions",
        "features",
        "reason",
        "alloc_cpus",
        "alloc_memory",
    ],
    "partitions": [
        "partitionname",
        "state",
        "nodes",
        "totalnodes",
        "totalcpus",
        "maxtime",
        "default",
        "defaulttime",
        "defmempercpu",
        "defmempernode",
        "allowgroups",
        "allowaccounts",
        "allowqos",
        "denyaccounts",
        "denyqos",
        "maxnodes",
        "minnodes",
        "maxcpuspernode",
        "maxcpuspersocket",
        "maxmempercpu",
        "maxmempernode",
        "prioritytier",
        "priorityjobfactor",
        "preemptmode",
        "gracetime",
        "oversubscribe",
        "overtimelimit",
        "qos",
        "alternate",
        "allocnodes",
        "cpubind",
        "disablerootjobs",
        "exclusiveuser",
        "hidden",
        "jobdefaults",
        "lln",
        "powerdownonidle",
        "reqresv",
        "rootonly",
        "shared",
        "tresbillingweights",
    ],
    "accounts": [
        "name",
        "description",
        "organization",
        "coordinators",
        "flags",
    ],
    "users": [
        "name",
        "default_account",
        "admin_level",
        "coordinators",
    ],
    "qos": [
        "name",
        "id",
        "priority",
        "max_wall",
        "max_jobs",
        "max_submit",
        "flags",
        "preempt",
        "preempt_mode",
        "grace_time",
    ],
    "reservations": [
        "name",
        "start_time",
        "end_time",
        "nodes",
        "users",
        "accounts",
        "partition",
        "state",
        "flags",
    ],
    "associations": [
        "account",
        "user",
        "cluster",
        "partition",
        "parent_account",
        "qos",
        "default_qos",
        "shares",
        "grp_jobs",
        "grp_submit",
    ],
    "coordinators": [
        "account",
        "name",
    ],
    "events": [
        "time",
        "cluster",
        "node",
        "state",
        "reason",
        "user",
    ],
}

# Default profile templates
DEFAULT_PROFILES: Dict[str, Dict[str, Any]] = {
    "default": {
        # Use dynamic columns (show all non-empty columns)
        "accounts": {
            "columns": "*",
            "styles": {
                "name": "cyan",
                "description": "white",
                "organization": "green",
                "coordinators": "yellow",
            },
        },
        "qos": {
            "columns": "*",
            "styles": {
                "name": "cyan bold",
                "id": "dim",
                "priority": "green",
                "flags": "yellow",
            },
        },
        "partitions": {
            "columns": "*",
            "styles": {
                "name": "cyan bold",
                "state": "green",
                "nodes": "yellow",
            },
        },
        "nodes": {
            "columns": "*",
            "styles": {
                "name": "cyan",
                "state": "green",
            },
        },
        "reservations": {
            "columns": "*",
            "styles": {
                "name": "cyan bold",
                "users": "hot_pink",
                "accounts": "green",
            },
        },
        "coordinators": {
            "columns": "*",
            "styles": {
                "account": "cyan",
                "name": "green",
            },
        },
        "users": {
            "columns": "*",
            "styles": {
                "name": "cyan",
            },
        },
        "associations": {
            "columns": "*",
            "styles": {
                "account": "cyan",
                "user": "green",
                "cluster": "yellow",
                "partition": "magenta",
            },
        },
        "jobs": {
            "columns": [
                "job_id",
                "user_name",
                "partition",
                "job_state",
                "start_time",
                "endlimit",
                "node_count",
                "gres",
                "reason",
            ],
            "styles": {
                "job_id": "cyan bold",
                "user_name": "blue",
                "partition": "green",
                "job_state": "yellow",
                "start_time": "green",
                "endlimit": "dim",
                "node_count": "cyan",
                "gres": "magenta",
            },
        },
    },
    "compact": {
        "accounts": {
            "columns": ["name", "description"],
            "styles": {"name": "cyan bold"},
        },
        "qos": {
            "columns": ["name", "priority", "max_wall"],
            "styles": {"name": "cyan bold"},
        },
        "partitions": {
            "columns": ["name", "state", "nodes"],
            "styles": {"name": "cyan bold"},
        },
        "nodes": {
            "columns": ["name", "state", "cpus", "real_memory", "gres"],
            "styles": {"name": "cyan"},
        },
        "reservations": {
            "columns": [
                "name",
                "start_time",
                "end_time",
                "nodes",
                "users",
            ],
            "styles": {"name": "cyan bold", "users": "hot_pink"},
        },
        "coordinators": {
            "columns": ["account", "name"],
            "styles": {"account": "cyan"},
        },
        "users": {
            "columns": ["name", "default_account"],
            "styles": {"name": "cyan"},
        },
        "associations": {
            "columns": ["account", "user", "cluster", "partition"],
            "styles": {"account": "cyan"},
        },
        "jobs": {
            "columns": [
                "job_id",
                "name",
                "user_name",
                "partition",
                "job_state",
                "endlimit",
                "nodes",
            ],
            "styles": {"job_id": "cyan bold", "job_state": "yellow"},
        },
    },
    "minimal": {
        "accounts": {"columns": ["name"]},
        "qos": {"columns": ["name"]},
        "partitions": {"columns": ["name", "state"]},
        "nodes": {"columns": ["name", "state", "gres"]},
        "reservations": {"columns": ["name"]},
        "coordinators": {"columns": ["account", "name"]},
        "users": {"columns": ["name"]},
        "associations": {"columns": ["account", "user"]},
        "jobs": {"columns": ["job_id", "user_name", "job_state"]},
    },
    # Template-based profiles
    "oneline": {
        "accounts": {
            "template": "[cyan]{name}[/cyan] - {description} ({organization})"
        },
        "qos": {
            "template": (
                "[cyan bold]{name}[/cyan bold] "
                "priority=[green]{priority}[/green] "
                "max_jobs/user={max_jobs_per_user} "
                "max_active/user={max_jobs_active_per_user} "
                "max_tres/job=[yellow]{max_tres_per_job}[/yellow] "
                "max_tres/user=[yellow]{max_tres_per_user}[/yellow] "
                "max_tres_total=[yellow]{max_tres_total}[/yellow]"
            )
        },
        "partitions": {
            "template": (
                "[cyan bold]{PartitionName}[/cyan bold] "
                "state=[green]{State}[/green] nodes={TotalNodes}"
            )
        },
        "nodes": {
            "template": (
                "[cyan]{name}[/cyan] "
                "state=[green]{state}[/green] "
                "cpus={cpus} mem={real_memory} gres={gres}"
            )
        },
        "reservations": {
            "template": (
                "[cyan bold]{name}[/cyan bold] "
                "{start_time} -> {end_time} "
                "users=[hot_pink]{users}[/hot_pink]"
            )
        },
        "coordinators": {
            "template": "[cyan]{account}[/cyan]: [green]{name}[/green]"
        },
        "users": {
            "template": "[cyan]{name}[/cyan] ({default_account})"
        },
        "jobs": {
            "template": (
                "[cyan bold]{job_id}[/cyan bold] "
                "[white]{name}[/white] "
                "user=[blue]{user_name}[/blue] "
                "state=[yellow]{job_state}[/yellow] "
                "end=[dim]{endlimit}[/dim] "
                "nodes={node_count}"
            )
        },
    },
    "detailed": {
        "accounts": {
            "template": (
                "[bold cyan]{name}[/bold cyan]\\n"
                "  Description: {description}\\n"
                "  Organization: [green]{organization}[/green]\\n"
                "  Coordinators: [yellow]{coordinators}[/yellow]"
            )
        },
        "reservations": {
            "template": (
                "[bold cyan]{name}[/bold cyan]\\n"
                "  Time: {start_time} → {end_time}\\n"
                "  Nodes: {node_list} ({node_count})\\n"
                "  Users: [hot_pink]{users}[/hot_pink]\\n"
                "  Accounts: [green]{accounts}[/green]"
            )
        },
        "jobs": {
            "template": (
                "[bold cyan]{job_id}[/bold cyan] - {name}\\n"
                "  User: [blue]{user_name}[/blue] "
                "Account: [green]{account}[/green]\\n"
                "  State: [yellow]{job_state}[/yellow] "
                "Partition: [magenta]{partition}[/magenta]\\n"
                "  Nodes: {node_count} ({nodes}) "
                "GRES: [magenta]{gres}[/magenta]\\n"
                "  Start: {start_time} End/Limit: {endlimit}\\n"
                "  Reason: {reason}"
            )
        },
    },
}


class ProfileManager:
    """Manages loading and parsing of output profiles."""

    def __init__(self):
        self._profiles: Dict[str, Dict[str, Any]] = {}
        self._loaded = False

    def _load_profiles(self) -> None:
        """Load profiles from all profile files."""
        if self._loaded:
            return

        # Start with default profiles
        self._profiles = dict(DEFAULT_PROFILES)

        # Load from profile files
        for filepath in PROFILE_FILES:
            if os.path.exists(filepath):
                try:
                    file_profiles = self._parse_profile_file(filepath)
                    self._merge_profiles(file_profiles)
                except Exception as e:
                    # Silently ignore parse errors in profile files
                    import sys

                    print(
                        f"Warning: Error parsing profile file {filepath}: {e}",
                        file=sys.stderr,
                    )

        self._loaded = True

    def _parse_profile_file(
        self, filepath: str
    ) -> Dict[str, Dict[str, Any]]:
        """Parse a profile file.

        Format:
        ```
        [profile:name]
        resource.columns = col1,col2,col3
        resource.styles.field = style
        resource.template = [cyan]{name}[/] - {description}

        # Multi-line templates with backslash continuation:
        resource.template = [cyan]{name}[/] \\
            Time: {start_time} \\
            Users: {users}
        ```
        """
        profiles: Dict[str, Dict[str, Any]] = {}
        current_profile: Optional[str] = None

        with open(filepath, "r") as f:
            lines = f.readlines()

        # Process lines with continuation support
        i = 0
        while i < len(lines):
            line = lines[i].rstrip("\n\r")

            # Handle line continuation (backslash at end)
            while line.rstrip().endswith("\\") and i + 1 < len(lines):
                # Remove trailing backslash and append next line
                line = line.rstrip()[:-1]
                i += 1
                next_line = lines[i].rstrip("\n\r")
                # Preserve some indentation as space
                line += next_line.lstrip()

            line = line.strip()
            i += 1

            # Skip empty lines and comments
            if not line or line.startswith("#"):
                continue

            # Profile header
            if line.startswith("[profile:") and line.endswith("]"):
                current_profile = line[9:-1].strip()
                if current_profile not in profiles:
                    profiles[current_profile] = {}
                continue

            # Setting line: resource.key = value
            if "=" in line and current_profile:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()

                self._set_nested_value(
                    profiles[current_profile], key, value
                )

        return profiles

    def _set_nested_value(
        self, target: Dict[str, Any], key: str, value: str
    ) -> None:
        """Set a nested value in a dictionary.

        Key format: resource.columns, resource.styles.field,
                    or resource.template
        """
        parts = key.split(".")
        current = target

        for i, part in enumerate(parts[:-1]):
            if part not in current:
                current[part] = {}
            current = current[part]

        final_key = parts[-1]

        # Parse value based on key type
        if final_key == "columns":
            if value == "*":
                current[final_key] = "*"
            else:
                current[final_key] = [
                    v.strip() for v in value.split(",")
                ]
        elif final_key == "template":
            # Keep template as-is, but convert escaped newlines
            current[final_key] = value
        else:
            current[final_key] = value

    def _merge_profiles(
        self, new_profiles: Dict[str, Dict[str, Any]]
    ) -> None:
        """Merge new profiles into existing profiles."""
        for name, profile in new_profiles.items():
            if name in self._profiles:
                self._deep_merge(self._profiles[name], profile)
            else:
                self._profiles[name] = profile

    def _deep_merge(
        self, base: Dict[str, Any], override: Dict[str, Any]
    ) -> None:
        """Deep merge override into base."""
        for key, value in override.items():
            if (
                key in base
                and isinstance(base[key], dict)
                and isinstance(value, dict)
            ):
                self._deep_merge(base[key], value)
            else:
                base[key] = value

    def get_profile(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a profile by name."""
        self._load_profiles()
        return self._profiles.get(name)

    def get_resource_config(
        self, profile_name: str, resource: str
    ) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific resource from a profile."""
        profile = self.get_profile(profile_name)
        if profile:
            return profile.get(resource)
        return None

    def list_profiles(self) -> List[str]:
        """List all available profile names."""
        self._load_profiles()
        return list(self._profiles.keys())

    def parse_profile_string(
        self, profile_str: str
    ) -> Dict[str, Dict[str, Any]]:
        """Parse an inline profile string.

        Format: resource.columns=col1,col2;resource.template=[cyan]{name}[/]

        Note: Only splits on ';' when followed by a resource.key= pattern.
        This allows templates to contain ';' characters.
        """
        profile: Dict[str, Any] = {}

        # Smart split: only split on ';' followed by 'word.word='
        # This preserves ';' inside template strings
        parts = []
        current = ""
        i = 0
        while i < len(profile_str):
            if profile_str[i] == ";":
                # Look ahead to see if this looks like a new setting
                rest = profile_str[(i + 1) :].lstrip()
                # Check if rest starts with word.word= pattern
                if re.match(r"^\w+\.\w+=", rest):
                    # This is a separator between settings
                    if current.strip():
                        parts.append(current.strip())
                    current = ""
                    i += 1
                    continue
            current += profile_str[i]
            i += 1

        if current.strip():
            parts.append(current.strip())

        for part in parts:
            if "=" in part:
                key, value = part.split("=", 1)
                self._set_nested_value(
                    profile, key.strip(), value.strip()
                )

        return profile


# Global profile manager instance
_profile_manager: Optional[ProfileManager] = None


def get_profile_manager() -> ProfileManager:
    """Get the global profile manager instance."""
    global _profile_manager
    if _profile_manager is None:
        _profile_manager = ProfileManager()
    return _profile_manager


def parse_columns_with_sort(
    columns: Union[List[str], str, None]
) -> Tuple[Optional[Union[List[str], str]], Optional[str], bool]:
    """Parse column list and extract sort field if present.

    Columns can have + or - suffix to indicate sort order:
      - field+ means sort ascending by field
      - field- means sort descending by field
    Only the first field with a sort marker is used for sorting.

    Args:
        columns: Column list, "*", or None

    Returns:
        Tuple of (clean_columns, sort_field, sort_ascending)
        - clean_columns: columns with sort markers removed
        - sort_field: first field marked for sorting (or None)
        - sort_ascending: True for +, False for -
    """
    if columns is None or columns == "*":
        return columns, None, True

    if isinstance(columns, str):
        columns = [c.strip() for c in columns.split(",")]

    clean_columns = []
    sort_field = None
    sort_ascending = True

    for col in columns:
        col = col.strip()
        if col.endswith("+"):
            clean_col = col[:-1]
            if sort_field is None:
                sort_field = clean_col
                sort_ascending = True
            clean_columns.append(clean_col)
        elif col.endswith("-"):
            clean_col = col[:-1]
            if sort_field is None:
                sort_field = clean_col
                sort_ascending = False
            clean_columns.append(clean_col)
        else:
            clean_columns.append(col)

    return clean_columns, sort_field, sort_ascending


def get_columns_for_resource(
    profile_name: str,
    resource: str,
    profile_str: Optional[str] = None,
) -> Optional[Union[List[str], str]]:
    """Get column configuration for a resource.

    Args:
        profile_name: Name of the profile to use
        resource: Resource type (accounts, qos, etc.)
        profile_str: Optional inline profile string (takes precedence)

    Returns:
        List of column names, "*" for all columns, or None if not specified
    """
    manager = get_profile_manager()

    # Check inline profile string first
    if profile_str:
        inline_profile = manager.parse_profile_string(profile_str)
        if resource in inline_profile:
            columns = inline_profile[resource].get("columns")
            if columns:
                return columns

    # Fall back to named profile
    config = manager.get_resource_config(profile_name, resource)
    if config:
        return config.get("columns")

    return None


def get_styles_for_resource(
    profile_name: str,
    resource: str,
    profile_str: Optional[str] = None,
) -> Dict[str, str]:
    """Get style configuration for a resource.

    Args:
        profile_name: Name of the profile to use
        resource: Resource type (accounts, qos, etc.)
        profile_str: Optional inline profile string (takes precedence)

    Returns:
        Dictionary mapping field names to style strings
    """
    manager = get_profile_manager()
    styles: Dict[str, str] = {}

    # Get styles from named profile first
    config = manager.get_resource_config(profile_name, resource)
    if config:
        styles.update(config.get("styles", {}))

    # Override with inline profile string
    if profile_str:
        inline_profile = manager.parse_profile_string(profile_str)
        if resource in inline_profile:
            inline_styles = inline_profile[resource].get("styles", {})
            styles.update(inline_styles)

    return styles


def get_template_for_resource(
    profile_name: str,
    resource: str,
    profile_str: Optional[str] = None,
) -> Optional[str]:
    """Get template string for a resource.

    Args:
        profile_name: Name of the profile to use
        resource: Resource type (accounts, qos, etc.)
        profile_str: Optional inline profile string (takes precedence)

    Returns:
        Template string or None if not specified
    """
    manager = get_profile_manager()

    # Check inline profile string first
    if profile_str:
        inline_profile = manager.parse_profile_string(profile_str)
        if resource in inline_profile:
            template = inline_profile[resource].get("template")
            if template:
                return template

    # Fall back to named profile
    config = manager.get_resource_config(profile_name, resource)
    if config:
        return config.get("template")

    return None


def _normalize_profile_str(
    profile_str: Optional[str], resource: str
) -> Optional[str]:
    """Normalize profile string, adding resource prefix if missing.

    Supports shorthand formats:
    - "name,organization" -> "resource.columns=name,organization"
    - "[cyan]{name}[/]" -> "resource.template=[cyan]{name}[/]"

    Args:
        profile_str: Raw profile string
        resource: Current resource type

    Returns:
        Normalized profile string with proper resource prefix
    """
    if not profile_str:
        return None

    # Check if it's already in proper format (has resource.key= pattern)
    # Look for pattern like "resource.columns=" or "resource.template="
    if (
        "." in profile_str.split("=")[0]
        if "=" in profile_str
        else False
    ):
        return profile_str

    # Check if it starts with "columns=" or "template=" or "styles="
    if profile_str.startswith(("columns=", "template=", "styles=")):
        return f"{resource}.{profile_str}"

    # Check if it looks like a column list (comma-separated words,
    # no template markers like { [ or =)
    if (
        "," in profile_str
        and "{" not in profile_str
        and "[" not in profile_str
        and "=" not in profile_str
    ):
        # Treat as column list
        return f"{resource}.columns={profile_str}"

    # Check if it's a single word without template markers (single column)
    if (
        "{" not in profile_str
        and "[" not in profile_str
        and "=" not in profile_str
        and " " not in profile_str
    ):
        # Treat as single column
        return f"{resource}.columns={profile_str}"

    # No resource prefix - treat as raw template for current resource
    return f"{resource}.template={profile_str}"


def get_profile_config(
    profile_name: str,
    resource: str,
    profile_str: Optional[str] = None,
) -> Tuple[
    Optional[Union[List[str], str]],
    Dict[str, str],
    Optional[str],
    Optional[str],
    bool,
]:
    """Get full configuration for a resource.

    Args:
        profile_name: Name of the profile to use
        resource: Resource type (accounts, qos, etc.)
        profile_str: Optional inline profile string (takes precedence).
                     If no 'resource.' prefix, treated as template for
                     current resource.

    Returns:
        Tuple of (columns, styles, template, sort_field, sort_ascending)
        - columns may be a list, "*", or None (with sort markers removed)
        - styles is a dict mapping field names to style strings
        - template is a string template or None
        - sort_field is the field to sort by (or None)
        - sort_ascending is True for ascending, False for descending
    """
    # Normalize profile_str - add resource prefix if missing
    normalized_str = _normalize_profile_str(profile_str, resource)

    columns = get_columns_for_resource(
        profile_name, resource, normalized_str
    )

    # Parse columns for sort info
    columns, sort_field, sort_ascending = parse_columns_with_sort(
        columns
    )

    styles = get_styles_for_resource(
        profile_name, resource, normalized_str
    )
    template = get_template_for_resource(
        profile_name, resource, normalized_str
    )
    return columns, styles, template, sort_field, sort_ascending


# Default values for fields (field is "empty" if it equals default)
DEFAULT_FIELD_VALUES: Dict[str, Dict[str, Any]] = {
    "reservations": {
        "accounts": "",
        "users": "",
        "partition": "",
        "flags": "",
        "tres": "",
    },
    "accounts": {
        "coordinators": [],
        "description": "",
        "organization": "",
    },
    "qos": {
        "description": "",
        "flags": [],
        "preempt_list": [],
    },
    "nodes": {
        "reason": "",
        "comment": "",
    },
    "partitions": {
        "allow_accounts": "ALL",
        "deny_accounts": "",
        "allow_qos": "ALL",
        "deny_qos": "",
    },
}


def is_field_empty(
    field: str,
    value: Any,
    resource: Optional[str] = None,
) -> bool:
    """Check if a field value should be considered empty.

    A field is empty if:
    - Value is None
    - Value is an empty string
    - Value is an empty list
    - Value equals the default value for that field/resource
    - Value is "-"

    Args:
        field: Field name
        value: Field value
        resource: Optional resource type for default value lookup

    Returns:
        True if field should be considered empty
    """
    if value is None:
        return True
    if value == "":
        return True
    if value == "-":
        return True
    if isinstance(value, list) and len(value) == 0:
        return True
    if isinstance(value, dict):
        # Handle set/number pattern - empty if not set
        if "set" in value and not value.get("set"):
            return True

    # Check against default values
    if resource and resource in DEFAULT_FIELD_VALUES:
        defaults = DEFAULT_FIELD_VALUES[resource]
        if field in defaults and value == defaults[field]:
            return True

    return False


def format_with_template(
    template: str,
    data: Dict[str, Any],
    value_formatter: Optional[Callable[[str, Any], str]] = None,
    resource: Optional[str] = None,
) -> str:
    """Format data using a template string.

    Args:
        template: Template string with {field} placeholders
        data: Dictionary of field values
        value_formatter: Optional function to format values
        resource: Optional resource type for default value lookup

    Template syntax:
        {field}           - replaced with field value
        {?field TEXT}     - show TEXT only if field is not empty
                            TEXT can contain {field} placeholders

    Returns:
        Formatted string with Rich markup
    """
    # Convert escaped newlines to actual newlines
    result = template.replace("\\n", "\n")

    # First, process conditional blocks {?field TEXT}
    # Pattern matches {?field_name any text including {field} until }
    # We need to handle nested braces carefully
    conditional_pattern = re.compile(
        r"\{\?(\w+)\s+([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}"
    )

    def replace_conditional(match: re.Match) -> str:
        field = match.group(1)
        content = match.group(2)
        value = data.get(field)

        # Check if field is empty
        if is_field_empty(field, value, resource):
            return ""

        # Field is not empty, return the content (will be processed later)
        return content

    result = conditional_pattern.sub(replace_conditional, result)

    # Now process regular {field} placeholders
    field_pattern = re.compile(r"\{(\w+)\}")

    def replace_field(match: re.Match) -> str:
        field = match.group(1)
        value = data.get(field)

        if value is None:
            return "-"

        # Format value
        if value_formatter:
            return value_formatter(field, value)

        # Handle common types
        if isinstance(value, list):
            return ", ".join(str(v) for v in value) if value else "-"
        elif isinstance(value, dict):
            # Handle set/number pattern
            if value.get("set"):
                return str(value.get("number", "-"))
            elif value.get("infinite"):
                return "∞"
            return str(value)

        return str(value) if value != "" else "-"

    return field_pattern.sub(replace_field, result)


def extract_fields_from_template(template: str) -> List[str]:
    """Extract field names from a template string.

    Args:
        template: Template string with {field} placeholders

    Returns:
        List of field names found in the template
    """
    # Match both regular {field} and conditional {?field ...}
    pattern = re.compile(r"\{(\w+)\}|\{\?(\w+)\s+")
    matches = pattern.findall(template)
    # Flatten and filter empty strings
    return [m[0] or m[1] for m in matches if m[0] or m[1]]


def _get_resource_fields() -> Dict[str, Dict[str, str]]:
    """Build RESOURCE_FIELDS from resource classes.

    Lazily imports resource classes to avoid circular imports.
    """
    # Import here to avoid circular imports
    from .accounts import Account
    from .associations import Association
    from .coordinators import Coordinator
    from .events import Event
    from .jobs import Job
    from .nodes import Node
    from .partitions import Partition
    from .qos import Qos
    from .reservations import Reservation
    from .users import User

    return {
        "accounts": Account.get_profile_fields(),
        "associations": Association.get_profile_fields(),
        "coordinators": Coordinator.get_profile_fields(),
        "events": Event.get_profile_fields(),
        "jobs": Job.get_profile_fields(),
        "nodes": Node.get_profile_fields(),
        "partitions": Partition.get_profile_fields(),
        "qos": Qos.get_profile_fields(),
        "reservations": Reservation.get_profile_fields(),
        "users": User.get_profile_fields(),
    }


# Available fields for each resource type (for --profile-str=help)
# Lazily initialized to avoid circular imports
_RESOURCE_FIELDS: Optional[Dict[str, Dict[str, str]]] = None


def get_resource_fields() -> Dict[str, Dict[str, str]]:
    """Get available fields for each resource type."""
    global _RESOURCE_FIELDS
    if _RESOURCE_FIELDS is None:
        _RESOURCE_FIELDS = _get_resource_fields()
    return _RESOURCE_FIELDS


def show_profile_help(resource: str) -> bool:
    """Show available fields for a resource.

    Args:
        resource: Resource type name (can be short form like 'res')

    Returns:
        True if help was shown, False otherwise
    """
    # Map short resource names to full names
    resource_map = {
        "res": "reservations",
        "acc": "accounts",
        "assoc": "associations",
        "part": "partitions",
        "node": "nodes",
        "user": "users",
        "coord": "coordinators",
        "conf": "config",
        "job": "jobs",
        "event": "events",
    }

    # Try to match by prefix
    full_resource = resource
    for prefix, full_name in resource_map.items():
        if resource.startswith(prefix):
            full_resource = full_name
            break

    resource_fields = get_resource_fields()
    if full_resource not in resource_fields:
        print(f"No field documentation for resource: {resource}")
        print(
            f"Available resources: {', '.join(resource_fields.keys())}"
        )
        return True

    fields = resource_fields[full_resource]
    print(f"\nAvailable fields for '{full_resource}':\n")
    print("  Field                      Description")
    print("  " + "-" * 55)
    for field, desc in sorted(fields.items()):
        print(f"  {field:<24}  {desc}")
    print()
    print("Template syntax:")
    print("  {field}           - Show field value")
    print("  {?field TEXT}     - Show TEXT only if field is not empty")
    print("  [color]...[/]     - Rich markup for colors")
    print("  \\n                - Newline")
    print()
    print("Example:")
    print('  --profile-str "[cyan]{name}[/] - description"')
    print()
    return True


def is_profile_help(profile_str: Optional[str]) -> bool:
    """Check if profile_str is a help request."""
    return profile_str is not None and profile_str.lower() == "help"


def show_all_profile_fields() -> None:
    """Show available fields for all resources."""
    resource_fields = get_resource_fields()

    print("\nAvailable profile fields by resource:\n")
    print("=" * 70)

    for resource in sorted(resource_fields.keys()):
        fields = resource_fields[resource]
        print(f"\n[{resource}]")
        print("-" * 40)
        for field, desc in sorted(fields.items()):
            print(f"  {field:<24}  {desc}")

    print("\n" + "=" * 70)
    print("\nSorting:")
    print("  field+              - Sort ascending by field")
    print("  field-              - Sort descending by field")
    print("\nTemplate syntax:")
    print("  {field}             - Show field value")
    print(
        "  {?field TEXT}       - Show TEXT only if field is not empty"
    )
    print("  [color]...[/]       - Rich markup for colors")
    print("  \\n                  - Newline")
    print("\nExample:")
    print('  --profile-str "name+,description"')
    print('  --profile-str "[cyan]{name}[/] - {description}"')
    print()


def sort_data(
    data: List[Dict[str, Any]],
    sort_field: Optional[str],
    ascending: bool = True,
) -> List[Dict[str, Any]]:
    """Sort a list of dictionaries by a field.

    Handles mixed types (strings, numbers, None) gracefully.

    Args:
        data: List of dictionaries to sort
        sort_field: Field name to sort by (None for no sorting)
        ascending: True for ascending, False for descending

    Returns:
        Sorted list (or original if sort_field is None)
    """
    if not sort_field or not data:
        return data

    def sort_key(item: Dict[str, Any]) -> Any:
        value = item.get(sort_field)
        # Handle None values - sort them last
        if value is None or value == "-" or value == "":
            return (1, "")
        # Try to convert to number for proper numeric sorting
        try:
            return (0, float(value))
        except (ValueError, TypeError):
            # Fall back to string comparison
            return (0, str(value).lower())

    return sorted(data, key=sort_key, reverse=not ascending)


def sort_hierarchical_data(
    data: List[Dict[str, Any]],
    sort_field: Optional[str],
    ascending: bool = True,
    depth_key: str = "_depth",
    parent_key: str = "parent_account",
    id_key: str = "account",
) -> List[Dict[str, Any]]:
    """Sort hierarchical data, preserving parent-child relationships.

    Within each hierarchy level, items are sorted independently.

    Args:
        data: List of dictionaries with hierarchy info
        sort_field: Field name to sort by (None for no sorting)
        ascending: True for ascending, False for descending
        depth_key: Key that stores the depth level
        parent_key: Key that stores the parent reference
        id_key: Key that stores the item's identifier

    Returns:
        Hierarchically sorted list
    """
    if not sort_field or not data:
        return data

    # Check if data has depth info (already structured hierarchically)
    if depth_key in data[0]:
        # Data is already structured with depth - need to sort within groups
        return _sort_with_depth(
            data, sort_field, ascending, depth_key, parent_key, id_key
        )

    # Simple flat sort
    return sort_data(data, sort_field, ascending)


def _sort_with_depth(
    data: List[Dict[str, Any]],
    sort_field: str,
    ascending: bool,
    depth_key: str,
    parent_key: str,
    id_key: str,
) -> List[Dict[str, Any]]:
    """Sort data that already has depth information.

    Args:
        data: List of dicts with depth info
        sort_field: Field to sort by
        ascending: Sort direction
        depth_key: Key for depth level
        parent_key: Key for parent reference
        id_key: Key for item identifier

    Returns:
        Sorted list preserving hierarchy
    """
    # Build a map of parent -> children
    from collections import defaultdict

    parent_children: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    roots: List[Dict[str, Any]] = []

    for item in data:
        # Use _parent_id if available (for user associations), else parent_key
        parent = item.get("_parent_id") or item.get(parent_key, "")
        depth = item.get(depth_key, 0)
        if depth == 0 or not parent:
            roots.append(item)
        else:
            parent_children[parent].append(item)

    def sort_key(item: Dict[str, Any]) -> Any:
        # Account associations (with _is_account=True or empty user) come first
        is_account = item.get("_is_account", not item.get("user"))
        value = item.get(sort_field)
        if value is None or value == "-" or value == "":
            # Empty values: accounts first (0), then sorted to end (1)
            return (0 if is_account else 1, 1, "")
        try:
            return (0 if is_account else 1, 0, float(value))
        except (ValueError, TypeError):
            return (0 if is_account else 1, 0, str(value).lower())

    def add_sorted_subtree(
        items: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        result = []
        sorted_items = sorted(
            items, key=sort_key, reverse=not ascending
        )
        for item in sorted_items:
            result.append(item)
            # Only account items can have children (not user items)
            is_account = item.get("_is_account", not item.get("user"))
            if is_account:
                item_id = item.get(id_key, "")
                if item_id in parent_children:
                    result.extend(
                        add_sorted_subtree(parent_children[item_id])
                    )
        return result

    return add_sorted_subtree(roots)
