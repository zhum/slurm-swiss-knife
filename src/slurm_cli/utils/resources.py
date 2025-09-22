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


class Resource:
    CACHE_TIMEOUT = 60
    cached_nodes_file = "/tmp/slurm_cli_nodes.json"
    cached_partitions_file = "/tmp/slurm_cli_partitions.json"
    cached_jobs_file = "/tmp/slurm_cli_jobs.json"
    cached_users_file = "/tmp/slurm_cli_users.json"
    cached_qos_file = "/tmp/slurm_cli_qos.json"
    cached_accounts_file = "/tmp/slurm_cli_accounts.json"
    cached_reservations_file = "/tmp/slurm_cli_reservations.json"

    @classmethod
    def guess_resource_type(cls, name: str) -> ResourceType:
        """Guess the resource type from the resource name."""
        if re.match(r"^[0-9_]+$", name):
            return ResourceType.jobs
        if cls.cached_resource(
            name,
            cls.cached_nodes_file,
            "scontrol show node --json",
            ResourceType.nodes,
        ):
            return ResourceType.nodes
        if cls.cached_resource(
            name,
            cls.cached_partitions_file,
            "scontrol show partition --json",
            ResourceType.partitions,
        ):
            return ResourceType.partitions
        if cls.cached_resource(
            name,
            cls.cached_users_file,
            "sacctmgr show user --json",
            ResourceType.users,
        ):
            return ResourceType.users
        if cls.cached_resource(
            name,
            cls.cached_qos_file,
            "sacctmgr show qos --json",
            ResourceType.qos,
        ):
            return ResourceType.qos
        if cls.cached_resource(
            name,
            cls.cached_accounts_file,
            "sacctmgr show accounts --json",
            ResourceType.accounts,
        ):
            return ResourceType.accounts
        if cls.cached_resource(
            name,
            cls.cached_reservations_file,
            "scontrol show reservations --json",
            ResourceType.reservations,
        ):
            return ResourceType.reservations
        return ResourceType.unknown

    @classmethod
    def update_cache(cls, file: str, cmd: str) -> Dict[str, Any]:
        raw_data = cls.run_cmd_json(
            ["scontrol", "show", "node", "--json"]
        )
        data = {node["name"]: node for node in raw_data["nodes"]}
        with open(cls.cached_nodes_file, "w") as f:
            json.dump(data, f)
            os.chmod(cls.cached_nodes_file, 0o600)
        return data

    @classmethod
    def cached_resource(
        cls, name: str, file: str, cmd: str, resource_type: ResourceType
    ) -> bool:  # noqa: E501
        """Check if the resource is a cached resource."""
        if os.path.exists(file):
            file_mtime = os.path.getmtime(file)
            if time.time() - file_mtime < cls.CACHE_TIMEOUT:
                with open(file, "r") as f:
                    raw_data = json.load(f)
                # The cache file already has the correct structure (name -> data)
                # so we can use it directly
                return name in raw_data

        # Update cache and check again
        data = cls.update_cache(file, cmd)
        return name in data

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
                f"[red]Failed to run command '{cmd}':[/red]"
                f" {e.stderr or e}"
            )
        return None

    @classmethod
    def run_cmd(cls, cmd: str) -> str:
        """Run a command and return the output."""
        return subprocess.check_output(cmd, shell=True).decode("utf-8")
