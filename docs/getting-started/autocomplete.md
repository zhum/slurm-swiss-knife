# Autocomplete Setup

Slurm CLI provides intelligent tab completion for commands, resources, and options.

## Quick Setup

### Method 1: Eval (Recommended for Testing)

Add to your shell session:

```bash
eval "$(slurm-cli autocomplete)"
```

### Method 2: Permanent Installation

Add to your `~/.bashrc` or `~/.bash_profile`:

```bash
# Add this line
eval "$(slurm-cli autocomplete)"
```

Then reload:

```bash
source ~/.bashrc
```

### Method 3: Completion Script File

Generate and save the completion script:

```bash
slurm-cli autocomplete > ~/.local/share/bash-completion/completions/slurm-cli
```

## Using Autocomplete

### Command Completion

```bash
slurm-cli sh<TAB>
# Completes to: show

slurm-cli show p<TAB>
# Shows: partitions
```

### Resource Completion

```bash
slurm-cli show <TAB>
# Shows: partitions nodes users qos accounts reservations ...
```

### Option Completion

```bash
slurm-cli show partitions --<TAB>
# Shows: --json --csv --profile --delimiter ...
```

### Field Completion for Create/Update

```bash
slurm-cli create qos myqos <TAB>
# Shows: priority= maxwall= flags= preemptmode= ...

slurm-cli modify users testuser set admin<TAB>
# Completes to: adminlevel=

slurm-cli modify users testuser set adminlevel=<TAB>
# Shows: None Admin Operator
```

### Value Completion from Cache

The CLI caches resource data for faster completion:

```bash
# First, populate the cache
slurm-cli show users

# Now completions use cached data
slurm-cli show users user=<TAB>
# Shows: user1 user2 user3 ...

slurm-cli show users defaultaccount=<TAB>
# Shows: account1 account2 ...
```

## Cache Locations

Completion data is cached in `/tmp/`:

| Cache File | Content |
|------------|---------|
| `/tmp/slurm_cli_users.json` | User data |
| `/tmp/slurm_cli_accounts.json` | Account data |
| `/tmp/slurm_cli_partitions.json` | Partition data |
| `/tmp/slurm_cli_qos.json` | QoS data |
| `/tmp/slurm_cli_jobs.json` | Job data |
| `/tmp/slurm_cli_nodes.json` | Node data |
| `/tmp/slurm_cli_reservations.json` | Reservation data |

## Automatic Cache Updates

The autocomplete system automatically updates cache when:

1. Cache file is missing
1. Cache file is older than 60 seconds

This ensures completions always show current data without manual refresh.

### Disable Automatic Updates

To disable automatic cache updates during completion (useful for slow networks or when Slurm is unavailable):

```bash
export SLURM_CLI_NO_CACHE_UPDATE=1
```

Accepted values: `1`, `y`, `yes`, `true`

### Force Cache Refresh

To manually refresh cache:

```bash
slurm-cli show users --force-cache-update
```

## Troubleshooting

### Completions Not Working

1. Ensure bash-completion is installed:
   ```bash
   # Debian/Ubuntu
   sudo apt install bash-completion
   
   # RHEL/CentOS
   sudo yum install bash-completion
   ```

2. Verify slurm-cli is in PATH:
   ```bash
   which slurm-cli
   ```

3. Check completion is loaded:
   ```bash
   complete -p slurm-cli
   ```

### Slow Completions

If completions are slow, it may be due to large cached files. Clear the cache:

```bash
rm /tmp/slurm_cli_*.json
```

### Debug Mode

Enable debug output to troubleshoot:

```bash
# View the generated completion script
slurm-cli autocomplete
```

## Zsh Support

While primarily designed for bash, basic completion works in zsh with bash compatibility:

```zsh
# Add to ~/.zshrc
autoload -U +X compinit && compinit
autoload -U +X bashcompinit && bashcompinit
eval "$(slurm-cli autocomplete)"
```

## Next Steps

- [Quick start guide](quickstart.md) to learn basic commands
- [Commands overview](../user-guide/commands.md) for all available commands

