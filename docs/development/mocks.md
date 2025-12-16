# Mock System

Slurm CLI includes a mock system for testing without a real Slurm cluster.

## Overview

The mock system provides fake implementations of Slurm commands:

- `sacctmgr` - Account management
- `scontrol` - Cluster control
- `squeue` - Job queue
- `sinfo` - Cluster info

## Quick Start

### Using Mocks

```bash
# Add mocks to PATH
export PATH=$PATH:./mocks

# Now slurm-cli uses mock commands
slurm-cli show partitions
slurm-cli show users --json
```

### Testing with Mocks

```bash
# Run command with mocks
PATH=$PATH:./mocks ./slurm-cli show qos

# Run tests with mocks
PATH=$PATH:./mocks poetry run pytest
```

## Mock Commands

### sacctmgr

Handles account-related commands:

```bash
# Show commands (return mock data)
sacctmgr show qos --json
sacctmgr show accounts
sacctmgr show users --json

# Modify commands (print and succeed)
sacctmgr -i create user name=test
sacctmgr -i modify qos where name=test set priority=100
sacctmgr -i delete user name=test
```

### scontrol

Handles cluster control:

```bash
# Show commands
scontrol show partitions --json
scontrol show nodes --json
scontrol show reservations --json

# Modify commands
scontrol update partitionname=gpu state=UP
scontrol create reservation ...
```

### squeue

Job queue information:

```bash
squeue --json
squeue -u testuser
```

### sinfo

Cluster information:

```bash
sinfo --json
sinfo -p gpu
```

## Mock Data

### Data Location

Mock data files are in `mocks/data/`:

```
mocks/data/
├── accounts.json       # Account data (JSON)
├── accounts            # Account data (text)
├── users.json          # User data
├── qos.json           # QoS data
├── partitions.json    # Partition data
├── nodes.json         # Node data
├── reservations.json  # Reservation data
├── associations.json  # Association data
├── events             # Event data (text)
└── squeue.json        # Job queue data
```

### JSON Format

Mock JSON follows Slurm's JSON output format:

```json
{
  "users": [
    {
      "name": "testuser",
      "administrator_level": "None",
      "default": {
        "account": "myaccount",
        "wckey": ""
      }
    }
  ]
}
```

### Text Format

Some commands use text format:

```
Name|Org|Desc
account1|org1|Description 1
account2|org2|Description 2
```

## Creating Mock Data

### From Real Cluster

Use the recording script:

```bash
# Record real Slurm outputs
./utils/record_slurm_outputs.sh

# Outputs saved to mocks/data/
```

### Manually

Create or edit files in `mocks/data/`:

```bash
# Edit user data
vim mocks/data/users.json
```

### Example: Add Test User

```json
{
  "users": [
    {
      "name": "testuser",
      "administrator_level": "Admin",
      "default": {
        "account": "testaccount",
        "wckey": ""
      },
      "associations": [
        {
          "account": "testaccount",
          "cluster": "testcluster"
        }
      ]
    }
  ]
}
```

## Mock Behavior

### Show Commands

Return data from `mocks/data/`:

```bash
$ sacctmgr show users --json
# Returns contents of mocks/data/users.json
```

### Create/Update/Delete Commands

Print command and succeed:

```bash
$ sacctmgr -i create user name=newuser account=test
MOCK: sacctmgr -i create user name=newuser account=test
# Exit code: 0
```

### Error Handling

Unknown commands show usage:

```bash
$ sacctmgr unknown command
Usage: sacctmgr {show|create|modify|delete} {qos|accounts|users|...}
This is a mock sacctmgr script for testing purposes.
```

## Customizing Mocks

### Adding New Data

1. Create data file in `mocks/data/`
2. Update mock script to serve it:

```bash
# In mocks/sacctmgr:
elif [ "$CMD" = "show" ] && [ "$RESOURCE" = "newresource" ]; then
    if [[ "$*" == *"--json"* ]]; then
        cat "$MOCKS_DIR/data/newresource.json"
    else
        cat "$MOCKS_DIR/data/newresource"
    fi
fi
```

### Simulating Errors

Return non-zero exit code:

```bash
# In mock script:
elif [ "$SOME_CONDITION" ]; then
    echo "Error: Resource not found" >&2
    exit 1
fi
```

## CI/CD Integration

### GitHub Actions

```yaml
jobs:
  test:
    steps:
      - uses: actions/checkout@v3
      - name: Run tests with mocks
        run: |
          export PATH=$PATH:./mocks
          poetry run pytest
```

### Local CI

```bash
# Run full test suite with mocks
PATH=$PATH:./mocks make check
```

## Troubleshooting

### Mock Not Found

```bash
# Check mock is executable
ls -la mocks/sacctmgr

# Make executable
chmod +x mocks/*
```

### Wrong Data Returned

```bash
# Verify data file exists
cat mocks/data/users.json

# Check mock script logic
cat mocks/sacctmgr
```

### PATH Issues

```bash
# Verify mocks in PATH
which sacctmgr
# Should show: ./mocks/sacctmgr

# Full path approach
PATH=$(pwd)/mocks:$PATH slurm-cli show users
```

## Related

- [Testing Guide](testing.md) - Writing tests
- [Contributing](contributing.md) - Development workflow

