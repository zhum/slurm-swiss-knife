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

## Related Commands

- [Nodes](nodes.md) - View nodes in partitions
- [Reservations](reservations.md) - Create reservations on partitions

