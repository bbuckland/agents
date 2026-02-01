#!/bin/bash
# Quick skill sync without full restart
# Usage: ./sync-skills.sh [hostname]
set -e

HOST="${1:-buckbot}"
REPO_DIR="$HOME/agents"
SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "Syncing skills to $HOST..."
rsync -avz "$SCRIPT_DIR/skills/" "$HOST:$REPO_DIR/openclaw/skills/"

echo "Skills synced. Restart openclaw to pick up changes:"
echo "  ssh $HOST 'cd $REPO_DIR && docker compose restart openclaw'"
