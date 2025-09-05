#!/usr/bin/env python3

"""
Show the Slurm partitions statistics

Original Author: Ole H. Nielsen, Technical University of Denmark
E-mail: Ole.H.Nielsen@fysik.dtu.dk
Home page: https://github.com/OleHolmNielsen/Slurm_tools

Converted to Python by:
  Sergey Zhumatiy <sergzhum@gmail.com> with help of Cursor AI
"""

import argparse
import subprocess
import sys
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Set, Tuple


class Colors:
    """ANSI color codes for terminal output"""

    RED = "\033[1;31m"
    GREEN = "\033[1;32m"
    MAGENTA = "\033[1;35m"
    NORMAL = "\033[0m"

    @staticmethod
    def disable():
        """Disable all colors"""
        Colors.RED = ""
        Colors.GREEN = ""
        Colors.MAGENTA = ""
        Colors.NORMAL = ""


class PartitionData:
    """Data structure for partition statistics"""

    def __init__(self, name: str):
        self.name = name
        self.order = 0
        self.state = ""
        self.nodes = 0
        self.freenodes = 0
        self.freecores = 0
        self.totalcores = 0
        self.corespernode = 0
        self.mincores = 0
        self.maxcores = 0
        self.memory = 0
        self.memoryplus = " "
        self.minmemory = 0
        self.maxmemory = 0
        self.timelimit = ""
        self.defaulttime = ""
        self.minnodes = 0
        self.maxnodes = 0
        self.gres = ""
        self.nodelist = ""
        self.clustername = ""
        self.is_default = False
        self.root_only = False
        self.is_hidden = False
        self.pending_reboot = ""
        self.maintenance = ""


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Show the Slurm partitions statistics",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Notes about the columns:
1. An * after the partition name identifies the default Slurm partition.
2. An @ after the partition state means that some nodes are pending a reboot.
3. An $ after the partition state means that some nodes are in
   maintenance mode.
