# Autocomplete in slurm-cli

## Setup

Generate and source the completion script:

```bash
slurm-cli autocomplete > ~/.local/share/bash-completion/completions/slurm-cli
source ~/.local/share/bash-completion/completions/slurm-cli
```

Or load it on-the-fly for testing:

```bash
source <(slurm-cli autocomplete)
```

The script registers bash completion for both `slurm-cli` and `./slurm-cli` (local binary invocation).

---

## How the Script Is Generated

The completion script is produced entirely at runtime by the `autocomplete` Click command in `cli.py`. Running `slurm-cli autocomplete` prints a self-contained bash script to stdout.

The script is assembled from four sources:

| Source | Produces |
|--------|----------|
| `get_common_autocomplete_functions()` in `autocomplete_helpers.py` | Cache helpers, key=value parser, `_slurm_complete_nodes_value` |
| `generate_bash_command_case()` in `prefix_utils.py` | `case` block that maps typed prefixes/aliases → canonical command names |
| `generate_bash_resource_case()` in `prefix_utils.py` | `case` block that maps typed prefixes/aliases → canonical resource names |
| Inline templates in the `autocomplete()` handler in `cli.py` | Per-command completion logic (what options/values each command accepts) |

The main bash function is named `_slurm_cli_initialize_autocomplete` and is registered with:

```bash
complete -o default -o bashdefault -o nosort -F _slurm_cli_initialize_autocomplete slurm-cli
complete -o default -o bashdefault -o nosort -F _slurm_cli_initialize_autocomplete ./slurm-cli
```

---

## Prefix and Alias Matching

### How it works

Commands and resources can be abbreviated to their shortest unambiguous prefix. For example, `sho` completes to `show`, `par` completes to `partitions`, `set` completes to `setdebug` (or both `setdebug`/`setdebugflags` when ambiguous).

`compute_shortest_unique_prefixes()` in `prefix_utils.py` takes the list of all names (canonical + aliases) and finds the minimum prefix length that uniquely identifies each one. The result is embedded as a bash `case` block:

```bash
case "$cmd" in
    sh*)
        guessed="show"; cmd="show" ;;
    setdebug|sd)
        if [[ "$cur" == "setdebug" ]]; then
            guessed="setdebug setdebugflags"   # ambiguous: show both
        else
            guessed="setdebug"
        fi
        cmd="setdebug" ;;
    setdebugf*|sdf)
        guessed="setdebugflags"; cmd="setdebugflags" ;;
    ...
esac
```

When a command's full name is itself a prefix of another command (e.g., `setdebug` vs `setdebugflags`), typing the exact name shows both as completions. This is detected in `generate_bash_command_case()`.

### Adding commands and aliases

Every command/resource must have an entry in the `COMMANDS` or `RESOURCES` dict in `prefix_utils.py`:

```python
COMMANDS = {
    "setdebug": {
        "aliases": ["sd"],
        "description": "Set slurmctld/slurmd debug level",
    },
    ...
}
```

Aliases are resolved to the canonical name at completion time. The alias must also be registered as a Click command in `register_commands()` in `cli.py`:

```python
main.add_command(setdebug, name="setdebug")
main.add_command(setdebug, name="sd")   # alias
```

---

## Caching

Resource lists (nodes, partitions, users, reservations, accounts, QoS, jobs) are expensive to fetch live on every keypress. The completion script caches them as JSON files in `/tmp/`:

| Cache file | Resource | jq expression used |
|---|---|---|
| `/tmp/slurm_cli_nodes.json` | nodes | `keys[]` |
| `/tmp/slurm_cli_partitions.json` | partitions | `keys[]` |
| `/tmp/slurm_cli_users.json` | users | `.users[].name` |
| `/tmp/slurm_cli_reservations.json` | reservations | `keys[]` |
| `/tmp/slurm_cli_accounts.json` | accounts | `.accounts[].name` |
| `/tmp/slurm_cli_qos.json` | qos | `.qos[].name` |
| `/tmp/slurm_cli_jobs.json` | jobs | `.jobs[].job_id` |

