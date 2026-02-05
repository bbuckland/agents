#!/bin/bash
set -e

cd "$(dirname "$0")/../.."

IP=$(cd infra && pulumi stack output ipv4Address 2>/dev/null)

if [ -z "$IP" ]; then
    echo "Error: Could not get server IP."
    exit 1
fi

echo "Syncing skills to openclaw@$IP..."
rsync -avz --delete openclaw/skills/ "openclaw@$IP:~/skills/"

echo ""
echo "Skills synced. Restart container to pick up changes:"
echo "  ssh openclaw@$IP 'docker compose restart openclaw'"
