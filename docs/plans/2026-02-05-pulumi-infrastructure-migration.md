# OpenClaw Pulumi Infrastructure Migration

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace Docker Compose deployment with Pulumi-managed Hetzner infrastructure following the OpenClaw Cloud Gateway Security Enforcement Checklist.

**Architecture:** Pulumi TypeScript manages a Hetzner Cloud server with hardened Docker containers, Tailscale for secure access, UFW firewall, and proper secrets management. The gateway binds to loopback only with token authentication.

**Tech Stack:** Pulumi (TypeScript), Hetzner Cloud, Docker, Tailscale, UFW, cloud-init

---

## Prerequisites Checklist

Before starting:
- [ ] Hetzner Cloud account with API token
- [ ] Tailscale account with auth key
- [ ] Current `.env` values backed up
- [ ] Pulumi account (free tier works)

---

## Task 1: Install Pulumi and Initialize Project

**Files:**
- Create: `infra/` directory
- Create: `infra/package.json`
- Create: `infra/Pulumi.yaml`
- Create: `infra/tsconfig.json`

**Step 1: Install Pulumi via Homebrew**

```bash
brew install pulumi
```

**Step 2: Verify Pulumi installation**

Run: `pulumi version`
Expected: Version number like `v3.x.x`

**Step 3: Create infrastructure directory**

```bash
mkdir -p infra
cd infra
```

**Step 4: Initialize Pulumi project**

```bash
pulumi new typescript --name agents-infra --description "OpenClaw infrastructure on Hetzner" --yes
```

**Step 5: Install Hetzner provider**

```bash
cd infra && npm install @pulumi/hcloud
```

**Step 6: Commit**

```bash
git add infra/
git commit -m "feat: initialize Pulumi infrastructure project"
```

---

## Task 2: Backup Environment Variables

**Files:**
- Read: `openclaw/.env`
- Create: `infra/secrets.md` (documentation only, not committed)

**Step 1: Document current environment variables**

```bash
# List all env vars (names only, not values)
grep -E "^[A-Z_]+=" openclaw/.env | cut -d= -f1 > /tmp/env-vars-to-migrate.txt
cat /tmp/env-vars-to-migrate.txt
```

Expected output:
```
OPENCLAW_CONFIG_DIR
OPENCLAW_WORKSPACE_DIR
OPENCLAW_GATEWAY_PORT
OPENCLAW_GATEWAY_TOKEN
ANTHROPIC_API_KEY
GH_TOKEN
YNAB_API_KEY
TELEGRAM_BUCKBOT_TOKEN
TELEGRAM_EXPENSE_TOKEN
TELEGRAM_QUANT_TOKEN
```

**Step 2: Store secrets in Pulumi config (encrypted)**

```bash
cd infra

# Gateway token
pulumi config set --secret openclaw:gatewayToken "$(grep OPENCLAW_GATEWAY_TOKEN ../openclaw/.env | cut -d= -f2)"

# API keys
pulumi config set --secret anthropic:apiKey "$(grep ANTHROPIC_API_KEY ../openclaw/.env | cut -d= -f2)"
pulumi config set --secret github:token "$(grep GH_TOKEN ../openclaw/.env | cut -d= -f2)"
pulumi config set --secret ynab:apiKey "$(grep YNAB_API_KEY ../openclaw/.env | cut -d= -f2)"

# Telegram tokens
pulumi config set --secret telegram:buckbotToken "$(grep TELEGRAM_BUCKBOT_TOKEN ../openclaw/.env | cut -d= -f2)"
pulumi config set --secret telegram:expenseToken "$(grep TELEGRAM_EXPENSE_TOKEN ../openclaw/.env | cut -d= -f2)"
pulumi config set --secret telegram:quantToken "$(grep TELEGRAM_QUANT_TOKEN ../openclaw/.env | cut -d= -f2)"
```

**Step 3: Verify secrets are encrypted**

Run: `cat infra/Pulumi.dev.yaml`
Expected: Values show `secure:` prefix with encrypted content

**Step 4: Commit Pulumi config (secrets are encrypted)**

```bash
git add infra/Pulumi.dev.yaml
git commit -m "feat: add encrypted secrets to Pulumi config"
```