### Cache freshness

`_slurm_ensure_cache FILE RESOURCE` checks the file's mtime. If the file is missing or older than `_SLURM_CACHE_TIMEOUT` seconds (default: 600), it refreshes synchronously by running:

```bash
"${COMP_WORDS[0]}" show RESOURCE --style=json > /dev/null 2>&1
```

`COMP_WORDS[0]` is the binary the user actually invoked (e.g., `./slurm-cli`), so the cache works even when the binary is not on `PATH`. Falls back to `slurm-cli` from PATH if the invoked binary fails.

### Disabling cache updates

Set `SLURM_CLI_NO_CACHE_UPDATE=1` (or `yes`/`true`/`y`) to skip all cache refreshes. Completions will still work using whatever files already exist in `/tmp/`.

---

## Completion Logic: How a TAB Press Is Resolved

When the user presses TAB, bash calls `_slurm_cli_initialize_autocomplete`. The function walks through `COMP_WORDS` to determine:

1. **Global options** (`--style`, `--profile`, `--dry-run`, etc.) — consumed first; their argument values are skipped over.
2. **Command** — the first non-option word. Matched against the prefix `case` block → sets `$cmd` (canonical) and `$guessed`.
3. **Resource** — the next non-option word after the command, used for `show`/`update`/`create`/`delete`.

If the cursor is on the command position, `COMPREPLY` is set to `compgen -W "$guessed" -- "$cur"`. If `$guessed == "no"` (nothing matched), the full command list is offered.

If the cursor is past the command, control falls into a per-command `case "$cmd"` block.

---

## Per-Command Completion

Each command has a dedicated `case` arm in the main function. Representative examples:

### Simple utility commands

```
version, ping, reconfigure, takeover → -v --verbose -h --help
bbstat, burstbuffer, daemons, dwstat, topology → --dry-run -v --verbose -h --help
schedloglevel → 0 1 yes no y n on off --dry-run -v --verbose -h --help
```

### setdebug

Completes a debug level (`quiet fatal error info verbose debug debug2 debug3 debug4 debug5`), then optionally `nodes=` (with node filter support — see below).

### setdebugflags

Completes `+FLAG` or `-FLAG` where FLAG is one of 43 known flags (`Backfill`, `Agent`, `BurstBuffer`, …). Prefix with `+` to enable, `-` to disable:

```
+B[TAB] → +Backfill +BackfillMap +BurstBuffer
-Ag[TAB] → -Agent
```

After flags, optionally `nodes=` with node filter support.

### show / update / create / delete

These commands take a resource name as the second argument, then resource-specific fields. The resource is matched via `generate_bash_resource_case()` in the same way commands are prefix-matched.

After the resource is identified, per-resource completion functions (generated from `RESOURCES` config in `prefix_utils.py`) offer relevant field names and values, using the cache helpers for dynamic values.

### drain / undrain / reboot / cancel-reboot

These take node specifications followed by optional filters. They use the node filter completion system (see below) and offer `reason=`, `-r`/`--reason` for drain/reboot.

---

## Node Filter Completion

Several commands accept nodes specified as either a literal nodelist or a filter expression. Supported filters:

| Filter | Completes to |
|--------|-------------|
| `partition=` | partition names from cache |
| `state=` | `idle alloc drain down mixed comp` |
| `user=` | usernames from cache |
| `reservation=` | reservation names from cache |
| `drain=` | `REGEXP` (hint; user types their own pattern) |
| `drainreason=` | `REGEXP` (hint) |

Negative filters use the `not:` prefix: `not:partition=`, `not:state=`, etc.

### Where node filters appear

**As standalone arguments** (in `drain`, `undrain`, `reboot`, `cancel-reboot`):

