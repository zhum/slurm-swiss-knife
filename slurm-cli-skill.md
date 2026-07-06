---
name: slurm-cli
description: Construct correct slurm-cli invocations to query and manage a Slurm cluster (jobs, nodes, partitions, users, qos, accounts, reservations, etc). Use when asked to run slurm-cli, query/filter jobs or nodes, drain/hold/requeue, or format output as json/csv/profile.
---

# slurm-cli usage

`slurm-cli` wraps `scontrol`/`sacctmgr`/`squeue`/`sinfo` behind one CLI:

```
slurm-cli [global opts] <verb> <resource> [filters/args] [subcommand opts]
```

## Verbs (with aliases)

- `show` (ls, list, get) — read
- `update` (set, modify, edit) — modify
- `create` (add, new) — create
- `delete` (remove, rm) — delete
- `write_config` (wconf)

Plus direct action commands (no resource arg needed): `drain`/`undrain`, `reboot`/`cancel-reboot`, `hold`/`release`, `requeue`, `suspend`, `top`, `reconfigure`, `ping`, `takeover`, `daemons`, `token`, `batch-script`, `list-resources`, `autocomplete`, `help`, `version`.

Prefix-matching works: `sho par` → `show partitions`. When unsure of exact syntax for a resource, run `slurm-cli <verb> <resource> --help` rather than guessing.

## Resources (with aliases)

`partitions`(part), `nodes`(node), `jobs`(job/j), `users`(user), `qos`(q), `accounts`(acc), `associations`(assoc), `reservations`(reservation), `coordinators`(coord), `events`(ev). Info-only: `problems`, `stats`, `config`, `license`, `dump`, `topology`.

## Filter syntax

`field=value` filters — **no native `!=`**, exclusion is `not:field=value`.

**Job filters** (show/update/delete jobs, hold/release/requeue/suspend/top): `user=`, `account=`, `partition=`, `state=`, `name=` (exact), `jobname=` (regex), `nodes=`, `reservation=`. A bare number is treated as a job ID. Multiple positive filters union; `not:` exclusions apply after.

**Node filters** (update nodes, drain/undrain, reboot, reservation node lists): `partition=`, `state=`, `user=`, `reservation=`, `drain=`/`drainreason=` (regex), keyword `all`/`ALL`. Multiple positive node filters **AND together** (intersection) — different from job filters. Hostlist ranges (`node[01-10]`, `gpu[01,03-04]`) expand automatically.

Examples:
```
slurm-cli show jobs state=running
slurm-cli delete jobs user=john
slurm-cli hold partition=gpu not:user=admin
slurm-cli hold jobname=test.*
slurm-cli drain drainreason="Not responding"
slurm-cli update nodes state=drain partition=gpu
slurm-cli update reservations test nodes=partition=cpu
```

## Output formats

Global flags precede the verb:

- `--style {pretty,json,csv}` (default `pretty`), or shorthands `-p`/`-j`/`--csv`
- `-d/--delimiter` — CSV delimiter (default `;`)
- `-z/--zebra` — striped rows (pretty)
- `-P/--profile NAME` — named profile from `~/.config/slurm-cli.profiles` (see `slurm-cli.profiles.example`)
- `-o/--profile-str STR` — inline profile override: `resource.columns=col1,col2;resource.styles.field=style`. Column suffix `+`/`-` = asc/desc sort.
- `--list-fields[=RESOURCE]` — discover available columns for a resource

Examples:
```
slurm-cli --json show jobs state=running
slurm-cli --profile compact show accounts
slurm-cli --profile-str "priority-,name" show qos
```

## Caching

Results are cached per-resource in `/tmp/slurm_cli_<resource>.json`, default timeout **600s**.

- `-f/--force-update` — bypass cache, force fresh query
- `-t/--cache-timeout SECONDS` — override timeout

**Important:** after `create`/`update`/`delete`, a following `show` may return stale cached data. Use `--force-update` to confirm the change actually took effect.

## Other flags

- `-y/--yes` — skip confirmation prompts on mutating ops
- `--dry-run` — preview without executing (also via `SLURM_CLI_DRYRUN=y` env var; `--no-dry-run` overrides)
- `-v/--verbose` — debug filter resolution
- `slurm-cli list-resources` — list all resource types
- `slurm-cli <verb> <resource> --help` — canonical per-resource examples
