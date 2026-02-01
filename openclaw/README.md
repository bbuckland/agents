# OpenClaw Docker Deployment

Docker configuration for running OpenClaw gateway on a remote server (e.g., Hetzner VPS).

## Prerequisites

- Docker and Docker Compose installed on the server
- Tailscale installed and configured on the server
- Tailscale installed on your Mac (for Tailscale Serve authentication)

## Setup

1. Copy the environment file and configure:
   ```bash
   cp .env.example .env
   # Edit .env with your values
   ```

2. Create the data directories on your server:
   ```bash
   mkdir -p /home/clawd/clawdbot-state
   mkdir -p /home/clawd/clawdbot-workspace
   mkdir -p /home/clawd/clawdbot-docker
   ```

3. Configure Tailscale Serve (on the server):
   ```bash
   tailscale serve --bg --https=443 http://localhost:18789
   ```

4. Check for drift (optional):
   ```bash
   ./drift.sh buckbot  # Compare local vs server config
   ```

5. Deploy using the deploy script:
   ```bash
   ./deploy.sh buckbot  # or your SSH hostname
   ```

   The deploy script:
   - Syncs `openclaw.json` (preserves server-side Telegram bot token)
   - Syncs Docker files and `.env`
   - Rebuilds and restarts the gateway

## Initial Server Setup

On first deploy, manually set the Telegram bot token on the server:
```bash
ssh buckbot
cd /home/clawd/clawdbot-state
jq '.channels.telegram.botToken = "YOUR_BOT_TOKEN"' openclaw.json > tmp.json && mv tmp.json openclaw.json
```

## Connecting from Mac

1. Log into Tailscale on your Mac (same account as server)
2. In OpenClaw Mac app, use "Direct (ws/wss)" with:
   - URL: `wss://your-server.tailnet-name.ts.net/`
3. Approve device pairing when prompted:
   ```bash
   docker exec <container> node dist/index.js devices list
   docker exec <container> node dist/index.js devices approve <request-id>
   ```

## Adding Skills

To add more skills, edit the `Dockerfile` to install required CLIs:

```dockerfile
# System packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    gh \
    jq \
    && rm -rf /var/lib/apt/lists/*

# NPM packages
RUN npm install -g @steipete/summarize
```

Then rebuild:
```bash
docker compose build --no-cache
docker compose up -d
```

## Configuration

The gateway config is stored in `${OPENCLAW_CONFIG_DIR}/openclaw.json`. See `openclaw.json.example` for a complete template.

### Key Settings

#### Gateway (Tailscale Serve)
```json
{
  "gateway": {
    "bind": "loopback",
    "tailscale": { "mode": "serve" },
    "auth": { "allowTailscale": true },
    "trustedProxies": ["0.0.0.0/0", "::/0", "127.0.0.1", "::1"]
  }
}
```

#### Context Management (Prevent Session Bloat)
```json
{
  "agents": {
    "defaults": {
      "contextTokens": 100000,
      "compaction": {
        "mode": "safeguard",
        "reserveTokensFloor": 20000,
        "memoryFlush": {
          "enabled": true,
          "softThresholdTokens": 30000
        }
      }
    }
  },
  "session": {
    "scope": "per-sender",
    "reset": {
      "mode": "daily",
      "atHour": 4,
      "idleMinutes": 120
    }
  }
}
```

| Setting | Purpose |
|---------|---------|
| `contextTokens: 100000` | Limits context window (default 200k is too large) |
| `compaction.reserveTokensFloor` | Always keeps 20k tokens headroom for new messages |
| `compaction.memoryFlush.enabled` | Proactively flushes memories to disk before compaction |
| `session.reset.mode: "daily"` | Resets sessions at 4am daily to prevent bloat |
| `session.reset.idleMinutes: 120` | Also resets after 2 hours idle |

#### Model Configuration
```json
{
  "agents": {
    "defaults": {
      "model": {
        "primary": "anthropic/claude-sonnet-4-20250514",
        "fallbacks": ["anthropic/claude-sonnet-4-20250514", "anthropic/claude-opus-4-5"]
      }
    }
  }
}
```

## Troubleshooting

### Session Bloat / Rate Limit Errors

If you see `HTTP 429 rate_limit_error` or context overflow errors:

1. Clear the session:
   ```bash
   docker exec <container> rm /home/node/.openclaw/agents/main/sessions/*.jsonl
   ```

2. Restart the gateway:
   ```bash
   docker compose restart
   ```

3. Ensure context management settings are configured (see above)

### Check Logs
```bash
docker logs <container> --tail 50
# Or inside container:
docker exec <container> cat /tmp/openclaw/openclaw-$(date +%Y-%m-%d).log | tail -30
```