```
slurm-cli drain partition=[TAB]  → gpu cpu ...
slurm-cli drain not:state=[TAB] → idle alloc drain down mixed comp
slurm-cli drain drain=[TAB]     → drain=REGEXP
```

**As the value of `nodes=`** (in `setdebug`, `setdebugflags`, `update nodes`):

```
slurm-cli setdebug error nodes=partition=[TAB]  → gpu cpu ...
slurm-cli setdebug error nodes=drain=[TAB]      → nodes=drain=REGEXP
```

### Implementation

Two bash functions handle node filter completion:

- **`_slurm_complete_node_filter cur prev`** — used by standalone-filter commands (`drain` etc.). Generated by `generate_node_filter_autocomplete()` in `node_filter.py`.
- **`_slurm_complete_nodes_value val cur key`** — used when nodes appear as `nodes=VALUE`. Defined in `get_common_autocomplete_functions()` in `autocomplete_helpers.py`.

Both detect the filter type from the prefix of the current word and complete accordingly. Sub-filters (e.g., `nodes=partition=gpu`) are handled by re-parsing after stripping the outer `nodes=` prefix.

---

## The `=` Word-Break Problem

Bash includes `=` in `COMP_WORDBREAKS` by default. This means when the user types `nodes=gpu`, bash may split it into three tokens: `["nodes", "=", "gpu"]`. The cursor could land on `"="` or `"gpu"` depending on context.

The completion code handles both cases via `_slurm_parse_keyval cur prev`:

```bash
_slurm_parse_keyval "$cur" "$prev"
# Sets $_key and $_val regardless of how bash split the tokens:
# cur="nodes=gpu"  → _key="nodes", _val="gpu"
# cur="gpu", prev="=" → _key=COMP_WORDS[COMP_CWORD-2], _val="gpu"
# cur="="  → _key=prev, _val=""
```

For deeply nested filters like `nodes=state=idle`, the code also checks `COMP_WORDS[COMP_CWORD-3]` and `COMP_CWORD-4` to detect when `state`, `partition`, `user`, `reservation`, or `drain` appear after `nodes=`.

---

## Developer Guide: Adding a New Command

1. **Define the Click command** in `cli.py` with appropriate options and arguments.

2. **Register it** in `register_commands()`:
   ```python
   main.add_command(mycommand, name="mycommand")
   main.add_command(mycommand, name="mc")  # alias, if any
   mycommand.help = "Description (aliases: mc)"
   ```

3. **Add to `COMMANDS`** in `prefix_utils.py`:
   ```python
   "mycommand": {
       "aliases": ["mc"],
       "description": "Description",
   },
   ```

4. **Add a completion arm** in the `case "$cmd"` block inside the `autocomplete()` handler in `cli.py`:
   ```python
   mycommand|mc)
       COMPREPLY=($(compgen -W "opt1= opt2= --dry-run -v --verbose -h --help" -- "$cur"))
       return
       ;;
   ```
   Use `_slurm_parse_keyval`, `_slurm_complete_value`, and the cache helpers as needed.

5. **Add a mock** in `mocks/scontrol` if the command invokes `scontrol`.

6. **Add tests** in `tests/test_mycommand.py`.

7. **Regenerate** and verify:
   ```bash
   ./slurm-cli autocomplete > /tmp/slurm_complete.sh
   source /tmp/slurm_complete.sh
   # Manual testing with COMP_WORDS/COMP_CWORD simulation
   ```

---

## Key Files

| File | Role |
|------|------|
| `src/slurm_cli/cli.py` | `autocomplete` command; all per-command completion templates |
| `src/slurm_cli/utils/prefix_utils.py` | `COMMANDS`/`RESOURCES` config; prefix computation; bash case generators |
| `src/slurm_cli/utils/autocomplete_helpers.py` | Shared bash helpers: cache, key=value parser, `_slurm_complete_nodes_value` |
| `src/slurm_cli/utils/node_filter.py` | `NODE_FILTER_PREFIXES`; `generate_node_filter_autocomplete()` |
