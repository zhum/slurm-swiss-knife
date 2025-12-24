# Jobs

Manage Slurm jobs - view, update, and cancel running or pending jobs.

## Show Jobs

```bash
# Show all jobs
slurm-cli show jobs

# Show specific job
slurm-cli show jobs 12345

# JSON output
slurm-cli show jobs --json

# CSV output
slurm-cli show jobs --csv
```

## Filter Jobs

```bash
# Filter by user
slurm-cli show jobs user=john

# Filter by state
slurm-cli show jobs state=running

# Filter by partition
slurm-cli show jobs partition=gpu

# Filter by account
slurm-cli show jobs account=research

# Filter by reservation
slurm-cli show jobs reservation=maint

# Combine filters
slurm-cli show jobs user=john state=pending partition=gpu
```

## Update Jobs

```bash
# Update time limit
slurm-cli update jobs 12345 TimeLimit=2-00:00:00

# Update priority
slurm-cli update jobs 12345 Priority=100

# Update partition
slurm-cli update jobs 12345 Partition=cpu

# Update account
slurm-cli update jobs 12345 Account=research

# Change node list
slurm-cli update jobs 12345 NodeList=node001,node002

# Update multiple properties
slurm-cli update jobs 12345 Priority=100 TimeLimit=4:00:00

# Update with filter (update all matching jobs)
slurm-cli update jobs user=john TimeLimit=1:00:00
```

### Update Options

#### Time Options

| Option | Format | Example |
|--------|--------|---------|
| `TimeLimit` | `D-HH:MM:SS` or `HH:MM:SS` | `TimeLimit=1-00:00:00` |
| `TimeMin` | `D-HH:MM:SS` or `HH:MM:SS` | `TimeMin=1:00:00` |
| `StartTime` | `YYYY-MM-DDTHH:MM:SS` | `StartTime=2024-01-15T09:00:00` |
| `EndTime` | `YYYY-MM-DDTHH:MM:SS` | `EndTime=2024-01-15T17:00:00` |
| `Deadline` | `YYYY-MM-DDTHH:MM:SS` | `Deadline=2024-01-20T00:00:00` |
| `EligibleTime` | `YYYY-MM-DDTHH:MM:SS` | `EligibleTime=now` |
| `DelayBoot` | seconds | `DelayBoot=60` |

#### Resource Options

| Option | Type | Description |
|--------|------|-------------|
| `NumNodes` | count | Number of nodes |
| `NumCPUs` | count | Number of CPUs |
| `NumTasks` | count | Number of tasks |
| `CPUsPerTask` | count | CPUs per task |
| `TasksPerNode` | count | Tasks per node |
| `MinMemoryNode` | MB | Minimum memory per node |
| `MinMemoryCPU` | MB | Minimum memory per CPU |
| `MinCPUsNode` | count | Minimum CPUs per node |
| `MinTmpDiskNode` | MB | Minimum temp disk per node |
| `Gres` | list | Generic resources (e.g., `gpu:2`) |

#### Node Options

| Option | Type | Description |
|--------|------|-------------|
| `NodeList` | nodes | Specific nodes to use |
| `ExcNodeList` | nodes | Nodes to exclude |
| `ReqNodeList` | nodes | Required nodes |
| `Partition` | name | Target partition |

#### Job Configuration

| Option | Type | Description |
|--------|------|-------------|
| `Priority` | number | Job priority |
| `Nice` | number | Nice value adjustment |
| `Account` | name | Account to charge |
| `QOS` | name | Quality of service |
| `ReservationName` | name | Reservation to use |
| `JobName` | string | Job name |
| `Comment` | string | Job comment |
| `AdminComment` | string | Admin comment |
| `Licenses` | list | Licenses required |
| `Features` | list | Required features |
| `Prefer` | list | Preferred features |
| `Dependency` | spec | Job dependencies |

#### Dependency Types

```bash
# Wait for job to start
slurm-cli update jobs 12345 Dependency=after:67890

# Wait for job to complete successfully
slurm-cli update jobs 12345 Dependency=afterok:67890

# Wait for job to fail
slurm-cli update jobs 12345 Dependency=afternotok:67890

# Wait for any completion
slurm-cli update jobs 12345 Dependency=afterany:67890

# Singleton - only one job with same name
slurm-cli update jobs 12345 Dependency=singleton
```

#### I/O Options

