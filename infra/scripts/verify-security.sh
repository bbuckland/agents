#!/bin/bash
set -e

cd "$(dirname "$0")/.."

# Get server IP from Pulumi
IP=$(pulumi stack output ipv4Address 2>/dev/null)

if [ -z "$IP" ]; then
    echo "Error: Could not get server IP. Is the stack deployed?"
    exit 1
fi

echo "=== OpenClaw Security Verification ==="
echo "Server IP: $IP"
echo ""

echo "1. Checking gateway is NOT exposed on public IP..."
if curl -s --connect-timeout 3 "http://$IP:18789/" > /dev/null 2>&1; then
    echo "   FAIL: Port 18789 is exposed to public internet!"
    exit 1
else
    echo "   PASS: Port 18789 is blocked from public access"
fi

echo ""
echo "2. Checking SSH is accessible..."
if nc -z -w3 "$IP" 22; then
    echo "   PASS: SSH is accessible"
else
    echo "   FAIL: SSH is not accessible"
    exit 1
fi

echo ""
echo "3. Connecting via SSH to verify internal state..."
ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=accept-new "openclaw@$IP" << 'EOF'
echo "   a. Checking gateway binding..."
if ss -tlnp | grep -q "127.0.0.1:18789"; then
    echo "      PASS: Gateway bound to loopback only"
else
    echo "      FAIL: Gateway not bound to loopback"
    exit 1
fi

echo "   b. Checking Docker security settings..."
CAPS=$(docker inspect openclaw-gateway --format '{{.HostConfig.CapDrop}}' 2>/dev/null || echo "")
if echo "$CAPS" | grep -q "ALL"; then
    echo "      PASS: All capabilities dropped"
else
    echo "      WARN: Could not verify capabilities (container may not be running yet)"
fi

echo "   c. Checking UFW status..."
sudo ufw status | grep -q "Status: active" && echo "      PASS: UFW is active" || echo "      FAIL: UFW is not active"

echo "   d. Checking file permissions..."
PERM=$(stat -c "%a" ~/.openclaw/openclaw.json 2>/dev/null || echo "")
if [ "$PERM" = "600" ]; then
    echo "      PASS: Config file permissions are 600"
else
    echo "      WARN: Config file permissions: $PERM (expected 600)"
fi

echo "   e. Checking Tailscale status..."
tailscale status > /dev/null 2>&1 && echo "      PASS: Tailscale is connected" || echo "      WARN: Tailscale not connected"
EOF

echo ""
echo "=== Verification Complete ==="
