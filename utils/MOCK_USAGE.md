# SLURM Mock System - Quick Start Guide

This guide explains how to use the SLURM mock system for testing without a real cluster.

## Overview

The mock system consists of:
1. **Recording Script** - Captures real SLURM command outputs
2. **Mock Scripts** - Simulate SLURM commands using recorded data
3. **Mock Data Files** - Stored outputs from real SLURM commands

## Quick Start

### 1. Record Data from a Real Cluster

Run this on a machine with access to a real SLURM cluster:

```bash
./utils/record_slurm_outputs.sh
```

This will create/update files in the `mocks/` directory with real SLURM outputs.

### 2. Use Mock Commands

#### Option A: Add to PATH (Recommended)

```bash
# Add mocks directory to PATH
export PATH="/path/to/slurm-cli/mocks:$PATH"

# Now use SLURM commands normally
scontrol show nodes --json
sacctmgr show qos --json
squeue --all
sinfo
```

#### Option B: Direct Execution

```bash
# Run mock scripts directly from mocks directory
./mocks/scontrol show partitions
./mocks/sacctmgr show qos --json
./mocks/squeue --all
./mocks/sinfo --json
```

## Supported Commands

### scontrol

```bash
# Nodes
./mocks/scontrol show nodes          # Text format
./mocks/scontrol show nodes --json   # JSON format
./mocks/scontrol show node --json    # Also works (singular)

# Partitions
./mocks/scontrol show partitions
./mocks/scontrol show partitions --json

# Reservations
./mocks/scontrol show reservations
./mocks/scontrol show reservations --json

# Config
./mocks/scontrol show config
```

### sacctmgr

```bash
# QoS
./mocks/sacctmgr show qos
./mocks/sacctmgr show qos --json
./mocks/sacctmgr show qos format=name,priority

# Accounts
./mocks/sacctmgr show accounts
./mocks/sacctmgr show accounts --json

# Users
./mocks/sacctmgr show users
./mocks/sacctmgr show users --json
```

### squeue

```bash
# All jobs
./mocks/squeue --all                          # Default format
./mocks/squeue --all --json                   # JSON format

# Active jobs
./mocks/squeue --states=PENDING,RUNNING       # Filter by state

# Extended format
./mocks/squeue -O JobID,Partition,Name,User   # Custom columns
```

### sinfo

```bash
# Cluster information
./mocks/sinfo                    # Text format
./mocks/sinfo --json            # JSON format
```

## Examples

### Testing Your SLURM CLI Tool

```bash
# Set up environment
export PATH="$(pwd)/mocks:$PATH"

# Test with mock data
slurm-cli nodes list
slurm-cli partitions show
slurm-cli qos list
```

### Using in Tests

```python
import subprocess
import os

# Add mocks to PATH
project_dir = "/path/to/slurm-cli"
os.environ["PATH"] = f"{project_dir}/mocks:{os.environ['PATH']}"

# Run command - will use mock
result = subprocess.run(
    ["scontrol", "show", "nodes", "--json"],
    capture_output=True,
    text=True
)

# Parse and test
data = json.loads(result.stdout)
assert "nodes" in data
```

### CI/CD Integration

```yaml
# .github/workflows/test.yml
- name: Test with mock SLURM
  run: |
    export PATH="${PWD}/mocks:${PATH}"
    pytest tests/
```

## Updating Mock Data

### When to Update

- SLURM version upgrade
- Cluster configuration changes
- New features require additional data
- Test data becomes outdated

### How to Update

1. Run recording script on updated cluster:

   ```bash
   ./utils/record_slurm_outputs.sh
   ```

1. Review changes:

    ```bash
    git diff mocks/
    ```

1. Sanitize sensitive information if needed

1. Commit updated files:

```bash
git add mocks/
git commit -m "Update mock SLURM data"
```

## Customizing Mock Behavior

### Add Delay to Simulate Real Commands

Edit the mock scripts and uncomment the sleep line:

```bash
# In scontrol, sacctmgr, squeue, or sinfo
# sleep 0.1  # Uncomment this line
sleep 0.1    # Like this
```

### Add New Commands

1. Update recording script (`utils/record_slurm_outputs.sh`):

   ```bash
   run_and_save \
       "scontrol show licenses" \
       "$MOCKS_DIR/licenses.json" \
       "Licenses (JSON format)"
   ```

1. Update corresponding mock script:

   ```bash
   # In scontrol script
   elif [ "$1" = "show" ] && [ "$2" = "licenses" ]; then
       if [ -f "$MOCKS_DIR/licenses.json" ]; then
           cat "$MOCKS_DIR/licenses.json"
       else
           echo "Error: licenses.json not found" >&2
           exit 1
       fi
   ```

1. Record new data and test

## Troubleshooting

### Error: File not found in mocks/

**Problem**: Mock data file is missing

**Solution**:

```bash
# Option 1: Record from real cluster
./utils/record_slurm_outputs.sh

# Option 2: Create minimal test file
echo '{"nodes":[]}' > mocks/nodes.json
```

### Commands not using mocks

**Problem**: Real SLURM commands are being executed instead of mocks

**Solution**:

```bash
# Check PATH
echo $PATH

# Ensure mocks directory is first in PATH
export PATH="/path/to/slurm-cli/mocks:$PATH"

# Verify which command is being used
which scontrol  # Should show project/mocks path
```

### Mock data is outdated

**Problem**: Tests fail due to schema changes

**Solution**:

```bash
# Re-record from updated cluster
./utils/record_slurm_outputs.sh

# Or manually update JSON structure in mocks/
```

## Tips & Best Practices

1. **Version Control**: Commit mock data files to git
2. **Sanitization**: Remove sensitive info before committing
3. **Documentation**: Add comments to custom mock files
4. **Testing**: Test both recording and playback regularly
5. **Minimal Data**: Keep mock files as small as practical
6. **Multiple Datasets**: Consider different mocks for different test scenarios

## Advanced Usage

### Multiple Mock Environments

```bash
# Create multiple mock directories
mocks/
├── small-cluster/
├── large-cluster/
└── gpu-cluster/

# Switch between them
ln -sf mocks/gpu-cluster mocks-current
# Update mock scripts to use mocks-current
```

### Conditional Mocking

```bash
# Use real commands if available, fallback to mocks
if command -v /usr/bin/scontrol &> /dev/null; then
    /usr/bin/scontrol "$@"
else
    ./mocks/scontrol "$@"  # Use mock
fi
```

## See Also

- [Mock Data README](../mocks/README.md) - Detailed mock data documentation
- [Recording Script](record_slurm_outputs.sh) - Source code for recording
- Main README.md - Project documentation