| Option | Type | Description |
|--------|------|-------------|
| `StdIn` | path | Standard input file |
| `StdOut` | path | Standard output file |
| `StdErr` | path | Standard error file |
| `WorkDir` | path | Working directory |

#### Notification Options

| Option | Values | Description |
|--------|--------|-------------|
| `MailUser` | user | Email recipient |
| `MailType` | types | When to email |

Mail types: `NONE`, `BEGIN`, `END`, `FAIL`, `REQUEUE`, `ALL`, `TIME_LIMIT`, `TIME_LIMIT_90`, `TIME_LIMIT_80`, `TIME_LIMIT_50`, `ARRAY_TASKS`

#### Boolean Options

| Option | Values | Description |
|--------|--------|-------------|
| `Contiguous` | yes/no | Require contiguous nodes |
| `Reboot` | yes/no | Reboot nodes before job |
| `Requeue` | 0/1 | Allow requeue on failure |
| `OverSubscribe` | yes/no | Allow oversubscription |
| `Shared` | yes/no | Share nodes with other jobs |

#### Miscellaneous Options

| Option | Type | Description |
|--------|------|-------------|
| `ArrayTaskThrottle` | count | Max concurrent array tasks |
| `CoreSpec` | count | Specialized cores |
| `ThreadSpec` | count | Specialized threads |
| `Switches` | count | Network switches required |
| `WCKey` | key | Workload characterization key |
| `Extra` | string | Extra data |
| `Clusters` | list | Target clusters |
| `ClusterFeatures` | list | Required cluster features |
| `BurstBuffer` | spec | Burst buffer specification |
| `ResetAccrueTime` | (flag) | Reset accrue time |

## Cancel Jobs

```bash
# Cancel a single job
slurm-cli delete jobs 12345

# Cancel multiple jobs
slurm-cli delete jobs 12345 12346 12347

# Cancel all jobs for a user (uses scancel -u)
slurm-cli delete jobs user=john

# Cancel jobs by state
slurm-cli delete jobs state=pending

# Mixed: specific jobs and filter
slurm-cli delete jobs 12345 user=john state=pending
```

### Dry Run

```bash
# Preview what would be cancelled
slurm-cli delete jobs --dry-run user=john state=pending
```

## Available Fields

| Field | Description |
|-------|-------------|
| `job_id` | Job ID number |
| `name` | Job name |
| `user_name` | Owner username |
| `account` | Account charged |
| `partition` | Partition/queue |
| `job_state` | Current state (RUNNING, PENDING, etc.) |
| `start_time` | When job started (or `-` if not started) |
| `end_time` | When job ended (or `-` if not ended) |
| `endlimit` | End time if known, otherwise time limit |
| `time_limit` | Requested time limit |
| `node_count` | Number of nodes |
| `nodes` | Node list |
| `cpus` | Number of CPUs |
| `gres` | Generic resources (GPUs, etc.) |
| `reason` | State reason (for pending jobs) |
| `priority` | Job priority |
| `command` | Command/script path |
| `submit_time` | Submission time |
| `current_working_directory` | Working directory |
| `standard_output` | stdout file path |
| `standard_error` | stderr file path |

## Job States

| State | Description |
|-------|-------------|
| `pending` | Waiting for resources |
| `running` | Currently executing |
| `completed` | Finished successfully |
| `cancelled` | Cancelled by user or admin |
| `failed` | Exited with error |
| `timeout` | Exceeded time limit |
| `node_fail` | Node failure |
| `preempted` | Preempted by higher priority job |
| `suspended` | Temporarily suspended |
| `completing` | Finishing up |

## Output Profiles

```bash
# Default profile
slurm-cli show jobs

# Detailed profile (all fields)
slurm-cli show jobs --profile=detailed

# Compact profile
slurm-cli show jobs --profile=compact

# Custom columns
slurm-cli show jobs --profile-str='jobs.columns=job_id,user_name,partition,job_state,nodes'
```

## Aliases

The jobs resource has these aliases:

1. `jobs` (full name)
1. `job` (singular)
1. `j` (short)

```bash
# All equivalent
slurm-cli show jobs
slurm-cli show job
slurm-cli show j
```

## Related Commands

- [Nodes](nodes.md) - View nodes running jobs
- [Partitions](partitions.md) - Manage partition queues
- [Users](users.md) - Manage user accounts

