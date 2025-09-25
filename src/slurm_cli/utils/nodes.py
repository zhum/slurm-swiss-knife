"""Utilities for managing nodes."""

import json
import subprocess
from typing import Any

from .base_resource import BaseSlurmResource
from .utils import console
from rich.markup import escape


class Node(BaseSlurmResource):
    _WIDTH = None

    def __init__(self, name: str, **kwargs: Any):
        self.name = name
        self.kwargs = kwargs

    @classmethod
    def max_width(cls) -> int:
        """Get the maximum width of the console."""
        if cls._WIDTH is None:
            cls._WIDTH = console.width
        return cls._WIDTH

    @classmethod
    def create(cls, name: str, **kwargs: Any) -> None:
        """Create a new node."""
        console.print(f"Creating node: {name}")
        args = ["scontrol", "create", "node", f"name={name}"]
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
                f"[green]Node '{name}' created successfully.[/green]"
            )
            if result.stdout:
                console.print(result.stdout)
        except subprocess.CalledProcessError as e:
            console.print(
                f"[red]Failed to create node '{name}':[/red] {e.stderr or e}"
            )

    @classmethod
    def update(cls, name: str, **kwargs: Any) -> None:
        """Update a node."""
        console.print(f"Updating node: {name}")

    @classmethod
    def delete(cls, name: str) -> None:
        """Delete a node."""
        console.print(f"Deleting node: {name}")

    @classmethod
    def show(
        cls,
        name: str = None,
        data: dict = None,
        style: str = "pretty",
        verbose: bool = False,
        force_cache_update: bool = False,
    ) -> None:
        """Show node information."""
        if not data:
            console.print_json("[red]No data available.[/red]")
            return
        try:
            if style == "json":
                if name:
                    console.print_json(json.dumps(data[name], indent=4))
                else:
                    console.print_json(json.dumps(data, indent=4))
            else:  # pretty style
                if name:
                    cls.show_one_pretty(name, data[name], verbose)
                else:
                    for node in data.keys():
                        cls.show_one_pretty(node, data[node], verbose)
        except subprocess.CalledProcessError as e:
            console.print(
                f"[red]Failed to show node(s):[/red] {e.stderr or e}"
            )

    @classmethod
    def show_one_pretty(
        cls,
        name: str,
        data: list[dict],
        verbose: bool = False,
    ) -> None:
        """Show one node information."""
        console.print("=============================================")
        # console.print_json(json.dumps(data, indent=4))
        console.print(f"[label]Node[/]: [object]{escape(name)}[/] "
                      f"{','.join(data['state'])}")
        console.print(f"[label]CPUs[/]: [b]{data['cpus']}/"
                      f"{data['alloc_cpus']}[/] "
                      f"[label]Mem[/]: [b]{data['real_memory']}/"
                      f"{data['alloc_memory']}[/]")
        console.print(f"[label]GRES[/]: [b]{data['gres']} "
                      f"[label]Used[/]: {data['gres_used']}[/]")
        console.print(f"[label]TRES[/]: [b]{data['tres']} "
                      f"[label]Used[/]: {data['tres_used']}[/]")
        for k in ["state", "cpus", "alloc_cpus", "real_memory",
                  "alloc_memory", "gres", "gres_used", "tres", "tres_used"]:
            data.pop(k)
        if not verbose:
            for k in ["cpu_load", "architecture", "boards", "boot_time",
                      "cluster_name", "cores", "specialized_cores",
                      "cpu_binding", "free_mem", "effective_cpus",
                      "specialized_cpus", "energy", "external_sensors",
                      "power", "gres_drained", "next_state_after_reboot",
                      "address", "operating_system", "owner", "port",
                      "reason_changed_at", "resume_after",
                      "specialized_memory", "last_busy",
                      "alloc_idle_cpus", "tres_weighted",
                      "slurmd_start_time", "sockets", "threads",
                      "temporary_disk", "weight", "version"]:
                data.pop(k)
            cls.print_dict_pretty(data)
