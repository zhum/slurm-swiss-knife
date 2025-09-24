import json
import os
import re
import subprocess
import time
from enum import Enum
from typing import Any, Dict

from .utils import console


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


SPINNER_STYLE = "dots2"
# moon, dots, simpleDots, dots2, dots12
# noise, line


class Resource:
    CACHE_TIMEOUT = 60
    CACHE_DIR = "/tmp/"
    CACHE_FILES = {
        "nodes": f"{CACHE_DIR}slurm_cli_nodes.json",
        "partitions": f"{CACHE_DIR}slurm_cli_partitions.json",
        "jobs": f"{CACHE_DIR}slurm_cli_jobs.json",
        "users": f"{CACHE_DIR}slurm_cli_users.json",
        "qos": f"{CACHE_DIR}slurm_cli_qos.json",
        "accounts": f"{CACHE_DIR}slurm_cli_accounts.json",
        "reservations": f"{CACHE_DIR}slurm_cli_reservations.json",
        "coordinators": f"{CACHE_DIR}slurm_cli_coordinators.json",
        "config": f"{CACHE_DIR}slurm_cli_config.json",
    }
    CACHE_CMD = {
        "nodes": ["scontrol", "show", "nodes", "--json"],
        "partitions": ["scontrol", "show", "partitions", "--details"],
        "jobs": ["sacctmgr", "show", "jobs", "--json"],
        "users": ["sacctmgr", "show", "users", "--json"],
        "qos": ["sacctmgr", "show", "qos", "--json"],
        "accounts": ["sacctmgr", "show", "accounts", "--json"],
        "reservations": ["scontrol", "show", "reservations", "--json"],
        "coordinators": ["sacctmgr", "show", "coordinators", "--json"],
        "config": ["scontrol", "show", "config", "--json"],
    }

    @classmethod
    def guess_resource_type(
        cls, name: str, force_update: bool = False
    ) -> ResourceType:
        """Guess the resource type from the resource name."""
        if re.match(r"^[0-9_]+$", name):
            return ResourceType.jobs
        if cls.cached_resource(
            name,
            ResourceType.nodes,
            force_update,
        ):
            return ResourceType.nodes
        if cls.cached_resource(
            name,
            ResourceType.partitions,
            force_update,
        ):
            return ResourceType.partitions
        if cls.cached_resource(
            name,
            ResourceType.users,
            force_update,
        ):
            return ResourceType.users
        if cls.cached_resource(
            name,
            ResourceType.qos,
            force_update,
        ):
            return ResourceType.qos
        if cls.cached_resource(
            name,
            ResourceType.accounts,
            force_update,
        ):
            return ResourceType.accounts
        if cls.cached_resource(
            name,
            ResourceType.reservations,
            force_update,
        ):
            return ResourceType.reservations
        return ResourceType.unknown

    @classmethod
    def update_cache(cls, name: str) -> Dict[str, Any]:
        if name == ResourceType.partitions:
            raw_data = cls.run_cmd(cls.CACHE_CMD[name])
            raw_data = cls.partitions2json(raw_data)
        else:
            raw_data = cls.run_cmd_json(cls.CACHE_CMD[name])
        if raw_data:
            with open(cls.CACHE_FILES[name], "w") as f:
                json.dump(raw_data, f)
                os.chmod(cls.CACHE_FILES[name], 0o600)
        return raw_data

    @classmethod
    def cached_resource(
        cls,
        name: str,
        resource_type: ResourceType,
        force_update: bool = False,
    ) -> bool:  # noqa: E501
        """Check if the resource is a cached resource."""
        file = cls.CACHE_FILES[name]
        if not force_update and os.path.exists(file):
            file_mtime = os.path.getmtime(file)
            if time.time() - file_mtime < cls.CACHE_TIMEOUT:
                with open(cls.CACHE_FILES[name], "r") as f:
                    raw_data = json.load(f)
                # The cache file already has the correct
                # structure (name -> data)
                # so we can use it directly
                return raw_data

        # Update cache and check again
        with console.status(
            "[bold blue]Calling slurm...",
            spinner=SPINNER_STYLE,
            spinner_style="yellow",
            speed=2,
        ):
            data = cls.update_cache(name)
        return data

    @classmethod
    def run_cmd_json(cls, cmd: [str]) -> Dict[str, Any] | None:
        """Run a command and return the JSON output."""
        try:
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True,
            )
            if result.stdout:
                json_text = json.loads(result.stdout)
                return json_text
        except (subprocess.CalledProcessError, ValueError) as e:
            console.print(
                f"[red]Failed to run command '{cmd}':[/red]" f" {e}"
            )
            if result.stderr:
                console.print(result.stderr)
            if result.stdout:
                console.print(result.stdout)
        return None

    @classmethod
    def run_cmd(cls, cmd: str) -> str:
        """Run a command and return the output."""
        result = None
        try:
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True,
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            console.print(
                f"[red]Failed to run command '{cmd}':[/red]" f" {e}"
            )
            if result.stderr:
                console.print(result.stderr)
            if result.stdout:
                console.print(result.stdout)
        return None

    @classmethod
    def partitions2json(cls, output: str) -> dict:
        """Convert partitions to JSON."""
        partitions = {}
        for line in output.splitlines():
            hash = {
                x[0]: x[1]
                for x in [y.split("=") for y in line.strip().split(" ")]
            }
            name = hash.pop("PartitionName")
            partitions[name] = hash
        return partitions
