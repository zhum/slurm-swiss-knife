# Slurm CLI

A powerful command-line interface for Slurm cluster management with intelligent autocomplete functionality.

## Overview

Slurm CLI (`slurm-cli`) is a modern, user-friendly wrapper around Slurm's native commands (`scontrol`, `sacctmgr`, `squeue`, `sinfo`) that provides:

- **Intuitive Commands** - Unified interface for managing all Slurm resources
- **Smart Autocomplete** - Tab completion for commands, resources, and options
- **Rich Output** - Beautifully formatted tables with customizable profiles
- **Filtering** - Powerful filtering capabilities for all resources
- **Multiple Output Formats** - Pretty tables, JSON, and CSV output

## Features

| Feature | Description |
|---------|-------------|
| **Unified CLI** | Single interface for all Slurm operations: show, create, update, delete |
| **Smart Autocomplete** | Context-aware tab completion with fuzzy matching |
| **Customizable Output** | Profile-based output formatting with Rich markup support |
| **Powerful Filtering** | Filter resources by any field with key=value syntax |
| **Node Control** | Drain, reboot, hold, and resume nodes with rich filter expressions |
| **Cluster Diagnostics** | Set debug levels, debug flags, burst buffer info, and topology inspection |

## Quick Example

```bash
# Show all partitions in a pretty table
slurm-cli show partitions

# Show QoS in JSON format
slurm-cli show qos --json

# Create a new account
slurm-cli create accounts myaccount organization=myorg

# Update user admin level
slurm-cli modify users testuser set adminlevel=admin

# Filter accounts by organization
slurm-cli show accounts organization=nvidia
```

## Supported Resources

| Resource | Commands | Description |
|----------|----------|-------------|
| `partitions` | show, update | Slurm partitions/queues |
| `nodes` | show, update | Compute nodes |
| `users` | show, create, update, delete | User accounts |
| `accounts` | show, create, update, delete | Account hierarchy |
| `qos` | show, create, update, delete | Quality of Service |
| `reservations` | show, create, update, delete | Resource reservations |
| `associations` | show, update | User-account associations |
| `coordinators` | show, create, delete | Account coordinators |
| `events` | show | Cluster events |
| `config` | show | Slurm configuration |

## Cluster Control Commands

| Command | Aliases | Description |
|---------|---------|-------------|
| `drain` | `dr` | Drain nodes with node filter support |
| `undrain` | `undr`, `resume` | Undrain/resume nodes |
| `reboot` | `reb` | Reboot nodes |
| `cancel-reboot` | `cancel-reb` | Cancel pending reboot |
| `hold` | `hol` | Hold jobs |
| `release` | `rel` | Release held jobs |
| `requeue` | `req` | Requeue jobs |
| `top` | | Move jobs to top of queue |
| `suspend` | `sus` | Suspend running jobs |
| `setdebug` | `sd` | Set slurmctld/slurmd debug level |
| `setdebugflags` | `sdf` | Enable/disable debug flag categories |
| `schedloglevel` | `sll` | Set scheduler log verbosity |
| `bbstat` | `bbs` | Show burst buffer status |
| `burstbuffer` | | Show burst buffer configuration |
| `daemons` | | Show running Slurm daemons |
| `dwstat` | | Show DataWarp burst buffer status |
| `topology` | | Show network topology |
| `reconfigure` | `reconf` | Force slurmctld to re-read config |
| `ping` | | Ping slurmctld |
| `takeover` | | Trigger backup controller takeover |
| `token` | `tok` | Generate JWT authentication token |
| `write-config` | `wconf` | Write Slurm configuration to file |
| `batch-script` | `bscript` | Show job batch script |

## Getting Started

1. [Install Slurm CLI](getting-started/installation.md)
2. [Set up autocomplete](getting-started/autocomplete.md)
3. [Learn the commands](user-guide/commands.md)

## Requirements

- Python 3.9 or higher
- Slurm cluster environment (or use [mock system](development/mocks.md) for testing)
- Bash shell (for autocomplete)

