#!/bin/bash
# Tail logs from server
# Usage: ./logs.sh [hostname] [service]
set -e

HOST="${1:-buckbot}"
SERVICE="${2:-}"
REPO_DIR="$HOME/agents"

if [ -n "$SERVICE" ]; then
    ssh "$HOST" "cd $REPO_DIR && docker compose logs -f $SERVICE"
else
    ssh "$HOST" "cd $REPO_DIR && docker compose logs -f"
fi