---

## Task 3: Configure Hetzner Provider

**Files:**
- Modify: `infra/index.ts`
- Create: `infra/src/config.ts`

**Step 1: Set Hetzner API token**

```bash
cd infra
pulumi config set --secret hcloud:token "<YOUR_HETZNER_API_TOKEN>"
```

**Step 2: Create config module**

Create `infra/src/config.ts`:

```typescript
import * as pulumi from "@pulumi/pulumi";

const config = new pulumi.Config();
const openclawConfig = new pulumi.Config("openclaw");
const anthropicConfig = new pulumi.Config("anthropic");
const githubConfig = new pulumi.Config("github");
const ynabConfig = new pulumi.Config("ynab");
const telegramConfig = new pulumi.Config("telegram");
const tailscaleConfig = new pulumi.Config("tailscale");

export const secrets = {
  gatewayToken: openclawConfig.requireSecret("gatewayToken"),
  anthropicApiKey: anthropicConfig.requireSecret("apiKey"),
  githubToken: githubConfig.requireSecret("token"),
  ynabApiKey: ynabConfig.requireSecret("apiKey"),
  telegramBuckbot: telegramConfig.requireSecret("buckbotToken"),
  telegramExpense: telegramConfig.requireSecret("expenseToken"),
  telegramQuant: telegramConfig.requireSecret("quantToken"),
  tailscaleAuthKey: tailscaleConfig.requireSecret("authKey"),
};

export const serverConfig = {
  name: config.get("serverName") || "openclaw-gateway",
  location: config.get("location") || "fsn1", // Falkenstein, Germany
  serverType: config.get("serverType") || "cx22", // 2 vCPU, 4GB RAM
  image: config.get("image") || "ubuntu-24.04",
};
```

**Step 3: Update directory structure**

```bash
mkdir -p infra/src
mv infra/index.ts infra/src/ 2>/dev/null || true
```

**Step 4: Commit**

```bash
git add infra/src/config.ts
git commit -m "feat: add Pulumi configuration module"
```

---

## Task 4: Create Cloud-Init Script for Server Bootstrap

**Files:**
- Create: `infra/src/cloud-init.ts`

**Step 1: Write cloud-init template**

Create `infra/src/cloud-init.ts`:

```typescript
import * as pulumi from "@pulumi/pulumi";

export interface CloudInitParams {
  gatewayToken: pulumi.Output<string>;
  anthropicApiKey: pulumi.Output<string>;
  githubToken: pulumi.Output<string>;
  ynabApiKey: pulumi.Output<string>;
  telegramBuckbot: pulumi.Output<string>;
  telegramExpense: pulumi.Output<string>;
  telegramQuant: pulumi.Output<string>;
  tailscaleAuthKey: pulumi.Output<string>;
}

export function generateCloudInit(params: CloudInitParams): pulumi.Output<string> {
  return pulumi.all([
    params.gatewayToken,
    params.anthropicApiKey,
    params.githubToken,
    params.ynabApiKey,
    params.telegramBuckbot,
    params.telegramExpense,
    params.telegramQuant,
    params.tailscaleAuthKey,
  ]).apply(([
    gatewayToken,
    anthropicApiKey,
    githubToken,
    ynabApiKey,
    telegramBuckbot,
    telegramExpense,
    telegramQuant,
    tailscaleAuthKey,
  ]) => `#cloud-config
package_update: true
package_upgrade: true

packages:
  - docker.io
  - docker-compose-v2
  - ufw
  - fail2ban
  - unattended-upgrades

users:
  - name: openclaw
    groups: docker
    shell: /bin/bash
    sudo: ['ALL=(ALL) NOPASSWD:ALL']
    ssh_authorized_keys:
      - ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIG... # Add your SSH key

