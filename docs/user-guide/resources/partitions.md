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
slurm-cli modify partitions gpu state=UP

# Update time limit
slurm-cli modify partitions batch defaulttime=4:00:00

# Set nodes for a partition
slurm-cli update partitions gpu nodes=node001,node002

# Add nodes to a partition
slurm-cli update partitions gpu nodes+=node003,node004

# Remove nodes from a partition
slurm-cli update partitions gpu nodes-=node001

# Add nodes using filter
slurm-cli update partitions gpu nodes+=state=idle
```

## Available Fields

| Field | Description |
|-------|-------------|
| `partitionname` | Partition name |
| `state` | Partition state (UP, DOWN, DRAIN, INACTIVE) |
| `nodes` | Node list |
| `totalnodes` | Total nodes in partition |
| `totalcpus` | Total CPUs in partition |
| `maxtime` | Maximum time limit |
| `defaulttime` | Default time limit |
| `default` | Is default partition |
| `allowgroups` | Allowed groups |
| `allowaccounts` | Allowed accounts |
| `allowqos` | Allowed QoS |
| `denyaccounts` | Denied accounts |
| `denyqos` | Denied QoS |
| `maxnodes` | Max nodes per job |
| `minnodes` | Min nodes per job |
| `prioritytier` | Priority tier |

## Update Options

All options are lowercase and support autocompletion.

### Basic Options

| Option | Type | Description |
|--------|------|-------------|
| `state` | up/down/drain/inactive | Partition state |
| `default` | yes/no | Is default partition |
| `defaulttime` | time | Default time limit for jobs |
| `maxtime` | time | Maximum time limit |
| `nodes` | nodelist | Nodes in partition |
| `allocnodes` | nodelist | Nodes that can allocate |
| `alternate` | partition | Alternate partition when drained |

### Resource Limits

| Option | Type | Description |
|--------|------|-------------|
| `maxnodes` | count | Max nodes per job |
| `minnodes` | count | Min nodes per job |
| `maxcpuspernode` | count | Max CPUs per node |
| `maxcpuspersocket` | count | Max CPUs per socket |
| `defmempercpu` | MB | Default memory per CPU |
| `defmempernode` | MB | Default memory per node |
| `maxmempercpu` | MB | Max memory per CPU |
| `maxmempernode` | MB | Max memory per node |
| `overtimelimit` | count | Minutes over time limit allowed |

### Access Control

| Option | Type | Description |
|--------|------|-------------|
| `allowaccounts` | account list | Allowed accounts |
| `denyaccounts` | account list | Denied accounts |
| `allowgroups` | group list | Allowed groups |
| `allowqos` | QoS list | Allowed QoS |
| `denyqos` | QoS list | Denied QoS |
| `qos` | QoS name | Partition QoS |

### Priority and Preemption

| Option | Type | Description |
|--------|------|-------------|
| `prioritytier` | count | Priority tier |
| `priorityjobfactor` | count | Job priority factor |
| `preemptmode` | off/cancel/requeue/suspend | Preemption mode |
| `gracetime` | time | Preemption grace time |

### Flags

| Option | Type | Description |
|--------|------|-------------|
| `disablerootjobs` | yes/no | Disable root jobs |
| `exclusiveuser` | yes/no | Exclusive user allocation |
| `hidden` | yes/no | Hide partition from view |
| `lln` | yes/no | Least loaded node scheduling |
| `oversubscribe` | yes/no | Allow CPU sharing |
| `powerdownonidle` | yes/no | Power down idle nodes |
| `reqresv` | yes/no | Require reservation |
| `rootonly` | yes/no | Root only access |
| `shared` | yes/no | Allow sharing (deprecated) |

### Other Options

| Option | Type | Description |
|--------|------|-------------|
| `cpubind` | none/socket/ldom/core/thread/off | Default task binding |
| `jobdefaults` | specs | Job default values |
| `tresbillingweights` | TRES weights | Billing weights |

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

