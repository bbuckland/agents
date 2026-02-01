#!/bin/bash
# Deploy OpenClaw config and restart gateway
# Usage: ./deploy.sh [hostname]

set -e

HOST="${1:-buckbot}"
CONFIG_DIR="/home/clawd/clawdbot-state"
DOCKER_DIR="/home/clawd/clawdbot-docker"

echo "Deploying to $HOST..."

# Sync config (preserves server-side secrets like telegram bot token)
echo "Syncing openclaw.json..."
scp openclaw.json "$HOST:$CONFIG_DIR/openclaw.json.new"

# Merge: keep server's telegram bot token, use local config for everything else
ssh "$HOST" "cd $CONFIG_DIR && \
  TELEGRAM_TOKEN=\$(jq -r '.channels.telegram.botToken // empty' openclaw.json) && \
  jq --arg token \"\$TELEGRAM_TOKEN\" '.channels.telegram.botToken = \$token' openclaw.json.new > openclaw.json.merged && \
  mv openclaw.json.merged openclaw.json && \
  rm openclaw.json.new"

# Sync docker files
echo "Syncing Docker files..."
scp Dockerfile docker-compose.yml .env "$HOST:$DOCKER_DIR/"

# Rebuild and restart
echo "Rebuilding and restarting..."
ssh "$HOST" "cd $DOCKER_DIR && docker compose build && docker compose down && docker compose up -d"

echo "Waiting for startup..."
sleep 8

# Check status
ssh "$HOST" "docker logs clawdbot-docker-moltbot-gateway-1 2>&1 | tail -10"

echo "Done!"
