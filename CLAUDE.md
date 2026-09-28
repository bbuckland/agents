# Agents Monorepo

Multi-agent system with OpenClaw (orchestrator) and quant-trading (API).

## Structure

```
agents/
├── infra/              # Pulumi infrastructure (Hetzner deployment)
│   ├── src/            # TypeScript modules
│   ├── scripts/        # Deploy, verify, logs, sync scripts
│   └── Pulumi.yaml     # Project config
├── openclaw/           # OpenClaw skills and workspaces
│   ├── skills/         # Bot skills
│   └── workspaces/     # Agent personas
├── quant-trading/      # Trading API (moved to monorepo apps/quant-engine; frozen)
│   ├── quant_trading/  # Python package
│   ├── tests/
│   └── Dockerfile
├── docker-compose.yml  # Local dev (quant-trading + postgres)
└── docs/plans/         # Design documents
```

## Architecture

- **OpenClaw** runs on Hetzner (managed by Pulumi), accessible via Tailscale
- **quant-trading** is a FastAPI service for local development
- Gateway: `https://openclaw-gateway.tail9150d4.ts.net/`
- Server IP: `46.225.98.142` (cax11 ARM64, Nuremberg)

## Local Development

```bash
# Run quant-trading locally
docker compose up -d

# Run quant-trading standalone
cd quant-trading && uv run uvicorn quant_trading.api:app --reload

# Run tests
cd quant-trading && uv run pytest
```

## Deployment (Pulumi)

Infrastructure is managed with Pulumi in `infra/`.

### Prerequisites

```bash
brew install pulumi/tap/pulumi
cd infra && pnpm install
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

Secrets are stored encrypted in Pulumi Cloud:

```bash
cd infra
pulumi config set --secret <namespace>:<key> <value>
```

Available namespaces: `openclaw`, `anthropic`, `github`, `ynab`, `telegram`, `tailscale`, `hcloud`

## Server Access

```bash
# SSH to server
ssh openclaw@46.225.98.142

# Via Tailscale (if on same tailnet)
ssh openclaw@openclaw-gateway

# View container status
ssh openclaw@46.225.98.142 "docker compose ps"

# Restart container
ssh openclaw@46.225.98.142 "docker compose restart"
```

## Safety Guidelines

1. **Secrets in Pulumi** — All secrets stored encrypted in Pulumi Cloud
2. **Gateway on loopback** — Port 18789 only accessible via Tailscale
3. **UFW firewall** — Only SSH (22) allowed from public internet
4. **Test locally first** — Run `docker compose up` before deploying

## Multi-Agent Setup

The gateway runs multiple isolated agents, each with its own Telegram bot:

| Agent | Bot | Purpose |
|-------|-----|---------|
| buckbot | @BuckBot | General assistant + agent monitor |
| expense | @ExpenseBot | Oracle Expenses automation |
| quant | @QuantBot | Trading assistant |

### Workspaces

Each agent has isolated workspace in `openclaw/workspaces/<agent>/`:
- `SOUL.md` - Agent persona
- Agent-specific files (reports, notes, etc.)

### Skills

- `openclaw/skills/quant-trading/` - Used by QuantBot and BuckBot
- `openclaw/skills/expense/` - Used by ExpenseBot
- `openclaw/skills/agent-status/` - Used by BuckBot for monitoring
