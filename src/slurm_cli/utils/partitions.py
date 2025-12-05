"""Utilities for managing partitions."""

import json
import subprocess
from typing import Any

from rich.markup import escape

from .base_resource import BaseSlurmResource

# from .resources import Resource, ResourceType
from .utils import console


class Partition(BaseSlurmResource):

    _WIDTH = None
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
    value_types = {
        "allowgroups": {"def": "ALL", "flag": False},
        "allowaccounts": {"def": "ALL", "flag": False},
        "allowqos": {"def": "ALL", "flag": False},
        "allocnodes": {"def": "ALL", "flag": False},
        "default": {"def": "NO", "flag": True},
        "defmempernode": {"def": "UNLIMITED", "flag": False},
        "defmempercpu": {"def": "UNLIMITED", "flag": False},
        "qos": {"def": "", "flag": False},
        "disablerootjobs": {"def": "NO", "flag": True},
        "exclusiveuser": {"def": "NO", "flag": True},
        "exclusivetopo": {"def": "NO", "flag": True},
        "gracetime": {"def": "0", "flag": False},
        "hidden": {"def": "NO", "flag": True},
        "maxnodes": {"def": "UNLIMITED", "flag": False},
        "maxtime": {"def": "", "flag": False},
        "minnodes": {"def": "1", "flag": False},
        "lln": {"def": "NO", "flag": True},
        "maxcpuspernode": {"def": "UNLIMITED", "flag": False},
        "maxcpuspersocket": {"def": "UNLIMITED", "flag": False},
        "priorityjobfactor": {"def": "1", "flag": False},
        "prioritytier": {"def": "1", "flag": False},
        "rootonly": {"def": "NO", "flag": True},
        "reqresv": {"def": "NO", "flag": True},
        "oversubscribe": {"def": "NO", "flag": True},
        "overtimelimit": {"def": "NONE", "flag": False},
        "preemptmode": {"def": "OFF", "flag": False},
        "selecttypeparameters": {"def": "NONE", "flag": False},
        "jobdefaults": {"def": "(null)", "flag": False},
        "maxmempernode": {"def": "UNLIMITED", "flag": False},
        "tres": {"def": "", "flag": False},
        "tresbillingweights": {"def": "", "flag": False},
    }

    def __init__(self, name: "str", **kwargs: Any):
        self.name = name
        self.kwargs = kwargs

    @classmethod
    def max_width(cls) -> int:
        """Get the maximum width of the console."""
        if cls._WIDTH is None:
            cls._WIDTH = console.width
        return cls._WIDTH

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
            console.print(
                "[yellow]Warning: Adding options is not supported"
                " for partitions.[/yellow]"
            )
        if len(delete) > 0:
            console.print(
                "[yellow]Warning: Deleting options is not supported"
                " for partitions.[/yellow]"
            )
        if len(set) > 0:
            options += " "
            options += " ".join(
                [f"{key}-={value}" for key, value in delete.items()]
            )
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
        args = [
            "scontrol",
            "delete",
            "partitionname={name}",
        ]
        try:
            result = subprocess.run(
                args,
                check=True,
                capture_output=True,
                text=True,
            )
            if result.stdout:
                console.print(result.stdout)
            console.print(
                f"[green]Partition '{name}' "
                "deleted successfully.[/green]"
            )
        except subprocess.CalledProcessError as e:
            console.print(
                f"[red]Failed to delete partition '{name}':[/red]"
                f" {e.stderr or e}"
            )

    @classmethod
    def show(
        cls,
        name: str = None,
        data: dict = None,
        style: str = "pretty",
        force_cache_update: bool = False,
        delimiter: str = ";",
    ) -> None:
        """Show partition information."""
        if style == "pretty":
            cls.show_pretty(name, data)
        elif style == "json":
            if name:
                console.print_json(
                    json.dumps(
                        data[name],
                        indent=4,
                    )
                )
            else:
                console.print_json(
                    json.dumps(
                        data,
                        indent=4,
                    )
                )
        elif style == "csv":
            cls.show_csv(name, data, delimiter)
        else:
            console.print(f"[red]Invalid style '{style}'.[/red]")

    @classmethod
    def show_csv(
        cls,
        name: str = None,
        partitions: dict = None,
        delimiter: str = ";",
    ) -> None:
        """Show partition information in CSV format."""
        if not partitions:
            console.print("[red]No partitions found.[/red]")
            return

        # Determine all unique fields across all partitions
        all_fields = set()
        partitions_to_show = (
            {name: partitions[name]}
            if name and name in partitions
            else partitions
        )

        for partition_data in partitions_to_show.values():
            all_fields.update(partition_data.keys())

        # Sort fields for consistent output (with common fields first)
        priority_fields = [
            "State",
            "TotalNodes",
            "TotalCPUs",
            "MaxTime",
            "DefaultTime",
        ]
        sorted_fields = [
            f for f in priority_fields if f in all_fields
        ] + sorted([f for f in all_fields if f not in priority_fields])

        # Print CSV header
        headers = ["PartitionName"] + sorted_fields
        print(delimiter.join(headers))

        # Print data rows
        for partition_name in sorted(partitions_to_show.keys()):
            data = partitions_to_show[partition_name]
            row = [partition_name] + [
                str(data.get(field, "")) for field in sorted_fields
            ]
            print(delimiter.join(row))

    @classmethod
    def show_pretty(
        cls, name: str = None, partitions: dict = None
    ) -> None:

        if not partitions:
            console.print("[red]No partitions found.[/red]")
            return
        if name:
            Partition.show_one_pretty(name, partitions[name])
        else:
            for partition in sorted(partitions.keys()):
                Partition.show_one_pretty(
                    partition, partitions[partition]
                )

    # @classmethod
    # def show_one(cls, name: str, partitions: dict) -> None:
    #     """Show partition information."""
    #     if not partitions:
    #         console.print("[red]No partitions found.[/red]")
    #         return
    #     if name:
    #         Partition.show_one(name, partitions[name])
    #     else:
    #         for partition in partitions.keys():
    #             Partition.show_one(partition, partitions[partition])

    @classmethod
    def show_one_pretty(cls, name: str, data: list[dict]) -> None:
        """Show one partition information."""
        states = {
            "UP": "[green]UP [/green]",
            "DRAIN": "[yellow]DRN[/yellow]",
            "INACTIVE": "[blue]INA[/blue]",
            "DOWN": "[red]DWN[/red]",
        }
        width = cls.max_width()
        state = states[data.pop("State")]
        max_time = data.pop("MaxTime")
        def_time = data.pop("DefaultTime")
        total_nodes = data.pop("TotalNodes")
        total_cpus = data.pop("TotalCPUs")
        second_line_len = len(
            f"Nodes/CPUs: {total_nodes}/{total_cpus} "
        )
        nodes = (
            data["Nodes"]
            if len(data["Nodes"]) < width - second_line_len - 3
            else data["Nodes"][: (width - second_line_len - 5)] + "..."
        )
        data.pop("Nodes")
        console.print(
            "=============================================\n"
            f"Partition: [object]{escape(name)}[/] {state} "
            f"def/max [time]{def_time}/{max_time}[/]"
        )
        console.print(
            f"Nodes/CPUs: [b]{total_nodes}/{total_cpus}"
            f"[/] ([nodes]{escape(nodes)}[/])"
        )

        # Check for missing fields and track them
        missing_fields = []
        extended_value_types = dict(cls.value_types)
        for key in data.keys():
            if key.lower() not in cls.value_types:
                missing_fields.append(key)
                # Use default values for missing fields
                extended_value_types[key.lower()] = {
                    "def": "",
                    "flag": False,
                }

        flags = {
            key.lower(): value
            for key, value in data.items()
            if extended_value_types[key.lower()]["flag"]
        }
        not_flags = {
            key.lower(): value
            for key, value in data.items()
            if not extended_value_types[key.lower()]["flag"]
        }
        flag_was_printed = cls.print_dict_pretty_flags_def(
            flags, extended_value_types
        )
        if flag_was_printed:
            console.print("  ", end="")
        cls.print_dict_pretty_def(not_flags, extended_value_types)

        # Show warning for missing fields
        if missing_fields:
            console.print(
                f"\n[yellow]Warning: Unknown partition fields "
                f"(using defaults): {', '.join(missing_fields)}[/yellow]"
            )
