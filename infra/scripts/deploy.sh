#!/bin/bash
set -e

cd "$(dirname "$0")/.."

echo "=== Deploying OpenClaw Infrastructure ==="

# Preview changes
pulumi preview

read -p "Proceed with deployment? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled."
    exit 1
fi

# Deploy
pulumi up --yes

echo ""
echo "=== Deployment Complete ==="
echo ""
echo "Next steps:"
echo "1. Wait 2-3 minutes for cloud-init to complete"
echo "2. Run: ./scripts/verify-security.sh"
echo "3. Check Tailscale admin for new device"
