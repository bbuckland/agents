# Agents Monorepo

Multi-agent system built on OpenClaw (orchestrator).

Trading lives in `bbuckland/monorepo` (`apps/quant-engine`, next to the YNAB MCP); see `docs/plans/agentic-trading-layer.md` there.

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
└── docs/plans/         # Design documents
```

## Architecture

- **OpenClaw** runs on Hetzner (managed by Pulumi), accessible via Tailscale
- Gateway: `https://openclaw-gateway.tail9150d4.ts.net/`
- Server IP: `46.225.98.142` (cax11 ARM64, Nuremberg)

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
4. **Preview before deploying** — Run `pulumi preview` in `infra/` first

## Multi-Agent Setup

The gateway runs multiple isolated agents, each with its own Telegram bot:

| Agent | Bot | Purpose |
|-------|-----|---------|
| buckbot | @BuckBot | General assistant + agent monitor |
| expense | @ExpenseBot | Oracle Expenses automation |

QuantBot (@QuantBot) is retired: its workspace and skill were removed from this repo. Its Telegram token is still wired in `infra/` (`src/config.ts` requires the `quantToken` secret; `src/cloud-init.ts` writes it to the server `.env`), so a rebuild re-provisions it until those lines are removed. Do not delete the `quantToken` Pulumi secret on its own: `pulumi up` would fail. The quant agent's workspace and config on the running server are untouched until someone removes them there.

### Workspaces

Each agent has isolated workspace in `openclaw/workspaces/<agent>/`:
- `SOUL.md` - Agent persona
- Agent-specific files (reports, notes, etc.)

### Skills

- `openclaw/skills/expense/` - Used by ExpenseBot
- `openclaw/skills/agent-status/` - Used by BuckBot for monitoring

## Pull requests (standing instruction from the owner)

The owner does not review PRs. For every PR Claude opens in this repo:

1. Before opening it, and again after large changes, run a critic subagent on Claude Opus over the full diff against `main`. Ask it for correctness bugs, security issues, broken config or infra changes and misleading docs, ranked by severity.
2. Resolve every finding: fix it, or note in the PR why it doesn't apply.
3. Once CI (if any) is green and all findings are resolved, mark the PR ready and squash-merge it without waiting for human review.