write_files:
  # OpenClaw configuration
  - path: /home/openclaw/.openclaw/openclaw.json
    owner: openclaw:openclaw
    permissions: '0600'
    content: |
      {
        "gateway": {
          "bind": "loopback",
          "port": 18789,
          "auth": {
            "mode": "token",
            "token": "${gatewayToken}",
            "allowTailscale": true
          },
          "mdns": {
            "enabled": false
          }
        },
        "model": {
          "primary": "claude-sonnet-4-20250514",
          "fallback": ["claude-3-5-sonnet-20241022"]
        },
        "channels": {
          "telegram": {
            "enabled": true,
            "allowDms": true
          }
        },
        "session": {
          "scope": "per-sender",
          "dailyResetHour": 4,
          "idleTimeoutMinutes": 120
        },
        "context": {
          "maxTokens": 100000
        }
      }

  # Environment file for Docker
  - path: /home/openclaw/.env
    owner: openclaw:openclaw
    permissions: '0600'
    content: |
      OPENCLAW_GATEWAY_TOKEN=${gatewayToken}
      ANTHROPIC_API_KEY=${anthropicApiKey}
      GH_TOKEN=${githubToken}
      YNAB_API_KEY=${ynabApiKey}
      TELEGRAM_BUCKBOT_TOKEN=${telegramBuckbot}
      TELEGRAM_EXPENSE_TOKEN=${telegramExpense}
      TELEGRAM_QUANT_TOKEN=${telegramQuant}

  # Docker compose for OpenClaw
  - path: /home/openclaw/docker-compose.yml
    owner: openclaw:openclaw
    permissions: '0644'
    content: |
      services:
        openclaw:
          image: ghcr.io/openclaw/openclaw:latest
          container_name: openclaw-gateway
          restart: unless-stopped
          cap_drop:
            - ALL
          security_opt:
            - no-new-privileges:true
          read_only: true
          tmpfs:
            - /tmp:rw,noexec,nosuid,size=100m
          mem_limit: 2g
          cpus: 2
          pids_limit: 100
          user: "1000:1000"
          ports:
            - "127.0.0.1:18789:18789"
          volumes:
            - /home/openclaw/.openclaw:/home/node/.openclaw:rw
            - /home/openclaw/workspace:/home/node/workspace:rw
            - /home/openclaw/skills:/home/node/skills:ro
          env_file:
            - /home/openclaw/.env
          command: ["node", "dist/index.js", "gateway", "--bind", "loopback", "--port", "18789"]

  # UFW rules script
  - path: /home/openclaw/setup-firewall.sh
    owner: root:root
    permissions: '0755'
    content: |
      #!/bin/bash
      set -e
      ufw default deny incoming
      ufw default allow outgoing
      ufw allow 22/tcp
      ufw limit 22/tcp
      # Note: 18789 intentionally NOT allowed - Tailscale only
      ufw --force enable

  # Tailscale setup script
  - path: /home/openclaw/setup-tailscale.sh
    owner: root:root
    permissions: '0755'
    content: |
      #!/bin/bash
      set -e
      curl -fsSL https://tailscale.com/install.sh | sh
      tailscale up --auth-key=${tailscaleAuthKey} --hostname=openclaw-gateway
      # Serve the gateway over Tailscale HTTPS
      tailscale serve --bg https+insecure://127.0.0.1:18789

runcmd:
  # Set up directories with correct permissions
  - mkdir -p /home/openclaw/.openclaw
  - mkdir -p /home/openclaw/workspace
  - mkdir -p /home/openclaw/skills
  - chown -R openclaw:openclaw /home/openclaw
  - chmod 700 /home/openclaw/.openclaw
  - chmod 600 /home/openclaw/.openclaw/openclaw.json
  - chmod 600 /home/openclaw/.env

  # Configure UFW
  - /home/openclaw/setup-firewall.sh

  # Install and configure Tailscale
  - /home/openclaw/setup-tailscale.sh

  # Enable Docker service
  - systemctl enable docker
  - systemctl start docker

  # Start OpenClaw
  - cd /home/openclaw && docker compose pull
  - cd /home/openclaw && docker compose up -d

  # Verify security settings
  - echo "=== Security Verification ==="
  - ss -tlnp | grep 18789 || echo "Gateway port check"
  - ufw status verbose
  - docker inspect openclaw-gateway --format '{{.HostConfig.CapDrop}}' || echo "Container not yet started"
`);
}
```

**Step 2: Verify file was created**

Run: `cat infra/src/cloud-init.ts | head -20`
Expected: File content starting with imports

**Step 3: Commit**

