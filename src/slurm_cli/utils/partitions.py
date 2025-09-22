"""Utilities for managing partitions."""

import re
import subprocess
from typing import Any

from .utils import console


class Partition:

    valid_args = {
        "allowaccounts": {
            "type": "list",
            "help": "Comma-separated list of accounts"
            "that are allowed to use this partition",
        },
        "allowgroups": {
            "type": "list",
            "help": "Comma-separated list of groups"
            "that are allowed to use this partition",
        },
        "allowqos": {
            "type": "list",
            "help": "Comma-separated list of QOSs"
            "that are allowed to use this partition",
        },
        "alternate": {
            "type": "partition",
            "help": "Alternate partition to be used if the "
            'state of this partition is "DRAIN" or "INACTIVE."',
        },
        "cpubind": {
            "type": "[none, socket, ldom, core, thread, off]",
            "help": "Specify the task binding mode to be used by"
            " default for this partition",
        },
        "default": {
            "type": "[yes, no, y, n, 1, 0]",
            "help": "Specify if this partition is to be used by jobs"
            "which do not explicitly identify a partition to use",
        },
        "defaulttime": {
            "type": "time",
            "help": "Run time limit used for jobs that don't specify a value",
        },
        "defmempercpu": {
            "type": "memory",
            "help": "Set the default memory to be allocated per CPU"
            "for jobs in this partition",
        },
        "defmempernode": {
            "type": "memory",
            "help": "Set the default memory to be allocated per node"
            "for jobs in this partition",
        },
        "denyaccounts": {
            "type": "list",
            "help": "Identify the Accounts which should be denied access"
            "to this partition",
        },
        "denyqos": {
            "type": "list",
            "help": "Identify the QOSs which should be denied access"
            "to this partition",
        },
        "disablerootjobs": {
            "type": "[yes, no, y, n, 1, 0]",
            "help": "Specify if jobs can be executed as user root",
        },
        "exclusiveuser": {
            "type": "[yes, no, y, n, 1, 0]",
            "help": "Specify if nodes will be exclusively allocated to users",
        },
        "gracetime": {
            "type": "time",
            "help": "Specify the preemption grace time to be extended to"
            " a job which has been selected for preemption",
        },
        "hidden": {
            "type": "[yes, no, y, n, 1, 0]",
            "help": "Specify if the partition and its jobs should be hidden"
            "from view",
        },
        "jobdefaults": {
            "type": "list",
            "help": "Specify job default values using a comma-delimited list"
            'of "key=value" pairs',
        },
        "lln": {
            "type": "[yes, no, y, n, 1, 0]",
            "help": "Schedule jobs on the least loaded nodes "
            "(based on the number of idle CPUs)",
        },
        "maxcpuspersocket": {
            "type": "int",
            "help": "Set the maximum number of CPUs that can be allocated per"
            " socket to all jobs in this partition",
        },
        "maxmempercpu": {
            "type": "memory",
            "help": "Set the maximum number of CPUs that can be allocated per"
            "CPU for jobs in this partition",
        },
        "maxmempernode": {
            "type": "memory",
            "help": "Set the maximum number of memory that can be allocated"
            " per node to all jobs in this partition",
        },
        "maxnodes": {
            "type": "int",
            "help": "Set the maximum number of nodes that can be allocated to"
            "all jobs in this partition",
        },
        "maxtime": {
            "type": "time",
            "help": "Set the maximum time limit for all jobs in"
            " this partition",
        },
        "minnodes": {
            "type": "int",
            "help": "Set the minimum number of nodes that can be allocated to"
            "all jobs in this partition",
        },
        "nodes": {
            "type": "list",
            "help": "Identify the node(s) to be associated with this"
            " partition",
        },
        "oversubscribe": {
            "type": "[yes, no, y, n, 1, 0]",
            "help": "Specify if compute resources (i.e. individual CPUs) in"
            " this partition can be shared by multiple jobs",
        },
        "overtimelimit": {
            "type": "int",
            "help": "Number of minutes by which a job can exceed its time "
            "limit before being canceled",
        },
        "powerdownonidle": {
            "type": "[yes, no, y, n, 1, 0]",
            "help": "If set to 'yes', then nodes allocated from this partition"
            " will immediately be requested to power down upon becoming IDLE",
        },
        "preemptmode": {
            "type": "[off, cancel, requeue, suspend]",
            "help": "Reset the mechanism used to preempt jobs in this"
            " partition",
        },
        "priority": {
            "type": "int",
            "help": "Jobs submitted to a higher priority partition will"
            " be dispatched before pending jobs in lower priority partitions",
        },
        "priorityjobfactor": {
            "type": "int",
            "help": "Partition factor used by priority/multifactor plugin in"
            " calculating job priority",
        },
        "prioritytier": {
            "type": "int",
            "help": "Jobs submitted to a partition with a higher priority tier"
            " value will be dispatched before pending jobs in partition with"
            " lower priority tier value",
        },
        "qos": {
            "type": "qos",
            "help": "Set the partition QOS with a QOS name or to remove the"
            " Partition QOS",
        },
        "reqresv": {
            "type": "[yes, no, y, n, 1, 0]",
            "help": "Specify if only allocation requests designating a"
            " reservation will be satisfied",
        },
        "rootonly": {
            "type": "[yes, no, y, n, 1, 0]",
            "help": "Specify if only allocation requests initiated by user"
            " root will be satisfied",
        },
        "tresbillingweights": {
            "type": "list",
            "help": "TRES Billing Weights",
        },
        "state": {
            "type": "[up, down, drain, inactive]",
            "help": "Partition state",
        },
    }

    def __init__(self, name: "str", **kwargs: Any):
        self.name = name
        self.kwargs = kwargs

    @classmethod
    def _check_args(
        cls,
        kwargs: Any,
        set: dict[str, Any],
        add: dict[str, Any],
        delete: dict[str, Any],
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

            if key not in cls.valid_args.keys():
                console.print(f"Invalid argument: {key}")
                return False
            key_type = cls.valid_args[key]["type"]
            if key_type == "int":
                try:
                    kwargs[key] = int(value)
                except ValueError:
                    console.print(
                        f"Invalid integer argument: {key}={value}"
                    )
                    return False
            elif key_type == "list":
                # kwargs[key] = value.split(",")
                pass
            elif key_type == "memory":
                try:
                    if value.endswith("M"):
                        kwargs[key] = int(value.rstrip("M")) * 1024
                    elif value.endswith("G"):
                        kwargs[key] = (
                            int(value.rstrip("G")) * 1024 * 1024
                        )
                    else:
                        console.print(
                            f"Invalid memory argument: {key}={value}"
                        )
                        return False
                except ValueError:
                    console.print(
                        f"Invalid memory argument: {key}={value}"
                    )
                    return False
            elif key_type == "time":
                try:
                    kwargs[key] = cls._parse_time_value(value)
                except Exception:
                    console.print(
                        f"Invalid time argument: {key}={value}"
                    )
                    return False
            elif key_type[0] == "[" and key_type[-1] == "]":
                if value.lower() not in key_type[1:-1].split(","):
                    console.print(
                        f"Invalid list argument: {key}={value}."
                        " Valid values are: "
                        f"{', '.join(key_type[1:-1].split(','))}"
                    )
                    return False
                kwargs[key] = value.lower()
            # qos, partition, account, group, qos
            elif key_type in ["qos", "partition", "account", "group"]:
                value = value.lower()
                # TODO: Check if the value is a valid qos, partition,
                # account, or group
            else:
                console.print(
                    f"Invalid argument: {key}={value}. {key_type} not found"
                )
                return False
            if arg_type:
                if arg_type == "add":
                    add[key] = value
                elif arg_type == "delete":
                    delete[key] = value
            else:
                set[key] = value
        return True

    @classmethod
    def _parse_time_value(cls, val):
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
        if val.startswith("now+"):
            return val
        elif val.startswith("tomorrow"):
            return val

        time_patterns = [
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
            re.compile(
                r"^(?P<h>\d{1,2}):(?P<m>\d{1,2}):(?P<s>\d{1,2})$"
            ),
            # MMDDYY
            re.compile(
                r"^(?P<month>\d{2})(?P<day>\d{2})(?P<year>\d{2})$"
            ),
            # MM/DD/YY
            re.compile(
                r"^(?P<month>\d{2})/(?P<day>\d{2})/(?P<year>\d{2})$"
            ),
            # MM.DD.YY
            re.compile(
                r"^(?P<month>\d{2})\.(?P<day>\d{2})\.(?P<year>\d{2})$"
            ),
        ]
        m = None
        for time_pattern in time_patterns:
            m = time_pattern.match(val)
            if m:
                break
        if not m:
            raise ValueError("Invalid time format")

        date = m.group("date")
        hh = m.group("h")
        mm = m.group("m")
        ss = m.group("s")

        # Fill in missing values
        hh = int(hh) if hh is not None else 0
        mm = int(mm) if mm is not None else 0
        ss = int(ss) if ss is not None else 0

        total_seconds = hh * 3600 + mm * 60 + ss

        if date:
            # If date is present, return a datetime object
            return f"{date}T{hh:02d}:{mm:02d}:{ss:02d}"
        else:
            # Otherwise, return total seconds as int
            return total_seconds

    @classmethod
    def create(
        cls, name: str, verbose: bool = False, **kwargs: Any
    ) -> None:
        """Create a new partition."""
        set = {}
        add = {}
        delete = {}
        if not cls._check_args(kwargs, set, add, delete):
            return
        options = " ".join(
            [f"{key}={value}" for key, value in set.items()]
        )
        if len(add) > 0:
            options += " "
            options += " ".join(
                [f"{key}+={value}" for key, value in add.items()]
            )
        if len(delete) > 0:
            options += " "
            options += " ".join(
                [f"{key}-={value}" for key, value in delete.items()]
            )
        # console.print(
        #     f"Creating partition: {name} with options: {options}"
        # )
        args = [
            "scontrol",
            "create",
            "partition",
            f"name={name}",
            options,
        ]

        try:
            result = subprocess.run(
                ["echo", *args],
                check=True,
                capture_output=True,
                text=True,
            )
            if result.stdout:
                console.print(result.stdout)
            if verbose:
                console.print(
                    f"[green]Partition '{name}' created successfully.[/green]"
                )

        except subprocess.CalledProcessError as e:
            console.print(
                f"[red]Failed to create partition '{name}':[/red]"
                f" {e.stderr or e}"
            )

    @classmethod
    def update(
        cls, name: str, verbose: bool = False, **kwargs: Any
    ) -> None:
        """Update a partition."""
        set = {}
        add = {}
        delete = {}
        if not cls._check_args(kwargs, set, add, delete):
            return
        options = " ".join(
            [f"{key}={value}" for key, value in set.items()]
        )
        if len(add) > 0:
            options += " "
            options += " ".join(
                [f"{key}+={value}" for key, value in add.items()]
            )
        if len(delete) > 0:
            options += " "
            options += " ".join(
                [f"{key}-={value}" for key, value in delete.items()]
            )
        # console.print(
        #     f"Updating partition: {name} with options: {options}"
        # )
        args = [
            "scontrol",
            "update",
            f"partitionname={name}",
            options,
        ]

        try:
            result = subprocess.run(
                ["echo", *args],
                check=True,
                capture_output=True,
                text=True,
            )
            if result.stdout:
                console.print(result.stdout)
            if verbose:
                console.print(
                    f"[green]Partition '{name}' updated successfully.[/green]"
                )
        except subprocess.CalledProcessError as e:
            console.print(
                f"[red]Failed to update partition '{name}':[/red]"
                f" {e.stderr or e}"
            )

    @classmethod
    def delete(cls, name: str) -> None:
        """Delete a partition."""
        console.print(f"Deleting partition: {name}")

        # TODO: Implement partition creation

    @classmethod
    def show(cls, field: str = None) -> None:
        """Show partition information."""
        console.print("Partition information:")
        if field:
            console.print(f"Field: {field}")
        # TODO: Implement partition information display


# create_node(name)
# create_user(name)
# create_qos(name)
# create_account(name)
# create_reservation(name)
# create_coordinator(name)
# create_config(name)
