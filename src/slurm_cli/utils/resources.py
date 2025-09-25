import json
import os
import re
import subprocess
import time
from enum import Enum
from typing import Any, Dict, Tuple, List

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
    unknown = None


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
    CACHE_LIST_FILES = {
        "nodes": f"{CACHE_DIR}slurm_cli_nodes.list",
        "partitions": f"{CACHE_DIR}slurm_cli_partitions.list",
        "jobs": f"{CACHE_DIR}slurm_cli_jobs.list",
        "users": f"{CACHE_DIR}slurm_cli_users.list",
        "qos": f"{CACHE_DIR}slurm_cli_qos.list",
        "accounts": f"{CACHE_DIR}slurm_cli_accounts.list",
        "reservations": f"{CACHE_DIR}slurm_cli_reservations.list",
        "coordinators": f"{CACHE_DIR}slurm_cli_coordinators.list",
        "config": f"{CACHE_DIR}slurm_cli_config.list",
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
    def set_cache_timeout(cls, timeout: int) -> None:
        """Set the cache timeout."""
        cls.CACHE_TIMEOUT = timeout

    @classmethod
    def guess_resource_type(
        cls, name: str, force_update: bool = False
    ) -> Tuple[ResourceType, dict]:
        """Guess the resource type from the resource name."""
        if re.match(r"^[0-9_]+$", name):
            return ResourceType.jobs, None
        part = cls.cached_resource_list(
            "partitions"
        )
        if part and name in part:
            return ResourceType.partitions, Resource.cached_resource(
                "partitions",
                force_update
            )
        node = cls.cached_resource_list(
            "nodes"
        )
        if node and name in node:
            return ResourceType.nodes, Resource.cached_resource(
                "nodes",
                force_update
            )
        user = cls.cached_resource_list(
            "users"
        )
        if user and name in user:
            return ResourceType.users, Resource.cached_resource(
                "users",
                force_update
            )
        qos = cls.cached_resource_list(
            "qos"
        )
        if qos and name in qos:
            return ResourceType.qos, Resource.cached_resource(
                "qos",
                force_update
            )
        account = cls.cached_resource_list(
            "accounts"
        )
        if account and name in account:
            return ResourceType.accounts, Resource.cached_resource(
                "accounts",
                force_update
            )
        reservation = cls.cached_resource_list(
            "reservations"
        )
        if reservation and name in reservation:
            return ResourceType.reservations, Resource.cached_resource(
                "reservations",
                force_update
            )
        coordinator = cls.cached_resource_list(
            "coordinators"
        )
        if coordinator and name in coordinator:
            return ResourceType.coordinators, Resource.cached_resource(
                "coordinators",
                force_update
            )
        return ResourceType.unknown, None

    @classmethod
    def update_cache(cls, name: str) -> Dict[str, Any]:
        if name == "partitions":
            raw_data = cls.run_cmd(cls.CACHE_CMD[name])
            raw_data = cls.partitions2json(raw_data)
        elif name == "reservations":
            raw_data = cls.run_cmd_json(cls.CACHE_CMD[name])
            raw_data = {hash.pop("name"): hash for
                        hash in raw_data['reservations']}
        elif name == "nodes":
            raw_data = cls.run_cmd_json(cls.CACHE_CMD[name])
            raw_data = {hash.pop("name"): hash for
                        hash in raw_data['nodes']}
        else:
            raw_data = cls.run_cmd_json(cls.CACHE_CMD[name])
        if raw_data:
            with open(cls.CACHE_FILES[name], "w") as f:
                json.dump(raw_data, f)
                os.chmod(cls.CACHE_FILES[name], 0o600)
            with open(cls.CACHE_LIST_FILES[name], "w") as f:
                json.dump(list(raw_data.keys()), f)
                os.chmod(cls.CACHE_LIST_FILES[name], 0o600)
        return raw_data

    @classmethod
    def cached_resource(
        cls,
        name: str,
        force_update: bool = False,
    ) -> bool:  # noqa: E501
        """Check if the resource is a cached resource."""
        file = cls.CACHE_FILES.get(name)
        if not file:
            return None
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
    def cached_resource_list(
        cls,
        name: str,
    ) -> List[str]:
        """Check if the resource is a cached resource."""
        file = cls.CACHE_LIST_FILES.get(name)
        if not file:
            return []
        if not os.path.exists(file):
            # just update!
            cls.cached_resource(name)
        try:
            with open(file, "r") as f:
                raw_data = json.load(f)
            return raw_data
        except Exception:
            return []
        return []

    @classmethod
    def run_cmd_json(cls, cmd: [str]) -> Dict[str, Any] | None:
        """Run a command and return the JSON output."""
        result = None
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
        except (subprocess.CalledProcessError,
                FileNotFoundError,
                ValueError) as e:
            console.print(
                f"[red]Failed to run command '{cmd}':[/red]" f" {e}"
            )
            if result and result.stderr:
                console.print(result.stderr)
            if result and result.stdout:
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
