# OpenClaw Docker Deployment

Docker configuration for running OpenClaw gateway on a remote server.

## Prerequisites

- Docker and Docker Compose installed on the server
- Tailscale installed and configured on the server
- SSH access configured (alias: `buckbot`)

## Quick Start

```bash
# Copy environment template
cp .env.example .env
# Edit .env with your API keys

# Deploy to server
./scripts/deploy.sh
```

## Setup

1. Copy the environment file and configure:
   ```bash
   cp .env.example .env
   # Edit .env with your values
   ```

2. Copy config examples:
   ```bash
   cp config/openclaw.json.example config/openclaw.json
   # Edit config/openclaw.json - add your Telegram bot token
   ```

3. Configure Tailscale Serve (on the server):
   ```bash
   tailscale serve --bg --https=443 http://localhost:18789
   ```

4. Deploy:
   ```bash
   ./scripts/deploy.sh
   ```

## Deployment Scripts

| Script | Purpose |
|--------|---------|
| `scripts/deploy.sh` | Push to GitHub, pull on server, restart all services |
| `scripts/logs.sh` | Tail logs from server (optionally filter by service) |
| `scripts/sync-skills.sh` | Quick skill sync without full restart |

### Usage

```bash
# Full deploy
./scripts/deploy.sh

# View all logs
./scripts/logs.sh

# View specific service logs
./scripts/logs.sh buckbot quant-trading

# Sync skills only
./scripts/sync-skills.sh
```

## Server Directory Structure

```
~/agents/                    # Git clone of this repo
├── docker-compose.yml       # Orchestrates all services
├── openclaw/
│   └── skills/              # Skills mounted into container
├── quant-trading/
└── workspace/               # Agent workspace (mounted volume)
```

## Configuration

The gateway config is stored in the Docker volume at `/home/node/.openclaw/openclaw.json`.

### Key Settings

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
| `compaction.reserveTokensFloor` | Always keeps 20k tokens headroom |
| `compaction.memoryFlush.enabled` | Proactively flushes memories before compaction |
| `session.reset.mode: "daily"` | Resets sessions at 4am daily |
| `session.reset.idleMinutes: 120` | Also resets after 2 hours idle |

## Adding Skills

Create a new directory under `skills/` with a `SKILL.md` file:

```
skills/
├── quant-trading/
│   └── SKILL.md
└── new-skill/
    └── SKILL.md
```

After adding skills, sync them:
```bash
./scripts/sync-skills.sh
ssh buckbot "cd ~/agents && docker compose restart openclaw"
```

## Multi-Agent Setup

This gateway supports multiple isolated agents, each with its own Telegram bot.

### Quick Setup

1. Create 3 Telegram bots via @BotFather
2. Add tokens to `.env`:
   ```bash
   TELEGRAM_BUCKBOT_TOKEN=your_token
   TELEGRAM_EXPENSE_TOKEN=your_token
   TELEGRAM_QUANT_TOKEN=your_token
   ```
3. Copy multi-agent config:
   ```bash
   cp config/openclaw.multi-agent.json.example config/openclaw.json
   ```
4. Deploy: `./scripts/deploy.sh`

### Agents

| Agent | Workspace | Purpose |
|-------|-----------|---------|
| buckbot | `workspaces/buckbot/` | General assistant |
| expense | `workspaces/expense/` | Oracle Expenses |
| quant | `workspaces/quant/` | Trading |

### ExpenseBot Browser Setup

ExpenseBot uses Playwright Connect to control a browser on your local machine (for Okta Passkey auth).

On your Mac:
```bash
npx playwright run-server --port 3000 --host 0.0.0.0
```

The bot connects via Tailscale to `ws://<your-mac>:3000`.

## Troubleshooting

### Session Bloat / Rate Limit Errors

If you see `HTTP 429 rate_limit_error`:

1. Clear the session on the server:
   ```bash
   ssh buckbot "docker exec agents-openclaw-1 rm /home/node/.openclaw/agents/main/sessions/*.jsonl"
   ```

2. Restart:
   ```bash
   ssh buckbot "cd ~/agents && docker compose restart openclaw"
   ```

### Check Logs

```bash
# Tail live logs
./scripts/logs.sh

# Or manually
ssh buckbot "cd ~/agents && docker compose logs --tail=50 openclaw"
```
