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
slurm-cli update jobs 12345 timelimit=2-00:00:00

# Update priority
slurm-cli update jobs 12345 priority=100

# Update partition
slurm-cli update jobs 12345 partition=cpu

# Update with filter (update all matching jobs)
slurm-cli update jobs user=john timelimit=1:00:00
```

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

