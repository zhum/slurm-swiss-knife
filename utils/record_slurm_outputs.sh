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
    "\\sacctmgr show account withcoord withrawqoslevel format=account,description,organization,coordinators,qoslevel|accounts|Accounts, Coordinators, Raw QOS Level (text format)"
    "\\sacctmgr show account withcoord withrawqoslevel --json|accounts.json|Accounts (JSON format)"
    "\\sacctmgr show users format=user,defaultaccount,admin|users|Users (text format)"
    "\\sacctmgr show users --json|users.json|Users (JSON format)"
    "\\sacctmgr show associations format=account,user,cluster,partition,share,qos|associations|Associations (text format)"
    "\\sacctmgr show associations --json|associations.json|Associations (JSON format)"
    "\\sacctmgr list event format=Cluster,ClusterNodes,Duration,Start,End,Event,EventRaw,NodeName,State,StateRaw,TRES,User,Reason -p|events|Events (text format)"
    # Note: events.json is handled separately due to JSON support issues in some Slurm versions
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

# Special handling for events.json - some Slurm versions don't support JSON output
EVENTS_NO_JSON_FLAG="$MOCKS_DIR/.events_no_json"
record_events_json() {
    local output_file="$MOCKS_DIR/events.json"
    local text_file="$MOCKS_DIR/events"
    
    echo "Recording: Events (JSON format)"
    
    # Check if we already know JSON doesn't work
    if [[ -f "$EVENTS_NO_JSON_FLAG" ]]; then
        echo "  Flag file exists, skipping JSON attempt"
        convert_events_to_json "$text_file" "$output_file"
        return
    fi
    
    # Try JSON format first
    echo "  Trying: sacctmgr list event --json"
    if \sacctmgr list event --json > "$output_file" 2>&1; then
        # Check if output is valid JSON
        if jq empty "$output_file" 2>/dev/null; then
            echo "  ✓ Success - valid JSON ($(wc -l < "$output_file") lines)"
            return
        else
            echo "  ✗ Output is not valid JSON, setting flag and converting from text"
            touch "$EVENTS_NO_JSON_FLAG"
            convert_events_to_json "$text_file" "$output_file"
        fi
    else
        echo "  ✗ Command failed, setting flag and converting from text"
        touch "$EVENTS_NO_JSON_FLAG"
        convert_events_to_json "$text_file" "$output_file"
    fi
}

# Convert pipe-delimited events text to JSON
convert_events_to_json() {
    local text_file="$1"
    local output_file="$2"
    
    echo "  Converting text format to JSON..."
    
    if [[ ! -f "$text_file" ]]; then
        echo "  ✗ Text file not found: $text_file"
        return 1
    fi
    
    # Parse pipe-delimited format and convert to JSON
    # Header: Cluster|ClusterNodes|Duration|Start|End|Event|EventRaw|NodeName|State|StateRaw|TRES|User|Reason|
    python3 -c "
import json
import sys

events = []
with open('$text_file', 'r') as f:
    lines = f.readlines()
    if not lines:
        print(json.dumps({'events': []}))
        sys.exit(0)
    
    # First line is header
    header = [h.strip() for h in lines[0].strip().rstrip('|').split('|')]
    
    # Map header names to lowercase keys
    key_map = {
        'Cluster': 'cluster',
        'ClusterNodes': 'cluster_nodes', 
        'Duration': 'duration',
        'TimeStart': 'start',
        'Start': 'start',
        'TimeEnd': 'end',
        'End': 'end',
        'Event': 'event',
        'EventRaw': 'event_raw',
        'NodeName': 'node',
        'State': 'state',
        'StateRaw': 'state_raw',
        'TRES': 'tres',
        'User': 'user',
        'Reason': 'reason',
    }
    
    for line in lines[1:]:
        line = line.strip()
        if not line:
            continue
        values = [v.strip() for v in line.rstrip('|').split('|')]
        event = {}
        for i, val in enumerate(values):
            if i < len(header):
                key = key_map.get(header[i], header[i].lower())
                event[key] = val
        if event:
            events.append(event)

print(json.dumps({'events': events}, indent=2))
" > "$output_file"
    
    if [[ $? -eq 0 ]]; then
        echo "  ✓ Converted to JSON ($(wc -l < "$output_file") lines)"
    else
        echo "  ✗ Conversion failed"
        return 1
    fi
}

# Record events.json with fallback
record_events_json
echo ""

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

