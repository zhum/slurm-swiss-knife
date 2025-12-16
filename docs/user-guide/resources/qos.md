# Quality of Service (QoS)

Manage Slurm Quality of Service settings.

## Show QoS

```bash
# Show all QoS
slurm-cli show qos

# Show specific QoS
slurm-cli show qos normal

# Filter by priority
slurm-cli show qos priority=100

# JSON output
slurm-cli show qos --json
```

## Create QoS

```bash
# Basic QoS creation
slurm-cli create qos highprio priority=100

# With limits
slurm-cli create qos limited \
    priority=50 \
    maxwall=24:00:00 \
    maxjobspu=10 \
    maxtrespu=cpu=100

# With flags
slurm-cli create qos nodelay flags=NoDecay

# With preemption
slurm-cli create qos preemptive \
    priority=200 \
    preemptmode=SUSPEND \
    preempt=normal,low
```

## Update QoS

### Simple Mode (by name)

```bash
# Update priority
slurm-cli modify qos normal set priority=50

# Update wall time limit
slurm-cli modify qos batch set maxwall=48:00:00

# Update preempt mode
slurm-cli modify qos highprio set preemptmode=CANCEL

# Multiple fields
slurm-cli modify qos normal set priority=100 maxwall=24:00:00 flags=NoDecay
```

### WHERE/SET Mode (bulk update)

```bash
# Update by priority
slurm-cli modify qos priority=0 set priority=10

# Update by flags
slurm-cli modify qos flags=NoDecay set usagefactor=2.0
```

## Delete QoS

```bash
# Delete with confirmation
slurm-cli delete qos oldqos

# Delete without confirmation
slurm-cli delete qos oldqos --yes
```

## Available Fields

| Field | Description |
|-------|-------------|
| `name` | QoS name |
| `id` | QoS ID |
| `description` | QoS description |
| `priority` | Priority value |
| `usage_factor` | Usage factor (default: 1.0) |
| `usage_threshold` | Usage threshold |
| `grace_time` | Grace time (seconds) |
| `flags` | QoS flags |
| `preempt_mode` | Preemption mode |
| `preempt_list` | QoS names that can be preempted |
| `max_wall` | Max wall time per job |
| `max_jobs_per_user` | Max running jobs per user |
| `max_jobs_per_account` | Max running jobs per account |
| `max_submit_jobs_per_user` | Max submitted jobs per user |
| `max_tres_per_job` | Max TRES per job |
| `max_tres_per_user` | Max TRES per user |
| `grp_jobs` | Max running jobs for all users |
| `grp_tres` | Max TRES for all users |

## QoS Flags

| Flag | Description |
|------|-------------|
| `DenyOnLimit` | Deny job if it would exceed limits |
| `EnforceUsageThreshold` | Enforce usage threshold |
| `NoDecay` | Disable fair share decay |
| `NoReserve` | Don't reserve resources |
| `OverPartQOS` | Override partition QoS |
| `PartitionMaxNodes` | Use partition max nodes |
| `PartitionMinNodes` | Use partition min nodes |
| `PartitionTimeLimit` | Use partition time limit |
| `RequiresReservation` | Requires reservation |
| `UsageFactorSafe` | Safe usage factor |

## Preempt Modes

| Mode | Description |
|------|-------------|
| `OFF` | No preemption |
| `CANCEL` | Cancel preempted jobs |
| `GANG` | Gang scheduling |
| `REQUEUE` | Requeue preempted jobs |
| `SUSPEND` | Suspend preempted jobs |
| `WITHIN` | Preempt within QoS |

## Examples

### Create Priority Tiers

```bash
# Low priority
slurm-cli create qos low priority=10 maxwall=168:00:00

# Normal priority
slurm-cli create qos normal priority=50 maxwall=72:00:00

# High priority (can preempt normal)
slurm-cli create qos high priority=100 maxwall=24:00:00 preemptmode=SUSPEND preempt=normal,low
```

### Set Resource Limits

```bash
slurm-cli modify qos normal set \
    maxjobspu=20 \
    maxtrespu=cpu=200,mem=800G,gres/gpu=8 \
    maxsubmitjobspu=50
```

### View QoS Details

```bash
slurm-cli show qos --profile-str='qos.columns=name,priority,max_wall,max_jobs_per_user,flags'
```

### Export QoS Configuration

```bash
slurm-cli show qos --json > qos_backup.json
```

## Related Commands

- [Accounts](accounts.md) - Accounts with QoS
- [Users](users.md) - Users with QoS
- [Associations](associations.md) - QoS in associations

