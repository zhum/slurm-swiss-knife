# Nodes

Manage Slurm compute nodes.

## Show Nodes

```bash
# Show all nodes
slurm-cli show nodes

# Show specific node
slurm-cli show nodes node001

# JSON output
slurm-cli show nodes --json

# CSV output
slurm-cli show nodes --csv
```

## Update Nodes

```bash
# Set node state
slurm-cli modify nodes node001 set state=DRAIN reason="Maintenance"

# Resume node
slurm-cli modify nodes node001 set state=RESUME
```

## Available Fields

| Field | Description |
|-------|-------------|
| `name` | Node hostname |
| `state` | Node state |
| `cpus` | Number of CPUs |
| `sockets` | Number of sockets |
| `cores` | Cores per socket |
| `threads` | Threads per core |
| `memory` | Real memory (MB) |
| `tmp_disk` | Temporary disk space |
| `weight` | Scheduling weight |
| `features` | Node features |
| `gres` | Generic resources (GPUs, etc.) |
| `partitions` | Assigned partitions |
| `reason` | State reason (if not idle) |
| `boot_time` | Last boot time |

## Node States

| State | Description |
|-------|-------------|
| `IDLE` | Available for jobs |
| `ALLOCATED` | Running jobs |
| `MIXED` | Partially allocated |
| `DRAIN` | Not accepting new jobs |
| `DOWN` | Not available |
| `RESERVED` | Reserved |

## Examples

### Show Node Resources

```bash
slurm-cli show nodes --profile-str='nodes.columns=name,state,cpus,memory,gres'
```

### Filter by State

```bash
slurm-cli show nodes state=IDLE
```

### Show Nodes with GPUs

```bash
slurm-cli show nodes --json | jq '.nodes[] | select(.gres != "")'
```

### Drain a Node

```bash
slurm-cli modify nodes node001 set state=DRAIN reason="Hardware issue"
```

## Related Commands

- [Partitions](partitions.md) - View partitions containing nodes
- [Reservations](reservations.md) - Reserve specific nodes

