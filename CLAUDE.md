# Agents Monorepo

Multi-agent system with OpenClaw (orchestrator) and quant-trading (API).

## Structure

```
agents/
├── openclaw/           # OpenClaw bot (Telegram gateway)
│   ├── Dockerfile
│   ├── config/         # Config examples
│   ├── scripts/        # Deployment scripts
│   └── skills/         # Skills (including quant-trading)
├── quant-trading/      # Trading API
│   ├── quant_trading/  # Python package
│   ├── tests/
│   └── Dockerfile
├── docker-compose.yml  # All services
└── docs/plans/         # Design documents
```

## Architecture

- **OpenClaw** is the orchestrator bot with skills
- **quant-trading** is a FastAPI service OpenClaw calls via the `quant-trading` skill
- Both run in Docker via `docker-compose.yml`
- OpenClaw reaches quant-trading at `http://quant-trading:8000`

## Local Development

```bash
# Run everything
docker compose up -d

# Run quant-trading standalone
cd quant-trading && uv run uvicorn quant_trading.api:app --reload

# Run tests
cd quant-trading && uv run pytest
```

## Deployment (Git-First Workflow)

**Always commit and push before deploying to server.**

```bash
# 1. Make changes locally
# 2. Test locally
docker compose up -d
docker compose logs

# 3. Commit and push
git add . && git commit -m "description"
git push

# 4. Deploy to server
cd openclaw && ./scripts/deploy.sh
```

## Server Access

```bash
# SSH alias
ssh buckbot

# View logs
cd openclaw && ./scripts/logs.sh
# Or specific service:
./scripts/logs.sh buckbot quant-trading

# Manual commands on server
ssh buckbot "cd ~/agents && docker compose ps"
ssh buckbot "cd ~/agents && docker compose restart openclaw"
```

## Deployment Scripts

| Script | Purpose |
|--------|---------|
| `openclaw/scripts/deploy.sh` | Push to GitHub, pull on server, restart services |
| `openclaw/scripts/logs.sh` | Tail logs from server |
| `openclaw/scripts/sync-skills.sh` | Quick skill sync without restart |

## Safety Guidelines

1. **Never commit secrets** — `.env` files are gitignored
2. **Git-first workflow** — Always update repo before server
3. **Test locally first** — Run `docker compose up` before deploying
4. **Review database changes** — Migrations need careful review

## Adding a New Agent

1. Create directory: `new-agent/`
2. Add Dockerfile and source code
3. Add service to `docker-compose.yml`
4. Create skill in `openclaw/skills/new-agent/SKILL.md`
5. Update this CLAUDE.md

## Multi-Agent Setup

The gateway runs multiple isolated agents, each with its own Telegram bot:

| Agent | Bot | Purpose |
|-------|-----|---------|
| buckbot | @BuckBot | General assistant + agent monitor |
| expense | @ExpenseBot | Oracle Expenses automation |
| quant | @QuantBot | Trading assistant |

### Configuration

Multi-agent config: `openclaw/config/openclaw.multi-agent.json.example`

### Workspaces

Each agent has isolated workspace in `openclaw/workspaces/<agent>/`:
- `SOUL.md` - Agent persona
- Agent-specific files (reports, notes, etc.)

### Skills

- `skills/quant-trading/` - Used by QuantBot and BuckBot
- `skills/expense/` - Used by ExpenseBot
- `skills/agent-status/` - Used by BuckBot for monitoring
