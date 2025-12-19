"""Common bash autocomplete helper functions for slurm-cli.

This module provides reusable bash functions that are shared across
all resource-specific autocomplete generators.
"""


def get_common_autocomplete_functions() -> str:
    """Generate common bash functions for autocomplete.

    Returns:
        Bash script string with helper functions.
    """
    return """
# ==============================================================================
# Common autocomplete helper functions
# ==============================================================================

# Complete with compgen, handling empty current word
# Usage: _slurm_complete "word1 word2 word3" "$cur"
_slurm_complete() {
    local words="$1"
    local cur="$2"
    if [[ -z "$cur" ]]; then
        COMPREPLY=($(compgen -W "$words"))
    else
        COMPREPLY=($(compgen -W "$words" -- "$cur"))
    fi
}

# Get names from a JSON cache file
# Usage: _slurm_cache_get "/tmp/file.json" ".field[].name" -> "name1 name2 name3"
_slurm_cache_get() {
    local file="$1"
    local jq_expr="$2"
    if [ -f "$file" ]; then
        jq -r "$jq_expr" "$file" 2>/dev/null | tr '\\n' ' '
    fi
}

# Parse key=value format and set _key and _val variables
# Usage: _slurm_parse_keyval "$cur" "$prev"
#        After call: $_key = key name (lowercase), $_val = value part
#        Returns: 0 if key=value found, 1 otherwise
_slurm_parse_keyval() {
    local cur="$1"
    local prev="$2"
    _key=""
    _val=""

    if [[ $cur == = ]]; then
        # cur is just "=", key is previous word
        _key="${prev,,}"
        _val=""
        return 0
    elif [[ $cur == *=* ]]; then
        # cur contains "=" (e.g., "key=val" or "key=")
        _key="${cur%%=*}"
        _key="${_key,,}"
        _val="${cur#*=}"
        return 0
    elif [[ $prev == = ]]; then
        # prev is "=", key is two words back
        _key="${COMP_WORDS[COMP_CWORD-2]}"
        _key="${_key,,}"
        _val="$cur"
        return 0
    fi
    return 1
}

# Parse key=value, key+=value, or key-=value format
# Usage: _slurm_parse_keyval_ext "$cur" "$prev"
#        After call: $_key = key name (lowercase), $_val = value part, $_op = operator (=, +=, -=)
#        Returns: 0 if found, 1 otherwise
_slurm_parse_keyval_ext() {
    local cur="$1"
    local prev="$2"
    _key=""
    _val=""
    _op=""

    # Check cur for key+=val, key-=val, or key=val
    if [[ $cur == *[-+]=* ]] || [[ $cur == *=* ]]; then
        _key="${cur%%[-+]*=*}"
        _key="${_key%%=*}"
        _key="${_key,,}"
        _val="${cur#*=}"
        [[ $cur == *+=* ]] && _op="+=" || { [[ $cur == *-=* ]] && _op="-=" || _op="="; }
        return 0
    # Check if prev is =, +=, or -=
    elif [[ $prev == "=" ]] || [[ $prev == "+=" ]] || [[ $prev == "-=" ]]; then
        _key="${COMP_WORDS[COMP_CWORD-2]}"
        _key="${_key,,}"
        _val="$cur"
        _op="$prev"
        return 0
    # Check if prev ends with operator
    elif [[ $prev == *[-+]= ]] || [[ $prev == *= ]]; then
        _key="${prev%%[-+]*=}"
        _key="${_key%%=}"
        _key="${_key,,}"
        _val="$cur"
        _op="${prev##*[!-+=]}"
        return 0
    fi
    return 1
}

# Complete value and add key= prefix back if needed
# Usage: _slurm_complete_value "word1 word2" "$_key" "$_val" "$cur"
#        If cur contains =, prefix is added back to completions
_slurm_complete_value() {
    local words="$1"
    local key="$2"
    local val="$3"
    local cur="$4"

    COMPREPLY=($(compgen -W "$words" -- "$val"))

    # If cur contains =, add key= prefix back to completions
    if [[ $cur == *=* && ${#COMPREPLY[@]} -gt 0 ]]; then
        COMPREPLY=("${COMPREPLY[@]/#/$key=}")
    fi
}

# Cache accessor functions for common resources
_slurm_cache_accounts() {
    _slurm_cache_get "/tmp/slurm_cli_accounts.json" '.accounts[].name'
}

_slurm_cache_qos() {
    _slurm_cache_get "/tmp/slurm_cli_qos.json" '.qos[].name'
}

_slurm_cache_partitions() {
    _slurm_cache_get "/tmp/slurm_cli_partitions.json" 'keys[]'
}

_slurm_cache_nodes() {
    _slurm_cache_get "/tmp/slurm_cli_nodes.json" 'keys[]'
}

_slurm_cache_users() {
    _slurm_cache_get "/tmp/slurm_cli_users.json" '.users[].name'
}

_slurm_cache_reservations() {
    _slurm_cache_get "/tmp/slurm_cli_reservations.json" 'keys[]'
}
"""  # noqa: E501
