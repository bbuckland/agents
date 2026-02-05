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
      - ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIDjcfBksKxpPQMoiw7zq1OvBiQHJM97WlfgnXCv3EZjB buckbot

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
