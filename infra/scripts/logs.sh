#!/bin/bash
set -e

cd "$(dirname "$0")/.."

IP=$(pulumi stack output ipv4Address 2>/dev/null)

if [ -z "$IP" ]; then
    echo "Error: Could not get server IP."
    exit 1
fi

SERVICE=${1:-openclaw}

echo "Tailing logs for $SERVICE on $IP..."
ssh "openclaw@$IP" "cd ~ && docker compose logs -f $SERVICE"
