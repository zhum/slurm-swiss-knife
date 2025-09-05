"""Common bash autocomplete helper functions for slurm-cli.

This module provides reusable bash functions that are shared across
all resource-specific autocomplete generators.
"""

from .resources import Resource


def get_common_autocomplete_functions() -> str:
    """Generate common bash functions for autocomplete.

    Returns:
        Bash script string with helper functions.
    """
    return f"""
# ==============================================================================
# Common autocomplete helper functions
# ==============================================================================

# Cache timeout in seconds
_SLURM_CACHE_TIMEOUT={Resource.CACHE_TIMEOUT}

# Check if cache update is disabled via environment variable
# Returns 0 if updates are disabled, 1 otherwise
_slurm_cache_updates_disabled() {{
    local val="${{SLURM_CLI_NO_CACHE_UPDATE:-}}"
    val="${{val,,}}"  # lowercase
    [[ "$val" == "1" || "$val" == "y" || "$val" == "yes" || "$val" == "true" ]]
}}

# Ensure cache file exists and is fresh, update if needed
# Usage: _slurm_ensure_cache "/tmp/slurm_cli_nodes.json" "nodes"
_slurm_ensure_cache() {{
    local file="$1"
    local resource="$2"

    # Skip if updates are disabled
    _slurm_cache_updates_disabled && return

    local needs_update=0

    if [[ ! -f "$file" ]]; then
        needs_update=1
    else
        # Check if file is older than timeout
        local now=$(date +%s)
        local mtime=$(stat -c %Y "$file" 2>/dev/null || echo 0)
        local age=$((now - mtime))
        if [[ $age -gt $_SLURM_CACHE_TIMEOUT ]]; then
            needs_update=1
        fi
    fi

    if [[ $needs_update -eq 1 ]]; then
        # Update cache silently in foreground (need results immediately)
        # Try the invoked binary first (handles ./slurm-cli), then fall back to PATH
        local _cli="${{COMP_WORDS[0]:-slurm-cli}}"
        "$_cli" show "$resource" --style=json >/dev/null 2>&1 || \
            slurm-cli show "$resource" --style=json >/dev/null 2>&1
    fi
}}

# Complete with compgen, handling empty current word
# Usage: _slurm_complete "word1 word2 word3" "$cur"
_slurm_complete() {{
    local words="$1"
    local cur="$2"
    if [[ -z "$cur" ]]; then
        COMPREPLY=($(compgen -W "$words"))
    else
        COMPREPLY=($(compgen -W "$words" -- "$cur"))
    fi
}}

# Get names from a JSON cache file
# Usage: _slurm_cache_get "/tmp/file.json" ".field[].name" -> "name1 name2 name3"
_slurm_cache_get() {{
    local file="$1"
    local jq_expr="$2"
    if [ -f "$file" ]; then
        jq -r "$jq_expr" "$file" 2>/dev/null | tr '\\n' ' '
    fi
}}

# Parse key=value format and set _key and _val variables
# Usage: _slurm_parse_keyval "$cur" "$prev"
#        After call: $_key = key name (lowercase), $_val = value part
#        Returns: 0 if key=value found, 1 otherwise
_slurm_parse_keyval() {{
    local cur="$1"
    local prev="$2"
    _key=""
    _val=""

    if [[ $cur == = ]]; then
        # cur is just "=", key is previous word
        _key="${{prev,,}}"
        _val=""
        return 0
    elif [[ $cur == *=* ]]; then
        # cur contains "=" (e.g., "key=val" or "key=")
        _key="${{cur%%=*}}"
        _key="${{_key,,}}"
        _val="${{cur#*=}}"
        return 0
    elif [[ $prev == = ]]; then
        # prev is "=", key is two words back
        _key="${{COMP_WORDS[COMP_CWORD-2]}}"
        _key="${{_key,,}}"
        _val="$cur"
        return 0
    fi
    return 1
}}

# Parse key=value, key+=value, or key-=value format
# Usage: _slurm_parse_keyval_ext "$cur" "$prev"
#        After call: $_key = key name (lowercase), $_val = value part, $_op = operator (=, +=, -=)
#        Returns: 0 if found, 1 otherwise
_slurm_parse_keyval_ext() {{
    local cur="$1"
    local prev="$2"
    _key=""
    _val=""
    _op=""

    # Check cur for key+=val, key-=val, or key=val
    if [[ $cur == *[-+]=* ]] || [[ $cur == *=* ]]; then
        _key="${{cur%%[-+]*=*}}"
        _key="${{_key%%=*}}"
        _key="${{_key,,}}"
        _val="${{cur#*=}}"
        [[ $cur == *+=* ]] && _op="+=" || {{ [[ $cur == *-=* ]] && _op="-=" || _op="="; }}
        return 0
    # Check if prev is =, +=, or -=
    elif [[ $prev == "=" ]] || [[ $prev == "+=" ]] || [[ $prev == "-=" ]]; then
        _key="${{COMP_WORDS[COMP_CWORD-2]}}"
        _key="${{_key,,}}"
        _val="$cur"
        _op="$prev"
        return 0
    # Check if prev ends with operator
    elif [[ $prev == *[-+]= ]] || [[ $prev == *= ]]; then
        _key="${{prev%%[-+]*=}}"
        _key="${{_key%%=}}"
        _key="${{_key,,}}"
        _val="$cur"
        _op="${{prev##*[!-+=]}}"
        return 0
    fi
    return 1
}}

# Complete value and add key= (or key+= / key-=) prefix back if needed
# Usage: _slurm_complete_value "word1 word2" "$_key" "$_val" "$cur"
#        If cur contains =, prefix is added back to completions
#        If prev is = (bash split on =), do NOT add prefix (it's already typed)
#        Uses $_op if set by _slurm_parse_keyval_ext (defaults to "=")
_slurm_complete_value() {{
    local words="$1"
    local key="$2"
    local val="$3"
    local cur="$4"
    local op="${{_op:-=}}"

    COMPREPLY=($(compgen -W "$words" -- "$val"))

    # Only add key+op prefix when cur contains = (bash didn't split)
    # If bash split on =, the key= is already on command line
    if [[ $cur == *=* && ${{#COMPREPLY[@]}} -gt 0 ]]; then
        COMPREPLY=("${{COMPREPLY[@]/#/$key$op}}")
    fi
}}

# Cache accessor functions for common resources
# Each function ensures cache is fresh before reading
_slurm_cache_accounts() {{
    _slurm_ensure_cache "/tmp/slurm_cli_accounts.json" "accounts"
    _slurm_cache_get "/tmp/slurm_cli_accounts.json" '.accounts[].name'
}}

_slurm_cache_qos() {{
    _slurm_ensure_cache "/tmp/slurm_cli_qos.json" "qos"
    _slurm_cache_get "/tmp/slurm_cli_qos.json" '.qos[].name'
}}

_slurm_cache_partitions() {{
    _slurm_ensure_cache "/tmp/slurm_cli_partitions.json" "partitions"
    _slurm_cache_get "/tmp/slurm_cli_partitions.json" 'keys[]'
}}

_slurm_cache_nodes() {{
    _slurm_ensure_cache "/tmp/slurm_cli_nodes.json" "nodes"
    _slurm_cache_get "/tmp/slurm_cli_nodes.json" 'keys[]'
}}

_slurm_cache_users() {{
    _slurm_ensure_cache "/tmp/slurm_cli_users.json" "users"
    _slurm_cache_get "/tmp/slurm_cli_users.json" '.users[].name'
}}

_slurm_cache_reservations() {{
    _slurm_ensure_cache "/tmp/slurm_cli_reservations.json" "reservations"
    _slurm_cache_get "/tmp/slurm_cli_reservations.json" 'keys[]'
}}

_slurm_cache_jobs() {{
    _slurm_ensure_cache "/tmp/slurm_cli_jobs.json" "jobs"
    _slurm_cache_get "/tmp/slurm_cli_jobs.json" '.jobs[].job_id'
}}

# Node filter prefixes for nodes= parameter
# Supports: ALL, partition=, state=, user=, reservation=
_slurm_node_filter_prefixes="ALL partition= state= user= reservation= drain="

# Complete nodes= value with either direct nodes or filter prefixes
# Usage: _slurm_complete_nodes_value "$_val" "$cur" ["$_key"]
# The prefix for completions is derived from $cur to preserve case
_slurm_complete_nodes_value() {{
    local val="$1"
    local cur="$2"
    local key="${{3:-nodes}}"
    local cached_nodes="$(_slurm_cache_nodes)"

    # Derive prefix from cur by removing val from the end (preserves original case)
    # Note: When bash splits on '=', cur is empty and we should NOT add prefix
    # because bash already has the key= part typed
    local prefix=""
    if [[ "$cur" == *=* && -n "$val" ]]; then
        prefix="${{cur%"$val"}}"
    elif [[ "$cur" == *=* && "$cur" != "=" ]]; then
        prefix="$cur"
    fi

    # Check if value starts with a filter prefix
    if [[ "$val" == partition=* ]]; then
        local filter_val="${{val#partition=}}"
        local partitions="$(_slurm_cache_partitions)"
        COMPREPLY=($(compgen -W "$partitions" -- "$filter_val"))
        [[ -n "$prefix" && ${{#COMPREPLY[@]}} -gt 0 ]] && COMPREPLY=("${{COMPREPLY[@]/#/${{prefix}}partition=}}")
    elif [[ "$val" == state=* ]]; then
        local filter_val="${{val#state=}}"
        local states="idle alloc drain down mixed comp"
        COMPREPLY=($(compgen -W "$states" -- "$filter_val"))
        [[ -n "$prefix" && ${{#COMPREPLY[@]}} -gt 0 ]] && COMPREPLY=("${{COMPREPLY[@]/#/${{prefix}}state=}}")
    elif [[ "$val" == user=* ]]; then
        local filter_val="${{val#user=}}"
        local users="$(_slurm_cache_users)"
        COMPREPLY=($(compgen -W "$users" -- "$filter_val"))
        [[ -n "$prefix" && ${{#COMPREPLY[@]}} -gt 0 ]] && COMPREPLY=("${{COMPREPLY[@]/#/${{prefix}}user=}}")
    elif [[ "$val" == reservation=* ]]; then
        local filter_val="${{val#reservation=}}"
        local reservations="$(_slurm_cache_reservations)"
        COMPREPLY=($(compgen -W "$reservations" -- "$filter_val"))
        [[ -n "$prefix" && ${{#COMPREPLY[@]}} -gt 0 ]] && COMPREPLY=("${{COMPREPLY[@]/#/${{prefix}}reservation=}}")
    elif [[ "$val" == drain=* ]]; then
        COMPREPLY=("REGEXP")
        [[ -n "$prefix" ]] && COMPREPLY=("${{prefix}}drain=REGEXP")
    else
        # Not a filter prefix, show filter prefixes and cached nodes
        COMPREPLY=($(compgen -W "$_slurm_node_filter_prefixes $cached_nodes" -- "$val"))
        [[ ${{#COMPREPLY[@]}} -gt 0 && -n "$prefix" ]] && COMPREPLY=("${{COMPREPLY[@]/#/$prefix}}")
    fi
}}
"""  # noqa: E501
