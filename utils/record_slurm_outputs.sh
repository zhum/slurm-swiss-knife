#!/usr/bin/env bash

# Script to record SLURM command outputs for creating mock data
# This should be run on a real SLURM cluster

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MOCKS_DIR="$(pwd)/mocks"

# Create mocks directory if it doesn't exist
mkdir -p "$MOCKS_DIR"

echo "Recording SLURM command outputs..."
echo "Output directory: $MOCKS_DIR"
echo ""

# Define commands to record as an array
# Format: "command|output_file|description"
declare -a COMMANDS=(
    "\\scontrol show partitions|partitions|Partitions (text format)"
    "\\scontrol show partitions --json|partitions.json|Partitions (JSON format)"
    "\\scontrol show nodes|nodes|Nodes (text format)"
    "\\scontrol show nodes --json|nodes.json|Nodes (JSON format)"
    "\\scontrol show reservations|reservations|Reservations (text format)"
    "\\scontrol show reservations --json|reservations.json|Reservations (JSON format)"
    "\\scontrol show config|slurm_config|SLURM configuration"
    "\\sacctmgr show qos format=name,priority,grptresmins,grptresrunmins,grptres,grpjobs,grpsubmitjobs,maxtresminsperuser,maxsubmitjobsperuser,maxwall|qos|QoS (text format)"
    "\\sacctmgr show qos --json|qos.json|QoS (JSON format)"
    "\\sacctmgr show accounts format=account,description,organization|accounts|Accounts (text format)"
    "\\sacctmgr show accounts --json|accounts.json|Accounts (JSON format)"
    "\\sacctmgr show users format=user,defaultaccount,admin|users|Users (text format)"
    "\\sacctmgr show users --json|users.json|Users (JSON format)"
    "\\squeue --all --format='%.18i %.9P %.50j %.8u %.2t %.10M %.6D %R'|squeue_all|Queue - all jobs (text format)"
    "\\squeue --all --json|squeue.json|Queue - all jobs (JSON format)"
    "\\squeue --all --states=PENDING,RUNNING,SUSPENDED --format='%.18i %.9P %.50j %.8u %.2t %.10M %.6D %R'|squeue_active|Queue - active jobs"
    "\\squeue --all -O 'JobID:8,Partition:24 ,Name:15 ,UserName:24 ,Account:32 ,State,TimeLimit:16,NumNodes:7 ,NodeList: ,Reason'|squeue_extended|Queue - extended format"
    "\\sinfo|sinfo|Cluster info (sinfo)"
    "\\sinfo --json|sinfo.json|Cluster info (JSON format)"
)

# Function to run a command and save output
run_and_save() {
    local cmd="$1"
    local output_file="$2"
    local description="$3"
    
    echo "Recording: $description"
    echo "  Command: $cmd"
    echo "  Output: $output_file"
    
    if eval "$cmd" > "$output_file" 2>&1; then
        echo "  ✓ Success ($(wc -l < "$output_file") lines)"
    else
        echo "  ✗ Failed (exit code: $?)"
        rm -f "$output_file"
    fi
    echo ""
}

# Iterate through commands and record outputs
for entry in "${COMMANDS[@]}"; do
    IFS='|' read -r cmd output_file description <<< "$entry"
    run_and_save "$cmd" "$MOCKS_DIR/$output_file" "$description"
done

echo "========================================"
echo "Recording complete!"
echo ""
echo "Files created in: $MOCKS_DIR"
ls -lh "$MOCKS_DIR/"
echo ""
echo "Next steps:"
echo "1. Review the recorded files"
echo "2. Sanitize any sensitive information if needed"
echo "3. Commit the mock data files to version control"
echo "4. Use the mock scripts (scontrol, sacctmgr, squeue) for testing"