4. An R after the partition name identifies a root-only Slurm partition.
5. An H after the partition name identifies a hidden Slurm partition.
        """,
    )

    parser.add_argument(
        "-p",
        "--partition",
        dest="partition_list",
        help="Print only jobs in partition(s) <partition-list>",
    )
    parser.add_argument(
        "-g", "--gres", action="store_true", help="Print also GRES information"
    )
    parser.add_argument(
        "-N",
        "--nodelist",
        action="store_true",
        help="Print also Node list in each partition",
    )
    parser.add_argument(
        "-m",
        "--minmax",
        action="store_true",
        help="Print minimum and maximum values for memory and cores/node",
    )
    parser.add_argument(
        "-a",
        "-P",
        "--all",
        dest="all_partitions",
        action="store_true",
        help=(
            "Display information about all partitions "
            "(including hidden ones), and include also nodes "
            "that are in maintenance mode"
        ),
    )
    parser.add_argument(
        "-f",
        "--federation",
        action="store_true",
        help="Show all partitions from the federation if a member of one. "
        "Requires Slurm 18.08 and newer",
    )
    parser.add_argument(
        "-n",
        "--no-headers",
        dest="no_headers",
        action="store_true",
        help="No headers or colors will be printed (for parsing)",
    )

    return parser.parse_args()


def run_command(cmd: List[str]) -> List[str]:
    """Run a shell command and return output lines"""
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=True
        )
        return [line for line in result.stdout.strip().split("\n") if line]
    except subprocess.CalledProcessError as e:
        print(f"Error running command {' '.join(cmd)}: {e}", file=sys.stderr)
        return []


def get_cluster_name() -> str:
    """Get the current cluster name"""
    output = run_command(["scontrol", "show", "config"])
    for line in output:
        if "ClusterName" in line:
            parts = line.split()
            if len(parts) >= 3:
                return parts[2]
    return "unknown"


def get_hidden_partitions() -> Set[str]:
    """Identify hidden partitions"""
    hide_output = run_command(["sinfo", "--hide", "-o", "%P"])
    all_output = run_command(["sinfo", "--all", "-o", "%P"])

    hide_set = set(p.rstrip("*") for p in hide_output)
    all_set = set(p.rstrip("*") for p in all_output)

    return all_set - hide_set


def get_pending_jobs(
    federation: bool, partition_list: str
) -> Tuple[Dict[str, int], Dict[str, int]]:
    """Get pending job statistics"""
    pending_resources = defaultdict(int)
    pending_other = defaultdict(int)

    cmd = [
        "squeue",
        "--noheader",
        "-t",
        "pending",
        "-O",
        "JobID,Partition,NumCPUs,Reason",
    ]
    if federation:
        cmd.append("--federation")
    if partition_list:
        cmd.extend(["-p", partition_list])

    output = run_command(cmd)

    for line in output:
        parts = line.split()
        if len(parts) < 4:
            continue

        job_partitions = parts[1].split(",")
        try:
            numcpus = int(parts[2])
        except ValueError:
            continue
        reason = parts[3]

        for p in job_partitions:
            if reason in ["(Resources)", "(Priority)"]:
                pending_resources[p] += numcpus
            else:
                pending_other[p] += numcpus

    return pending_resources, pending_other


def parse_sinfo_output(
    args, mycluster: str, hidden_partitions: Set[str]
) -> Dict[str, PartitionData]:
    """Parse sinfo output and build partition data"""
    partitions = {}

    # Build sinfo command
    sinfo_options = (
        "Partition,Available,Nodes,CPUsState,Memory,Time,"
        "DefaultTime,Size,StateLong,Gres: ,Root,NodeList: ,Cluster"
    )
    cmd = ["sinfo", "--noheader", "--exact", "-O", sinfo_options]

    if args.federation:
        cmd.append("--federation")
    if args.partition_list:
        cmd.extend(["-p", args.partition_list])
    if args.all_partitions:
        cmd.append("--all")

    output = run_command(cmd)

    for idx, line in enumerate(output, 1):
        # Split the line into fields (sinfo uses fixed-width columns)
        fields = line.split()
        if len(fields) < 11:
            continue

        # Parse partition name and check for default (*)
        partition_name = fields[0].rstrip("*")
        is_default = fields[0].endswith("*")

        # Initialize partition data if needed
        if partition_name not in partitions:
            partitions[partition_name] = PartitionData(partition_name)
            partitions[partition_name].order = idx
            partitions[partition_name].is_default = is_default
            partitions[partition_name].is_hidden = (
                partition_name in hidden_partitions
            )

        p = partitions[partition_name]

        # Parse fields
        p.state = fields[1]  # Available: up or down
        try:
            nodes = int(fields[2])
        except ValueError:
            nodes = 0
        p.nodes += nodes

        # Parse CPU cores (A/I/O/T format)
        cpus_state = fields[3]
        cpus_parts = cpus_state.split("/")
        if len(cpus_parts) == 4:
            try:
                idle_cores = int(cpus_parts[1])
                total_cores = int(cpus_parts[3])
                p.freecores += idle_cores
                p.totalcores += total_cores

                # Calculate cores per node
                if nodes > 0:
                    cpn = total_cores / nodes
                    if p.corespernode == 0 or cpn < p.corespernode:
                        p.corespernode = int(cpn)

                    if args.minmax:
                        if p.mincores == 0 or cpn < p.mincores:
                            p.mincores = int(cpn)
                        if cpn > p.maxcores:
                            p.maxcores = int(cpn)
            except (ValueError, ZeroDivisionError):
                pass

        # Parse memory
        mem_str = fields[4]
        mem_has_plus = mem_str.endswith("+")
        mem_value = int(mem_str.rstrip("+"))
        mem_gb = int(mem_value / 1000)  # Convert MB to GB

        if p.memory == 0 or mem_gb < p.memory:
            p.memory = mem_gb
        if mem_gb > p.memory:
            p.memoryplus = "+"
        if mem_has_plus:
            p.memoryplus = "+"

        if args.minmax:
            if p.minmemory == 0 or mem_gb < p.minmemory:
                p.minmemory = mem_gb
            if mem_gb > p.maxmemory:
                p.maxmemory = mem_gb

        # Time limits
        p.timelimit = fields[5].replace(":00", "")  # Strip seconds
        p.defaulttime = fields[6].replace(":00", "")  # Strip seconds

        # Job sizes (min-max nodes)
        jobsize = fields[7].split("-")
        if len(jobsize) >= 1:
            try:
                p.minnodes = int(jobsize[0])
            except ValueError:
                pass
        if len(jobsize) >= 2:
            try:
                p.maxnodes = int(jobsize[1])
            except ValueError:
                pass

        # Node state
        nodestate = fields[8]
        if "@" in nodestate:
            p.pending_reboot = "@"
            nodestate = nodestate.replace("@", "")

        if "maint" in nodestate:
            p.maintenance = "$"
            if not args.all_partitions:
                continue  # Skip maintenance nodes

        if nodestate.startswith("idle"):
            p.freenodes += nodes

        # GRES
        if len(fields) > 9 and fields[9] != "(null)":
            if nodestate.startswith("idle"):
                gpustate = ":free"
            elif nodestate == "mixed":
                gpustate = ":mix"
            else:
                gpustate = ":used"

            gres_str = f"{fields[9]}({nodes}{gpustate})"
            if p.gres:
                p.gres += "+" + gres_str
            else:
                p.gres = gres_str

        # Root only
        if len(fields) > 10 and fields[10] == "yes":
            p.root_only = True

        # Node list
        if len(fields) > 11:
            nodelist_str = fields[11]
            if p.nodelist:
                p.nodelist += "," + nodelist_str
            else:
                p.nodelist = nodelist_str

        # Cluster name (federation)
        if len(fields) > 12 and fields[12] != "N/A":
            p.clustername = fields[12]
        else:
            p.clustername = mycluster

    return partitions


def print_partition_stats(
    partitions: Dict[str, PartitionData],
    pending_resources: Dict[str, int],
    pending_other: Dict[str, int],
    args,
):
    """Print formatted partition statistics"""
    # Calculate maximum partition name length
    maxlength = 5  # Minimum
    for p in partitions.values():
        plen = len(p.name)
        if p.is_default:
            plen += 1
        if p.root_only:
            plen += 1
        if p.is_hidden:
            plen += 1
        if p.is_default or p.root_only or p.is_hidden:
            plen += 1  # For the colon
        maxlength = max(maxlength, plen)

    # Calculate maximum cluster name length
    clusternamelength = 7
    for p in partitions.values():
        clusternamelength = max(clusternamelength, len(p.clustername))

    # Print headers
    if not args.no_headers:
        header1 = (
            "Partition     #Nodes     #CPU_cores  Cores_pending   "
            "Job_Nodes MaxJobTime Cores Mem/Node"
        )
        header2 = (
            "Name State Total  Idle  Total   Idle Resorc  Other   "
            "Min   Max  Day-hr:mn /node     (GB)"
        )

        # Adjust for partition name length
        n = maxlength - 5
        header1 = " " * n + header1
        header2 = " " * n + header2

        # Prepend cluster name if federation
        if args.federation:
            header1 = f"{'Cluster':<{clusternamelength}} {header1}"
            header2 = f"{'Name':<{clusternamelength}} {header2}"

        # Append GRES header
        if args.gres:
            header1 += "    GRES      "
            header2 += " (#Nodes:state)"

        # Append nodelist header
        if args.nodelist:
            header1 += "  NODELIST    "
            header2 += "               "

        print(header1)
        print(header2)

    # Sort partitions by their order
    sorted_partitions = sorted(partitions.values(), key=lambda p: p.order)

    # Print each partition
    for p in sorted_partitions:
        # Build partition name with flags
        pname = p.name
        if p.is_default or p.root_only or p.is_hidden:
            pname += ":"
        if p.is_default:
            pname += "*"
        if p.root_only:
            pname += "R"
        if p.is_hidden:
            pname += "H"

        # Truncate long names
        if len(pname) > maxlength:
            pname = pname[: maxlength - 1] + "+"

        # Add state modifiers
        state = p.state
        if p.pending_reboot:
            state += "@"
        if p.maintenance:
            state += "$"

        # Memory and cores display
        if args.minmax:
            if p.minmemory == p.maxmemory:
                memsize = str(p.memory)
            else:
                memsize = f"{p.minmemory}-{p.maxmemory}"

            if p.mincores == p.maxcores:
                cores = str(p.corespernode)
            else:
                cores = f"{p.mincores}-{p.maxcores}"
        else:
            memsize = str(p.memory) + p.memoryplus
            cores = str(p.corespernode)

        # Color codes
        if not args.no_headers:
            # Color free nodes and cores
            if p.freenodes > 0 and pending_resources[p.name] == 0:
                colornodes = Colors.GREEN
            else:
                colornodes = Colors.NORMAL

            if p.freecores > 0 and pending_resources[p.name] == 0:
                colorcores = Colors.GREEN
            else:
                colorcores = Colors.NORMAL

            # Color pending resources
            if pending_resources[p.name] > 0:
                colorpending = Colors.RED
            else:
                colorpending = Colors.NORMAL
        else:
            colornodes = colorcores = colorpending = ""

        # Print cluster name if federation
        if args.federation:
            print(f"{p.clustername:<{clusternamelength}} ", end="")

        # Print main data
        print(
            f"{pname:>{maxlength}} {state:5.5} {p.nodes:5d} "
            f"{colornodes}{p.freenodes:5d}{Colors.NORMAL} {p.totalcores:6d} "
            f"{colorcores}{p.freecores:6d}{Colors.NORMAL} "
            f"{colorpending}{pending_resources[p.name]:6d}{Colors.NORMAL} "
            f"{pending_other[p.name]:6d} {p.minnodes:5d} {p.maxnodes:5d} "
            f"{p.timelimit:10.10} {cores:5.5} {memsize:>8}",
            end="",
        )

        # Print GRES if requested
        if args.gres:
            gres_str = p.gres if p.gres else "(No_GRES)"
            print(f" {gres_str}", end="")

        # Print nodelist if requested
        if args.nodelist:
            if p.nodelist:
                # Use scontrol to collapse the nodelist
                nodelist_sorted = run_command(
                    ["scontrol", "show", "hostlistsorted", p.nodelist]
                )
                nodelist_str = (
                    nodelist_sorted[0] if nodelist_sorted else "(None)"
                )
            else:
                nodelist_str = "(None)"
            print(f" {nodelist_str}", end="")

        print()  # End of line

    # Print default partition info
    if not args.no_headers:
        default_part = next(
            (p for p in partitions.values() if p.is_default), None
        )
        if default_part:
            print(
                f"The cluster {default_part.clustername} "
                f"default partition is: {default_part.name}"
            )


def main():
    """Main function"""
    args = parse_arguments()

    # Disable colors if no-headers is set
    if args.no_headers:
        Colors.disable()

    # Get cluster information
    mycluster = get_cluster_name()
    hidden_partitions = get_hidden_partitions()

    # Print header
    if not args.no_headers:
        timestamp = datetime.now().strftime('%c')
        print(
            f"Partition statistics for cluster {mycluster} at {timestamp}"
        )

    # Get pending jobs
    pending_resources, pending_other = get_pending_jobs(
        args.federation, args.partition_list
    )

    # Parse sinfo output
    partitions = parse_sinfo_output(args, mycluster, hidden_partitions)

    # Print statistics
    print_partition_stats(partitions, pending_resources, pending_other, args)


if __name__ == "__main__":
    main()