```bash
git add infra/src/cloud-init.ts
git commit -m "feat: add cloud-init template with security hardening"
```

---

## Task 5: Create Hetzner Server Resource

**Files:**
- Create: `infra/src/server.ts`
- Modify: `infra/src/index.ts`

**Step 1: Create server module**

Create `infra/src/server.ts`:

```typescript
import * as pulumi from "@pulumi/pulumi";
import * as hcloud from "@pulumi/hcloud";
import { serverConfig } from "./config";
import { generateCloudInit, CloudInitParams } from "./cloud-init";

export interface ServerOutputs {
  serverId: pulumi.Output<number>;
  serverName: pulumi.Output<string>;
  ipv4Address: pulumi.Output<string>;
  ipv6Address: pulumi.Output<string>;
}

export function createServer(cloudInitParams: CloudInitParams): ServerOutputs {
  // Create SSH key resource (optional - can also use existing)
  const sshKey = new hcloud.SshKey("openclaw-ssh-key", {
    name: "openclaw-deploy-key",
    publicKey: pulumi.output(
      // Read from local file or set via config
      require("fs").readFileSync(
        `${process.env.HOME}/.ssh/id_ed25519.pub`,
        "utf8"
      )
    ),
  });

  // Generate cloud-init user data
  const userData = generateCloudInit(cloudInitParams);

  // Create the server
  const server = new hcloud.Server("openclaw-gateway", {
    name: serverConfig.name,
    serverType: serverConfig.serverType,
    location: serverConfig.location,
    image: serverConfig.image,
    sshKeys: [sshKey.id],
    userData: userData,
    publicNets: [{
      ipv4Enabled: true,
      ipv6Enabled: true,
    }],
    labels: {
      environment: "production",
      service: "openclaw-gateway",
      managed_by: "pulumi",
    },
  });

  // Create firewall (defense in depth - in addition to UFW)
  const firewall = new hcloud.Firewall("openclaw-firewall", {
    name: "openclaw-gateway-fw",
    rules: [
      {
        direction: "in",
        protocol: "tcp",
        port: "22",
        sourceIps: ["0.0.0.0/0", "::/0"],
        description: "SSH access",
      },
      {
        direction: "in",
        protocol: "icmp",
        sourceIps: ["0.0.0.0/0", "::/0"],
        description: "ICMP ping",
      },
      // Note: Port 18789 intentionally NOT allowed
      // Access via Tailscale only
    ],
    labels: {
      environment: "production",
      service: "openclaw-gateway",
    },
  });

  // Attach firewall to server
  new hcloud.FirewallAttachment("openclaw-fw-attachment", {
    firewallId: firewall.id.apply(id => parseInt(id)),
    serverIds: [server.id.apply(id => parseInt(id))],
  });

  return {
    serverId: server.id.apply(id => parseInt(id)),
    serverName: server.name,
    ipv4Address: server.ipv4Address,
    ipv6Address: server.ipv6Address,
  };
}
```

**Step 2: Update main index.ts**

Create `infra/src/index.ts`:

```typescript
import * as pulumi from "@pulumi/pulumi";
import { secrets } from "./config";
import { createServer } from "./server";

// Create the OpenClaw gateway server
const serverOutputs = createServer({
  gatewayToken: secrets.gatewayToken,
  anthropicApiKey: secrets.anthropicApiKey,
  githubToken: secrets.githubToken,
  ynabApiKey: secrets.ynabApiKey,
  telegramBuckbot: secrets.telegramBuckbot,
  telegramExpense: secrets.telegramExpense,
  telegramQuant: secrets.telegramQuant,
  tailscaleAuthKey: secrets.tailscaleAuthKey,
});

// Export outputs for reference
export const serverId = serverOutputs.serverId;
export const serverName = serverOutputs.serverName;
export const ipv4Address = serverOutputs.ipv4Address;
export const ipv6Address = serverOutputs.ipv6Address;

// Tailscale hostname (manual - will need to be updated after first deploy)
export const tailscaleHostname = pulumi.output("openclaw-gateway.tailXXXXX.ts.net");

// Security reminder
export const securityNote = pulumi.output(
  "Gateway is accessible via Tailscale only. Run verification commands after deploy."
);
```

