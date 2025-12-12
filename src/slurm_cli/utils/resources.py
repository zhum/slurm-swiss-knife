import json
import os
import re
import subprocess
import time

# from enum import Enum
from typing import Any, Dict, List, Tuple

from .utils import console

SPINNER_STYLE = "dots2"
# moon, dots, simpleDots, dots2, dots12
# noise, line
SPINNER_SPEED = 1.0


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
        "associations": f"{CACHE_DIR}slurm_cli_associations.json",
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
        "associations": f"{CACHE_DIR}slurm_cli_associations.list",
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
        "associations": ["sacctmgr", "show", "associations", "--json"],
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
    ) -> Tuple[str, dict]:
        """Guess the resource type from the resource name."""
        if name[:1] == "j" or re.match(r"^[0-9_]+$", name):
            return "jobs", None
        part = cls.cached_resource_list("partitions")
        if name[:4] == "part" or (part and name in part):
            return "partitions", Resource.cached_resource(
                "partitions", force_update
            )
        node = cls.cached_resource_list("nodes")
        if name[:4] == "node" or (node and name in node):
            return "nodes", Resource.cached_resource(
                "nodes", force_update
            )
        user = cls.cached_resource_list("users")
        if name[:4] == "user" or (user and name in user):
            return "users", Resource.cached_resource(
                "users", force_update
            )
        qos = cls.cached_resource_list("qos")
        if name[:3] == "qos" or (qos and name in qos):
            return "qos", Resource.cached_resource("qos", force_update)
        account = cls.cached_resource_list("accounts")
        if name[:3] == "acc" or (account and name in account):
            return "accounts", Resource.cached_resource(
                "accounts", force_update
            )
        reservation = cls.cached_resource_list("reservations")
        if name[:3] == "res" or (reservation and name in reservation):
            return "reservations", Resource.cached_resource(
                "reservations", force_update
            )
        coordinator = cls.cached_resource_list("coordinators")
        if name[:5] == "coord" or (coordinator and name in coordinator):
            return "coordinators", Resource.cached_resource(
                "coordinators", force_update
            )
        if name[:4] == "prob":
            return "problems", []
        elif name[:4] == "stat":
            return "stats", []
        elif name[:4] == "assoc":
            return "associations", []
        elif name[:4] == "dump":
            return "dump", []
        elif name[:2] == "ev":
            return "events", []
        elif name[:3] == "lic" or name[:4] == "reso":
            return "licenses", []
        elif name[:3] == "bad" or name[:3] == "runa":
            return "runawayjobs", []
        elif name[:3] == "tra":
            return "transactions", []
        elif name[:2] == "tr":
            return "tres", []
        elif name[:2] == "ar":
            return "archive", []

        return "unknown", None

    @classmethod
    def update_cache(cls, name: str) -> Dict[str, Any]:
        if name == "partitions":
            raw_data = cls.run_cmd(cls.CACHE_CMD[name])
            raw_data = cls.partitions2json(raw_data)
        elif name == "reservations":
            raw_data = cls.run_cmd_json(cls.CACHE_CMD[name])
            raw_data = {
                hash.pop("name"): hash
                for hash in raw_data["reservations"]
            }
        elif name == "nodes":
            raw_data = cls.run_cmd_json(cls.CACHE_CMD[name])
            raw_data = {
                hash.pop("name"): hash for hash in raw_data["nodes"]
            }
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
            speed=SPINNER_SPEED,
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
        except (
            subprocess.CalledProcessError,
            FileNotFoundError,
            ValueError,
        ) as e:
            console.print(
                f"[red]Failed to run command '{cmd}':[/red]" f" {e}"
            )
            if result and result.stderr:
                console.print(result.stderr)
            if result and result.stdout:
                console.print(result.stdout)
            exit(1)
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
        """Convert partitions to JSON.

        Partition data is multi-line format:
        PartitionName=xxx
           Key1=Value1 Key2=Value2
           Key3=Value3
        (empty line)
        """
        partitions = {}
        current_partition = None
        current_data = {}

        for line in output.splitlines():
            line = line.strip()

            # Empty line marks end of a partition block
            if not line:
                if current_partition:
                    partitions[current_partition] = current_data
                    current_partition = None
                    current_data = {}
                continue

            # Parse key=value pairs from the line
            for pair in line.split():
                if "=" in pair:
                    key, value = pair.split("=", 1)

                    # Check if this starts a new partition
                    if key == "PartitionName":
                        # Save previous partition if any
                        if current_partition:
                            partitions[current_partition] = current_data
                        current_partition = value
                        current_data = {}
                    else:
                        current_data[key] = value

        # Don't forget the last partition
        if current_partition:
            partitions[current_partition] = current_data

        return partitions
