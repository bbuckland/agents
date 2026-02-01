#!/bin/bash
# Deploy agents to server
# Usage: ./deploy.sh [hostname]
set -e

HOST="${1:-buckbot}"
REPO_DIR="$HOME/agents"
SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "Deploying to $HOST..."

# Push to GitHub first
echo "Pushing to GitHub..."
cd "$ROOT_DIR"
git push

# Pull on server and restart
echo "Pulling and restarting on server..."
ssh "$HOST" "cd $REPO_DIR && git pull && docker compose up -d --build"

echo "Waiting for startup..."
sleep 8

# Show logs
ssh "$HOST" "cd $REPO_DIR && docker compose logs --tail=20"

echo "Done!"
