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

<div class="grid cards" markdown>

-   :material-console:{ .lg .middle } __Unified CLI__

    ---

    Single interface for all Slurm operations: show, create, update, delete

-   :material-format-list-bulleted:{ .lg .middle } __Smart Autocomplete__

    ---

    Context-aware tab completion with fuzzy matching

-   :material-palette:{ .lg .middle } __Customizable Output__

    ---

    Profile-based output formatting with Rich markup support

-   :material-filter:{ .lg .middle } __Powerful Filtering__

    ---

    Filter resources by any field with key=value syntax

</div>

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

## Getting Started

1. [Install Slurm CLI](getting-started/installation.md)
2. [Set up autocomplete](getting-started/autocomplete.md)
3. [Learn the commands](user-guide/commands.md)

## Requirements

- Python 3.9 or higher
- Slurm cluster environment (or use [mock system](development/mocks.md) for testing)
- Bash shell (for autocomplete)