**Step 3: Update package.json main entry**

Update `infra/package.json` to point to `src/index.ts`:

```json
{
  "main": "src/index.ts"
}
```

**Step 4: Commit**

```bash
git add infra/src/server.ts infra/src/index.ts infra/package.json
git commit -m "feat: add Hetzner server with firewall"
```

---

## Task 6: Add Tailscale Auth Key to Config

**Files:**
- Modify: `infra/Pulumi.dev.yaml`

**Step 1: Generate Tailscale auth key**

Go to https://login.tailscale.com/admin/settings/keys and create a reusable auth key.

**Step 2: Add to Pulumi config**

```bash
cd infra
pulumi config set --secret tailscale:authKey "<YOUR_TAILSCALE_AUTH_KEY>"
```

**Step 3: Verify config**

Run: `pulumi config`
Expected: Shows `tailscale:authKey` as `[secret]`

**Step 4: Commit**

```bash
git add infra/Pulumi.dev.yaml
git commit -m "feat: add Tailscale auth key to config"
```

---

## Task 7: Create Deployment Scripts

**Files:**
- Create: `infra/scripts/deploy.sh`
- Create: `infra/scripts/verify-security.sh`
- Create: `infra/scripts/logs.sh`

**Step 1: Create deploy script**

Create `infra/scripts/deploy.sh`:

```bash
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
```

**Step 2: Create security verification script**

Create `infra/scripts/verify-security.sh`:

```bash
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
```

**Step 3: Create logs script**

Create `infra/scripts/logs.sh`:

```bash
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
```

**Step 4: Make scripts executable**

```bash
chmod +x infra/scripts/*.sh
```

**Step 5: Commit**

```bash
git add infra/scripts/
git commit -m "feat: add deployment and verification scripts"
```

---

## Task 8: Update .gitignore

**Files:**
- Modify: `.gitignore`

**Step 1: Add Pulumi ignores**

Add to `.gitignore`:

```gitignore
# Pulumi
infra/node_modules/
infra/.pulumi/
```

**Step 2: Commit**

```bash
git add .gitignore
git commit -m "chore: add Pulumi directories to gitignore"
```

---

## Task 9: Test Pulumi Preview

**Files:**
- None (verification only)

**Step 1: Install dependencies**

```bash
cd infra && npm install
```

**Step 2: Login to Pulumi**

```bash
pulumi login
```

**Step 3: Select or create stack**

```bash
cd infra && pulumi stack select dev || pulumi stack init dev
```

**Step 4: Run preview**

Run: `cd infra && pulumi preview`
Expected: Shows resources to be created:
- `hcloud:index:SshKey` openclaw-ssh-key
- `hcloud:index:Server` openclaw-gateway
- `hcloud:index:Firewall` openclaw-firewall
- `hcloud:index:FirewallAttachment` openclaw-fw-attachment

**Step 5: Commit any config changes**

```bash
git add infra/
git commit -m "chore: finalize Pulumi configuration"
```

---

## Task 10: Deploy Infrastructure

**Files:**
- None (deployment)

**Step 1: Run deployment**

```bash
cd infra && ./scripts/deploy.sh
```

Expected: Server created, outputs displayed

**Step 2: Wait for cloud-init**

```bash
# Wait 2-3 minutes, then check cloud-init status
IP=$(cd infra && pulumi stack output ipv4Address)
ssh openclaw@$IP "cloud-init status --wait"
```

Expected: `status: done`

**Step 3: Run security verification**

```bash
cd infra && ./scripts/verify-security.sh
```

Expected: All checks pass

**Step 4: No commit needed (infrastructure deployed)**

---

## Task 11: Clean Up Old openclaw Directory

**Files:**
- Remove: `openclaw/Dockerfile`
- Remove: `openclaw/scripts/`
- Remove: `openclaw/config/`
- Preserve: `openclaw/skills/`
- Preserve: `openclaw/workspaces/`
- Remove: `openclaw/.env` (secrets now in Pulumi)

**Step 1: Backup current .env one more time**

```bash
cp openclaw/.env ~/.openclaw-env-backup-$(date +%Y%m%d)
echo "Backed up to ~/.openclaw-env-backup-$(date +%Y%m%d)"
```

