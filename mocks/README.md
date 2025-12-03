# SLURM Mock Data

This directory contains mock data files for testing SLURM commands without access to a real cluster.

## Directory Structure

```
mocks/
├── README.md           # This file
├── nodes.json          # Node information (JSON format)
├── nodes               # Node information (text format)
├── partitions.json     # Partition information (JSON format)
├── partitions          # Partition information (text format)
├── reservations.json   # Reservation information (JSON format)
├── reservations        # Reservation information (text format)
├── qos.json            # QoS information (JSON format)
├── qos                 # QoS information (text format)
├── accounts.json       # Account information (JSON format)
├── accounts            # Account information (text format)
├── users.json          # User information (JSON format)
├── users               # User information (text format)
├── squeue.json         # Queue jobs (JSON format)
├── squeue_all          # All jobs (text format)
├── squeue_active       # Active jobs only (text format)
├── squeue_extended     # Extended job info (text format)
├── sinfo.json          # Cluster info (JSON format)
├── sinfo               # Cluster info (text format)
└── slurm_config        # SLURM configuration
```

## Recording Mock Data

To record real SLURM command outputs from a cluster, use the recording script:

```bash
# On a real SLURM cluster
./utils/record_slurm_outputs.sh
```

This script will:
1. Run various SLURM commands (scontrol, sacctmgr, squeue, sinfo)
2. Save the outputs to the `mocks/` directory
3. Support both JSON and text formats

### Commands Recorded

| Command | Output File | Description |
|---------|-------------|-------------|
| `scontrol show partitions` | `partitions` | Partition info (text) |
| `scontrol show partitions --json` | `partitions.json` | Partition info (JSON) |
| `scontrol show nodes` | `nodes` | Node info (text) |
| `scontrol show nodes --json` | `nodes.json` | Node info (JSON) |
| `scontrol show reservations` | `reservations` | Reservation info (text) |
| `scontrol show reservations --json` | `reservations.json` | Reservation info (JSON) |
| `scontrol show config` | `slurm_config` | SLURM configuration |
| `sacctmgr show qos --json` | `qos.json` | QoS info (JSON) |
| `sacctmgr show qos format=...` | `qos` | QoS info (text) |
| `sacctmgr show accounts --json` | `accounts.json` | Account info (JSON) |
| `sacctmgr show accounts format=...` | `accounts` | Account info (text) |
| `sacctmgr show users --json` | `users.json` | User info (JSON) |
| `sacctmgr show users format=...` | `users` | User info (text) |
| `squeue --all --json` | `squeue.json` | All jobs (JSON) |
| `squeue --all --format=...` | `squeue_all` | All jobs (text) |
| `squeue --states=PENDING,RUNNING,...` | `squeue_active` | Active jobs (text) |
| `squeue -O ...` | `squeue_extended` | Extended format (text) |
| `sinfo` | `sinfo` | Cluster info (text) |
| `sinfo --json` | `sinfo.json` | Cluster info (JSON) |

## Using Mock Commands

The project includes mock scripts in this directory that read from these files:

- `scontrol` - Mock scontrol command
- `sacctmgr` - Mock sacctmgr command
- `squeue` - Mock squeue command
- `sinfo` - Mock sinfo command

### Setting Up Mock Environment

To use the mock commands instead of real SLURM commands:

```bash
# Add the mocks directory to your PATH
export PATH="/path/to/slurm-swiss-knife/mocks:$PATH"

# Now SLURM commands will use the mock scripts
scontrol show nodes --json
sacctmgr show qos --json
squeue --all
sinfo
```

### Examples

```bash
# From project root directory:

# Show nodes (JSON format)
./mocks/scontrol show nodes --json

# Show partitions (text format)
./mocks/scontrol show partitions

# Show QoS (JSON format)
./mocks/sacctmgr show qos --json

# Show all jobs
./mocks/squeue --all

# Show cluster info
./mocks/sinfo

# Or from within the mocks directory:
cd mocks
./scontrol show nodes --json
./sacctmgr show qos --json
```

## Data Sanitization

⚠️ **Important**: Before committing mock data to version control, review and sanitize:

1. **User Information**: Remove or anonymize usernames and personal information
2. **Account Names**: Anonymize sensitive account names
3. **Node Names**: Consider anonymizing hostnames if they reveal sensitive infrastructure
4. **Resource Limits**: Review if resource allocations are sensitive
5. **Job Details**: Remove or anonymize job names and scripts

## Updating Mock Data

When SLURM is updated or your cluster configuration changes:

1. Run the recording script on the updated cluster
2. Review the changes to mock files
3. Sanitize sensitive information
4. Test with the mock commands
5. Commit the updated files

## File Formats

### JSON Files
- Used by SLURM commands with `--json` flag
- Structured data, easier to parse
- Recommended for programmatic access

### Text Files
- Traditional SLURM command output
- Human-readable format
- Used for compatibility with tools expecting text output

## Troubleshooting

### Missing Files

If you get an error about missing mock files:

```
Error: nodes.json file not found in mocks/
```

Either:
1. Run `./utils/record_slurm_outputs.sh` on a real cluster
2. Create minimal test data files manually
3. Copy example data from another environment

### Outdated Data

Mock data may become outdated. Signs include:
- Test failures due to schema changes
- Missing fields in JSON output
- Deprecated command options

Solution: Re-record data from an updated SLURM cluster.

## Testing

Use mock data for:
- Unit tests
- Integration tests
- Development without cluster access
- CI/CD pipelines
- Documentation examples

## Contributing

When adding new SLURM commands:
1. Add recording logic to `utils/record_slurm_outputs.sh`
2. Create corresponding mock script (e.g., `snewcommand`)
3. Add mock file names to this README
4. Test both recording and playback

