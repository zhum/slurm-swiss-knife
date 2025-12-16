# Filtering & Formatting

Slurm CLI provides powerful filtering and formatting capabilities for all resources.

## Filtering Resources

### Basic Filtering

Filter resources by specifying `key=value` pairs:

```bash
# Filter users by default account
slurm-cli show users defaultaccount=myaccount

# Filter accounts by organization
slurm-cli show accounts organization=nvidia

# Filter QoS by priority
slurm-cli show qos priority=100
```

### Multiple Filters

Combine multiple filters (AND logic):

```bash
slurm-cli show users defaultaccount=myaccount adminlevel=Admin
```

### Filter by Name

The first positional argument filters by name:

```bash
# Show specific partition
slurm-cli show partitions gpu

# Show specific user
slurm-cli show users testuser

# Show specific QoS
slurm-cli show qos normal
```

### Filter Aliases

Some fields have convenient aliases:

| Alias | Actual Field |
|-------|--------------|
| `user` | `name` (for users) |
| `username` | `name` (for users) |
| `account` | `default.account` (for users) |
| `defaultaccount` | `default.account` (for users) |
| `admin` | `administrator_level` (for users) |
| `adminlevel` | `administrator_level` (for users) |

```bash
# These are equivalent:
slurm-cli show users defaultaccount=myaccount
slurm-cli show users account=myaccount
```

## Output Formats

### Pretty Table (Default)

Formatted table with colors and borders:

```bash
slurm-cli show partitions
```

### JSON Output

Machine-readable JSON format:

```bash
slurm-cli show partitions --json
```

### CSV Output

CSV format for spreadsheets and scripts:

```bash
slurm-cli show partitions --csv
```

### Custom CSV Delimiter

```bash
slurm-cli show partitions --csv --delimiter='|'
slurm-cli show partitions --csv --delimiter=$'\t'  # Tab
```

## Display Options

### Zebra Striping

Alternate row colors for readability:

```bash
slurm-cli show partitions --zebra
```

### Force Cache Update

Refresh cached data before display:

```bash
slurm-cli show users --force-cache-update
```

### Verbose Mode

Show additional information:

```bash
slurm-cli show partitions --verbose
```

## Column Selection

### Show Specific Columns

```bash
slurm-cli show users --profile-str='users.columns=name,adminlevel'
```

### Show All Columns

```bash
slurm-cli show users --profile-str='*'
```

### Column Order

Columns appear in the order specified:

```bash
# Puts adminlevel first
slurm-cli show users --profile-str='users.columns=adminlevel,name,default.account'
```

## Combining Options

Mix and match options:

```bash
# JSON output with filtering
slurm-cli show users defaultaccount=myaccount --json

# CSV with specific columns
slurm-cli show users --csv --profile-str='users.columns=name,adminlevel'

# Filtered pretty output with zebra
slurm-cli show qos priority=100 --zebra
```

## Pipeline Examples

### With jq

```bash
# Extract user names
slurm-cli show users --json | jq '.users[].name'

# Filter with jq
slurm-cli show qos --json | jq '.qos[] | select(.priority.number > 50)'
```

### With awk/sed

```bash
# Process CSV output
slurm-cli show partitions --csv | awk -F';' '{print $1, $3}'

# Count users
slurm-cli show users --csv | wc -l
```

### With grep

```bash
# Find specific entries
slurm-cli show users --csv | grep admin
```

## Scripting Examples

### Bash Script

```bash
#!/bin/bash
# Get all admin users

slurm-cli show users --json | jq -r '
  .users[] | 
  select(.administrator_level == "Admin") | 
  .name
'
```

### Python Script

```python
import subprocess
import json

result = subprocess.run(
    ["slurm-cli", "show", "qos", "--json"],
    capture_output=True,
    text=True
)
data = json.loads(result.stdout)

for qos in data["qos"]:
    print(f"{qos['name']}: priority={qos.get('priority', {}).get('number', 'N/A')}")
```

## Performance Tips

1. **Use filters** - Filtering server-side is faster than downloading all data
2. **Use JSON** - JSON is faster to parse for scripts than CSV
3. **Cache wisely** - Avoid `--force-cache-update` in loops
4. **Select columns** - Request only needed columns with `--profile-str`