**Step 2: Remove old deployment files**

```bash
rm -rf openclaw/Dockerfile
rm -rf openclaw/scripts/
rm -rf openclaw/config/
rm -f openclaw/.env
rm -f openclaw/.env.example
rm -f openclaw/README.md
```

**Step 3: Keep skills and workspaces**

```bash
# These should remain for reference/sync
ls openclaw/skills/
ls openclaw/workspaces/
```

**Step 4: Update docker-compose.yml**

Remove the `openclaw` service from `docker-compose.yml` since it's now managed by Pulumi. Keep `quant-trading` and `postgres` for local development.

**Step 5: Commit**

```bash
git add -A
git commit -m "refactor: remove old Docker deployment, infrastructure now in Pulumi"
```

---

## Task 12: Create Skills Sync Script

**Files:**
- Create: `infra/scripts/sync-skills.sh`

**Step 1: Create sync script**

Create `infra/scripts/sync-skills.sh`:

```bash
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
```

**Step 2: Make executable**

```bash
chmod +x infra/scripts/sync-skills.sh
```

**Step 3: Commit**

```bash
git add infra/scripts/sync-skills.sh
git commit -m "feat: add skills sync script for Pulumi deployment"
```

---

## Task 13: Update CLAUDE.md

**Files:**
- Modify: `CLAUDE.md`

**Step 1: Update deployment section**

Update `CLAUDE.md` to reflect new Pulumi-based deployment:

```markdown
## Deployment (Pulumi)

Infrastructure is managed with Pulumi in `infra/`.

### Prerequisites

```bash
brew install pulumi
cd infra && npm install
pulumi login
```

### Deploy

```bash
cd infra && ./scripts/deploy.sh
```

### Verify Security

```bash
cd infra && ./scripts/verify-security.sh
```

### View Logs

```bash
cd infra && ./scripts/logs.sh [service]
```

### Sync Skills

```bash
cd infra && ./scripts/sync-skills.sh
```

### Secrets Management

Secrets are stored encrypted in Pulumi config:

```bash
cd infra
pulumi config set --secret <namespace>:<key> <value>
```

Available namespaces: `openclaw`, `anthropic`, `github`, `ynab`, `telegram`, `tailscale`
```

**Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: update CLAUDE.md with Pulumi deployment instructions"
```

---

## Task 14: Final Verification

**Files:**
- None (verification only)

**Step 1: Verify gateway via Tailscale**

```bash
# Get Tailscale hostname from admin console or:
tailscale status

# Test gateway access via Tailscale
curl -s -H "Authorization: Bearer $(pulumi config get openclaw:gatewayToken --show-secrets)" \
  https://openclaw-gateway.tailXXXXX.ts.net:18789/health
```

Expected: Health check response

**Step 2: Verify gateway NOT accessible via public IP**

```bash
IP=$(cd infra && pulumi stack output ipv4Address)
curl -s --connect-timeout 3 "http://$IP:18789/" && echo "FAIL" || echo "PASS: Gateway not exposed"
```

Expected: `PASS: Gateway not exposed`

**Step 3: Test Telegram bot**

Send a message to your Telegram bot and verify it responds.

**Step 4: Final commit**

```bash
git add -A
git commit -m "feat: complete Pulumi infrastructure migration"
```

---

## Post-Migration Checklist

- [ ] Server deployed and running
- [ ] Gateway bound to loopback only (verified)
- [ ] UFW firewall active
- [ ] Tailscale connected
- [ ] Gateway accessible via Tailscale
- [ ] Gateway NOT accessible via public IP
- [ ] Docker container running with security constraints
- [ ] File permissions correct (600/700)
- [ ] Telegram bot responding
- [ ] Old `.env` backed up and removed from repo
- [ ] CLAUDE.md updated

---

## Rollback Procedure

If issues occur:

```bash
# Destroy Pulumi resources
cd infra && pulumi destroy

# Restore old deployment
git checkout HEAD~1 -- openclaw/
git checkout HEAD~1 -- docker-compose.yml

# Redeploy with old method
cd openclaw && ./scripts/deploy.sh
```
