#!/usr/bin/env bash

# Source your completion script
eval "$(./slurm-cli autocomplete)"

test_completion() {
    local description="$1"
    shift
    local -a words=("$@")
    local cword=$((${#words[@]} - 1))  # Last word position

    echo "--- $description ---"
    echo "COMP_WORDS: ${words[*]}"
    echo "COMP_CWORD: $cword (completing: '${words[$cword]}')"

    COMP_LINE="${words[*]}"
    COMP_POINT=${#COMP_LINE}
    COMP_WORDS=("${words[@]}")
    COMP_CWORD=$cword

    _slurm_cli_initialize_autocomplete
    echo "Completions: ${COMPREPLY[*]}"
    echo ""
    unset COMPREPLY
}

# Test cases
test_completion "update accounts <TAB>" "./slurm-cli" "$@" ""
# test_completion "update acc<TAB>" "./slurm-cli" "update" "acc"
# test_completion "show accounts <TAB>" "./slurm-cli" "show" "accounts" ""
# test_completion "update <TAB>" "./slurm-cli" "update" ""
