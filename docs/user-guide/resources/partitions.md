# Partitions

Manage Slurm partitions (also known as queues).

## Show Partitions

```bash
# Show all partitions
slurm-cli show partitions

# Show specific partition
slurm-cli show partitions gpu

# JSON output
slurm-cli show partitions --json

# CSV output
slurm-cli show partitions --csv
```

## Update Partitions

```bash
# Update partition state
slurm-cli modify partitions gpu set state=UP

# Update time limit
slurm-cli modify partitions batch set defaulttime=4:00:00
```

## Available Fields

| Field | Description |
|-------|-------------|
| `name` | Partition name |
| `state` | Partition state (UP, DOWN, DRAIN, INACTIVE) |
| `nodes` | Number of nodes |
| `cpus` | Total CPUs |
| `memory` | Total memory |
| `timelimit` | Default time limit |
| `maxtime` | Maximum time limit |
| `default` | Is default partition |
| `root_only` | Root only access |
| `priority` | Partition priority |

## Examples

### Show Partition Statistics

```bash
slurm-cli show partitions --profile-str='partitions.columns=name,state,nodes,cpus,memory'
```

### Filter by State

```bash
slurm-cli show partitions state=UP
```

### Detailed View

```bash
slurm-cli show partitions --profile-str='*'
```

## Node Filter Syntax

When specifying nodes for partitions, you can use filter syntax:

```bash
# Update partition to include nodes from another partition
slurm-cli update partitions backup nodes=partition=gpu

# Set partition nodes to currently idle nodes
slurm-cli update partitions test nodes=state=idle
```

Available filters:

| Filter | Example | Description |
|--------|---------|-------------|
| `partition=` | `nodes=partition=gpu` | All nodes from partition |
| `state=` | `nodes=state=idle` | Nodes with specific state |
| `user=` | `nodes=user=john` | Nodes running user's jobs |
| `reservation=` | `nodes=reservation=maint` | Nodes in a reservation |

## Related Commands

- [Nodes](nodes.md) - View nodes in partitions
- [Reservations](reservations.md) - Create reservations on partitions

