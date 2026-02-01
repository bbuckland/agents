#!/bin/bash
# Check for config drift between local and server
# Usage: ./drift.sh [hostname]

set -e

HOST="${1:-buckbot}"
CONFIG_DIR="/home/clawd/clawdbot-state"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Temp files
LOCAL_NORMALIZED=$(mktemp)
SERVER_NORMALIZED=$(mktemp)
trap "rm -f $LOCAL_NORMALIZED $SERVER_NORMALIZED" EXIT

# Fields to ignore when comparing (server-managed or dynamic)
IGNORE_FILTER='
  del(.meta) |
  del(.wizard) |
  del(.channels.telegram.botToken) |
  del(.agents.list)
'

echo "Checking drift against $HOST..."

# Normalize local config
jq "$IGNORE_FILTER" "$SCRIPT_DIR/openclaw.json" | jq -S '.' > "$LOCAL_NORMALIZED"

# Fetch and normalize server config
ssh "$HOST" "cat $CONFIG_DIR/openclaw.json" | jq "$IGNORE_FILTER" | jq -S '.' > "$SERVER_NORMALIZED"

# Compare
if diff -q "$LOCAL_NORMALIZED" "$SERVER_NORMALIZED" > /dev/null 2>&1; then
    echo "✓ No drift detected - server matches local config"
    exit 0
else
    echo "✗ Drift detected!"
    echo ""
    echo "Differences (local → server):"
    echo "─────────────────────────────"
    diff --color=auto -u "$LOCAL_NORMALIZED" "$SERVER_NORMALIZED" | tail -n +3 || true
    echo ""
    echo "Run ./deploy.sh $HOST to sync local → server"
    exit 1
fi
