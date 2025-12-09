"""Base class for Slurm resource management."""

import re
from typing import Any, Dict

from rich.markup import escape

from .resources import Resource
from .utils import console


class BaseSlurmResource:
    """Base class for all Slurm resources."""

    _WIDTH = None
    _TIME_PATTERNS = [
        # YYYY-MM-DD[THH:MM[:SS]]
        re.compile(
            r"^(?P<date>\d{4}-\d{2}-\d{2})(?:[T ](?P<h>\d{1,2}):"
            r"(?P<m>\d{1,2})(?::(?P<s>\d{1,2}))?)?$"
        ),
        # [D-]HH:MM:SS (e.g., 2-12:30:00)
        re.compile(
            r"^(?:(?P<days>\d+)-)?(?P<h>\d{1,2}):(?P<m>\d{1,2}):"
            r"(?P<s>\d{1,2})$"
        ),
        # HH:MM:SS
        re.compile(r"^(?P<h>\d{1,2}):(?P<m>\d{1,2}):(?P<s>\d{1,2})$"),
        # MMDDYY
        re.compile(r"^(?P<month>\d{2})(?P<day>\d{2})(?P<year>\d{2})$"),
        # MM/DD/YY
        re.compile(
            r"^(?P<month>\d{2})/(?P<day>\d{2})/(?P<year>\d{2})$"
        ),
        # MM.DD.YY
        re.compile(
            r"^(?P<month>\d{2})\.(?P<day>\d{2})\.(?P<year>\d{2})$"
        ),
    ]

    # Subclasses should define their valid_args
    valid_args: Dict[str, Dict[str, str]] = {}

    @classmethod
    def get_profile_fields(cls) -> Dict[str, str]:
        """Return field names and descriptions for profile templates.

        Subclasses should override this to provide their specific fields.
        """
        return {}

    @classmethod
    def _check_args(
        cls,
        kwargs: Any,
        set: Dict[str, Any],
        add: Dict[str, Any],
        delete: Dict[str, Any],
    ) -> bool:
        """Check if the arguments are valid."""
        for key, value in kwargs.items():
            arg_type = None
            if key[-1] == "+":
                key = key[:-1]
                arg_type = "add"
            elif key[-1] == "-":
                key = key[:-1]
                arg_type = "delete"

            # Try to match key as a prefix of exactly one valid_args key
            matches = [
                k for k in cls.valid_args.keys() if k.startswith(key)
            ]
            if len(matches) == 1:
                full_key = matches[0]
            elif key not in cls.valid_args.keys():
                console.print(f"Invalid argument: {key}!")
                return False
            elif len(matches) > 1:
                console.print(
                    f"Ambiguous argument: {key}. Matches: {', '.join(matches)}"
                )
                return False
            key_type = cls.valid_args[full_key]["type"]
            if key_type == "int":
                try:
                    set[full_key] = int(value)
                except ValueError:
                    console.print(
                        f"Invalid integer argument: {full_key}={value}"
                    )
                    return False
            elif key_type == "list":
                set[full_key] = value.split(",")
            elif key_type == "memory":
                try:
                    if value.endswith("M"):
                        set[full_key] = int(value.rstrip("M")) * 1024
                    elif value.endswith("G"):
                        set[full_key] = (
                            int(value.rstrip("G")) * 1024 * 1024
                        )
                    else:
                        console.print(
                            f"Invalid memory argument: {full_key}={value}"
                        )
                        return False
                except ValueError:
                    console.print(
                        f"Invalid memory argument: {full_key}={value}"
                    )
                    return False
            elif key_type == "time":
                try:
                    set[full_key] = cls._parse_time_value(value)
                except Exception:
                    console.print(
                        f"Invalid time argument: {full_key}={value}"
                    )
                    return False
            elif key_type[0] == "[" and key_type[-1] == "]":
                if value.lower() not in key_type[1:-1].split(","):
                    console.print(
                        f"Invalid list argument: {full_key}={value}."
                        " Valid values are: "
                        f"{', '.join(key_type[1:-1].split(','))}"
                    )
                    return False
                set[full_key] = value.lower()
            # qos, partition, account, group, qos
            elif key_type in ["qos", "partition", "account", "group"]:
                value = value.lower()
                # TODO: Check if the value is a valid qos, partition,
                # account, or group
            elif key_type == "nodes":
                node_list = cls.expand_nodenames(value)
                all_nodes = Resource.cached_resource_list("nodes")
                for node in node_list:
                    if node not in all_nodes:
                        console.print(
                            f"Invalid nodes argument: {full_key}={value}. "
                            f"Node {node} not found."
                        )
                        return False
                set[full_key] = value
            else:
                console.print(
                    f"Invalid argument: {full_key}={value}. "
                    f"{key_type} not found"
                )
                return False
            if arg_type:
                if arg_type == "add":
                    add[full_key] = value
                elif arg_type == "delete":
                    delete[full_key] = value
            else:
                set[full_key] = value
        return True

    @classmethod
    def _parse_time_value(cls, val):
        """Parse time values in various formats."""
        # Try to parse as integer seconds
        try:
            return int(val)
        except ValueError:
            pass

        # Accepts:
        #   - now+count time-units
        #   - tomorrow
        #   - HH:MM:SS
        #   - MMDDYY
        #   - MM/DD/YY
        #   - MM.DD.YY
        #   - YYYY-MM-DD[THH:MM[:SS]]
        #   - [D-]HH:MM:SS (e.g., 2-12:30:00)
        if val.startswith("now"):
            return val
        elif val.startswith("tomorrow"):
            return val

        m = None
        for time_pattern in cls._TIME_PATTERNS:
            m = time_pattern.match(val)
            if m:
                break
        if not m:
            raise ValueError("Invalid time format")

        date = m.group("date") if "date" in m.groupdict() else None
        days = int(m.group("days")) if "days" in m.groupdict() else 0
        hh = int(m.group("h")) if "h" in m.groupdict() else 0
        mm = int(m.group("m")) if "m" in m.groupdict() else 0
        ss = int(m.group("s")) if "s" in m.groupdict() else 0

        total_seconds = days * 86400 + hh * 3600 + mm * 60 + ss

        if date:
            # If date is present, return a datetime object
            return f"{date}T{hh:02d}:{mm:02d}:{ss:02d}"
        else:
            # Otherwise, return total seconds as int
            return total_seconds

    @classmethod
    def max_width(cls) -> int:
        """Get the maximum width of the console."""
        if cls._WIDTH is None:
            cls._WIDTH = console.width
        return cls._WIDTH

    @classmethod
    def print_dict_pretty(cls, data: dict) -> bool:
        """Print a dictionary in a pretty format."""
        line_len = 2
        something_was_printed = False
        console.print("  ", end="")
        for k in sorted(data.keys()):
            value = data[k]
            if isinstance(value, list):
                if len(value) == 0:
                    continue
                value = ",".join(value)
            else:
                value = str(value)
                if str(value) == "":
                    continue
            line_len += len(k) + len(value) + 2
            if line_len > cls.max_width():
                console.print("\n  ", end="")
                line_len = 0
            console.print(f"[label]{k}[/]: [str]{value}[/]", end=" ")
            if len(k) + len(value) + 2 > cls.max_width():
                console.print("\n  ", end="")
                line_len = 0
            something_was_printed = True
        if something_was_printed:
            console.print()
        return something_was_printed

    @classmethod
    def print_dict_pretty_def(
        cls, data: dict, value_types: dict
    ) -> bool:
        """Print a dictionary skipping the default values
        in a pretty format."""
        line_len = 2
        something_was_printed = False
        width = cls.max_width()
        for key in sorted(data.keys()):
            value = data[key]
            if key in value_types:
                if value == value_types[key]["def"]:
                    continue
                line_len += len(key) + len(value) + 2
                if line_len > width:
                    console.print("\n  ", end="")
                    line_len = 0
                style = (
                    "allow"
                    if re.match(r"allow", key)
                    else (
                        "deny"
                        if re.match(r"deny", key)
                        else ("qos" if re.match(r"qos", key) else "str")
                    )
                )
                console.print(f"{key}: [{style}]{value}[/]", end=" ")
                something_was_printed = True
        if something_was_printed:
            console.print()
        return something_was_printed

    @classmethod
    def print_dict_pretty_flags_def(
        cls,
        data: dict,
        value_types: dict,
    ) -> bool:
        """Print a dictionary skipping the default values
        in a pretty format."""
        line_len = 2
        something_was_printed = False
        width = cls.max_width()
        console.print("  ", end="")
        for key in sorted(data.keys()):
            value = data[key]
            if key in value_types:
                if value == value_types[key]["def"]:
                    continue
                line_len += len(key) + len(value) + 1
                if line_len > width:
                    console.print("\n  ", end="")
                    line_len = 0
                if value == "YES":
                    console.print(f"[green]{escape(key)}[/]", end=" ")
                else:
                    console.print(f"[red]{escape(key)}[/]", end=" ")
                something_was_printed = True
        if something_was_printed:
            console.print()
        return something_was_printed

    @classmethod
    def expand_nodenames(cls, pattern: str) -> list:
        """
        Expand a Slurm-style node name pattern like "node[01,03,10-12]"
        into a list of node names.

        Example:
            "node[01,03,10-12]" ->
            ["node01","node03","node10","node11","node12"]
        """

        # Match prefix and bracketed part
        m = re.match(r"^(.*)\[(.+)\]$", pattern)
        if not m:
            # No brackets, return as single node
            return [pattern]

        prefix = m.group(1)
        inside = m.group(2)
        result = []

        # Split by comma, handle ranges and single values
        for part in inside.split(","):
            if "-" in part:
                start, end = part.split("-", 1)
                # Preserve leading zeros
                width = max(len(start), len(end))
                for i in range(int(start), int(end) + 1):
                    node = f"{prefix}{str(i).zfill(width)}"
                    result.append(node)
            else:
                node = f"{prefix}{part}"
                result.append(node)
        return result
