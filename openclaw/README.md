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
   mkdir -p /home/user/openclaw-state
   mkdir -p /home/user/openclaw-workspace
   ```

3. Configure Tailscale Serve (on the server):
   ```bash
   tailscale serve --bg --https=443 http://localhost:18789
   ```

4. Build and start:
   ```bash
   docker compose build
   docker compose up -d
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

The gateway config is stored in `${OPENCLAW_CONFIG_DIR}/openclaw.json`. Key settings:

```json
{
  "gateway": {
    "bind": "loopback",
    "tailscale": {
      "mode": "serve"
    },
    "auth": {
      "allowTailscale": true
    },
    "trustedProxies": ["0.0.0.0/0", "::/0", "127.0.0.1", "::1"]
  }
}
```
