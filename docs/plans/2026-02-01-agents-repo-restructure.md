# Agents Repo Restructure — Design Document

**Date:** 2026-02-01
**Status:** Ready for Implementation
**Goal:** Restructure quant-superpowers into a clean multi-agent monorepo called `agents`

---

## Overview

Reorganize the current `quant-superpowers` repo into a logical multi-agent structure:

- **openclaw/** — The OpenClaw bot (orchestrator, formerly moltbot)
- **quant-trading/** — Trading API that OpenClaw calls via skills

Architecture: OpenClaw is the "brain" that has skills to call the quant-trading API. Both run on the same VM via a single docker-compose.

---

## Target Directory Structure

```
agents/
├── CLAUDE.md                     # AI context: navigation, deployment, operations
├── docker-compose.yml            # All services: openclaw, quant-trading, postgres
├── .env.example                  # Shared env template (no secrets)
├── .gitignore
│
├── openclaw/                     # OpenClaw bot
│   ├── Dockerfile
│   ├── .env.example              # OpenClaw-specific env template
│   ├── README.md
│   ├── config/
│   │   ├── openclaw.json.example
│   │   └── auth-profiles.json.example
│   ├── scripts/
│   │   ├── deploy.sh             # SSH + pull + docker compose up
│   │   ├── logs.sh               # Tail remote logs
│   │   └── sync-skills.sh        # Quick skill sync without restart
│   └── skills/
│       └── quant-trading/
│           └── SKILL.md          # Skill to call quant API
│
├── quant-trading/                # Trading API
│   ├── Dockerfile
│   ├── quant_trading/            # Python package (renamed from quant)
│   │   ├── __init__.py
│   │   ├── api.py
│   │   ├── engine.py
│   │   ├── broker.py
│   │   ├── config.py
│   │   ├── data.py
│   │   ├── models.py
│   │   ├── risk.py
│   │   ├── strategy.py
│   │   └── strategies/
│   │       ├── __init__.py
│   │       └── momentum_breakout.py
│   ├── tests/
│   ├── pyproject.toml
│   └── README.md
│
├── docs/
│   └── plans/                    # Design documents
│
└── README.md                     # Monorepo overview
```

---

## Docker Compose

Single compose file at root orchestrates all services:

```yaml
services:
  openclaw:
    build: ./openclaw
    ports:
      - "18789:18789"
    volumes:
      - openclaw-state:/home/node/.openclaw
      - ./openclaw/skills:/home/node/skills:ro
    environment:
      - ANTHROPIC_API_KEY
      - OPENCLAW_GATEWAY_TOKEN
    depends_on:
      - quant-trading

  quant-trading:
    build: ./quant-trading
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@postgres:5432/quant
      - ALPACA_API_KEY
      - ALPACA_SECRET_KEY
    depends_on:
      - postgres

  postgres:
    image: postgres:16-alpine
    volumes:
      - postgres-data:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=quant
      - POSTGRES_PASSWORD=postgres

volumes:
  openclaw-state:
  postgres-data:
```

**Inter-service communication:** OpenClaw reaches quant-trading at `http://quant-trading:8000` on the internal Docker network.

---

## CLAUDE.md Content

The `CLAUDE.md` file provides AI assistants with operational context:

### 1. Repo Overview
- Multi-agent monorepo
- OpenClaw = orchestrator bot with skills
- quant-trading = trading API called by OpenClaw

### 2. Directory Navigation
- `openclaw/` — Bot configuration, Dockerfile, skills, deployment scripts
- `quant-trading/` — Python trading engine
- `docs/plans/` — Design documents

### 3. Development Workflow
```bash
# Run locally
docker compose up -d

# Run quant-trading standalone for dev
cd quant-trading && uv run uvicorn quant_trading.api:app --reload

# Run tests
cd quant-trading && uv run pytest
```

### 4. Deployment Workflow (Git-First)
**Always update the repo before the server:**

1. Make changes locally
2. Test locally with `docker compose up`
3. Commit and push to GitHub
4. SSH to server and pull changes
5. Restart services

```bash
# Deploy using script
cd openclaw && ./scripts/deploy.sh

# Or manually
git add . && git commit -m "description" && git push
ssh buckbot "cd ~/agents && git pull && docker compose up -d --build"
```

### 5. Server Access
```bash
# SSH to server
ssh buckbot

# View logs (or use script)
cd openclaw && ./scripts/logs.sh

# Manual log access
docker compose logs -f openclaw
docker compose logs -f quant-trading
```

### 6. Safety Guidelines
- Never commit `.env` files or secrets
- Always test locally before deploying
- Update git repo before updating server
- Review database migrations before applying

---

## OpenClaw Scripts

### deploy.sh
```bash
#!/bin/bash
# Deploy agents to server
set -e

echo "Pushing to GitHub..."
git push

echo "Deploying to server..."
ssh buckbot "cd ~/agents && git pull && docker compose up -d --build"

echo "Deployment complete. Checking logs..."
ssh buckbot "docker compose logs --tail=20"
```

### logs.sh
```bash
#!/bin/bash
# Tail logs from server
ssh buckbot "cd ~/agents && docker compose logs -f"
```

### sync-skills.sh
```bash
#!/bin/bash
# Quick skill sync without full restart
set -e
rsync -avz ./skills/ buckbot:~/agents/openclaw/skills/
echo "Skills synced. Restart openclaw to pick up changes:"
echo "  ssh buckbot 'cd ~/agents && docker compose restart openclaw'"
```

---

## Migration Tasks

### Task 1: Create Directory Structure
```bash
cd /path/to/quant-superpowers

# Create new structure
mkdir -p openclaw/{config,scripts,skills/quant-trading}
mkdir -p quant-trading/quant_trading/strategies
mkdir -p quant-trading/tests
mkdir -p docs/plans
```

### Task 2: Migrate OpenClaw
- Keep existing `openclaw/Dockerfile`
- Move `openclaw/docker-compose.yml` services → root `docker-compose.yml`
- Create `openclaw/.env.example`
- Create `openclaw/config/openclaw.json.example`
- Create `openclaw/config/auth-profiles.json.example`
- Create `openclaw/scripts/deploy.sh`
- Create `openclaw/scripts/logs.sh`
- Create `openclaw/scripts/sync-skills.sh`
- Create `openclaw/skills/quant-trading/SKILL.md`
- Create `openclaw/README.md`

### Task 3: Migrate Quant-Trading
- Move `src/quant/*.py` → `quant-trading/quant_trading/`
- Move `src/quant/strategies/` → `quant-trading/quant_trading/strategies/`
- Move `tests/` → `quant-trading/tests/`
- Move `pyproject.toml` → `quant-trading/pyproject.toml`
- **Rename package:** Update all imports from `quant.` to `quant_trading.`
- Update `pyproject.toml` package name and paths
- Create `quant-trading/Dockerfile`
- Create `quant-trading/README.md`

### Task 4: Create Root Files
- Create `docker-compose.yml` (combined services + postgres)
- Create `.env.example`
- Create `CLAUDE.md`
- Create `README.md`
- Update `.gitignore`

### Task 5: Clean Up Old Files
- Delete `src/` directory
- Delete `api/` directory (confirm if still needed)
- Delete old root `docker-compose.yml`
- Delete `openclaw/docker-compose.yml`

### Task 6: Test
```bash
# Verify tests pass
cd quant-trading && uv sync && uv run pytest

# Verify docker compose works
docker compose up -d
docker compose logs

# Test inter-service communication
curl http://localhost:8000/health
```

### Task 7: Update Git Remote
```bash
git remote set-url origin git@github.com:bbuckland/agents.git
git push -u origin main
```

---

## Quant-Trading Skill

**`openclaw/skills/quant-trading/SKILL.md`:**

```markdown
---
name: quant-trading
description: Trading recommendations and portfolio management for F100 stocks
---

# Quant Trading

You help manage a quantitative trading system.

## API Base URL
http://quant-trading:8000

## Endpoints

### GET /api/analyze
Returns today's trading recommendations with rationale.

### POST /api/execute
Execute approved trades.
Body: `{"trades": [{"ticker": "AAPL", "action": "buy", "size": 800}]}`

### GET /api/positions
Returns current open positions.

### GET /api/portfolio
Returns portfolio summary with P&L.

## Usage
- Morning: Call /api/analyze to get recommendations
- Review recommendations with user before executing
- Never auto-execute trades without explicit approval
```

---

## Decisions Summary

| Question | Decision |
|----------|----------|
| Git history? | Fresh repo structure, push to bbuckland/agents |
| Docker architecture? | OpenClaw calls quant-trading API |
| Compose structure? | Single docker-compose at root |
| Package naming? | Rename `quant` → `quant_trading` |
| Database? | Include postgres in docker-compose |

---

*Document version: 1.0*
*Created: 2026-02-01*
