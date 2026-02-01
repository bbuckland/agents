# Agents Monorepo — Design Document

**Date:** 2026-01-28
**Status:** Draft
**Goal:** Consolidate buckbot and quant-superpowers into a unified agents monorepo

---

## Overview

Merge two existing repositories into a single multi-agent monorepo called `agents`:

1. **buckbot** (existing) → becomes `moltbot/` agent
2. **quant-superpowers** (existing) → becomes `quant-trading/` agent
3. **dashboard** (new) → shared analytics dashboard
4. **Future agents** — extensible structure

---

## Current State

### buckbot repo (`~/Documents/personal/buckbot`)
- `docs/SERVER-SETUP.md` — Detailed Hetzner deployment docs
- `docs/plans/` — Deployment design and implementation plans
- Server already running at `178.156.160.63` (ssh alias: `buckbot`)
- Docker deployment with `moltbot:local` image
- Telegram bot `@buck94_bot`

### quant-superpowers repo (`~/Documents/personal/code/quant-superpowers`)
- `src/quant/` — Python trading engine
- `tests/` — Test suite
- `docs/plans/` — System design and phase plans
- Phase 1 complete, Phase 2 in planning

### Server Structure (Hetzner)
```
/home/clawd/
├── clawdbot-docker/          # Docker project (git clone of moltbot source)
│   ├── docker-compose.yml
│   ├── .env
│   └── Dockerfile
├── clawdbot-state/           # Persistent config (mounted volume)
│   ├── moltbot.json
│   ├── auth-profiles.json
│   └── agents/
└── clawdbot-workspace/       # Agent workspace (mounted volume)
```

---

## Target Directory Structure

```
agents/
├── moltbot/                    # Moltbot agent (from buckbot repo)
│   ├── skills/                 # Skill definitions
│   │   ├── quant-trading/
│   │   │   └── SKILL.md        # Calls quant API
│   │   └── .../
│   ├── deploy/
│   │   ├── docker-compose.yml  # From server
│   │   ├── .env.example        # Template (no secrets)
│   │   └── Dockerfile          # If custom build needed
│   ├── config/
│   │   ├── moltbot.json.example
│   │   └── auth-profiles.json.example
│   ├── scripts/
│   │   ├── deploy.sh           # SSH + docker compose up
│   │   ├── logs.sh             # Tail remote logs
│   │   └── sync-skills.sh      # Quick skill sync
│   ├── docs/
│   │   └── SERVER-SETUP.md     # From buckbot repo
│   └── README.md
│
├── quant-trading/              # Quant trading agent (from quant-superpowers)
│   ├── src/quant/              # Python engine
│   ├── tests/
│   ├── alembic/                # DB migrations (Phase 2)
│   ├── pyproject.toml
│   └── README.md
│
├── dashboard/                  # Shared dashboard (Phase 3)
│   ├── src/
│   ├── package.json
│   └── README.md
│
├── shared/                     # Shared utilities (future)
│   └── python/
│
├── docs/
│   └── plans/                  # Design docs for the monorepo
│       ├── 2026-01-28-agents-monorepo-design.md
│       ├── 2026-01-28-quant-superpowers-design.md
│       └── .../
│
├── .github/
│   └── workflows/              # CI/CD per agent
│
├── README.md                   # Monorepo overview
└── .gitignore
```

---

## Migration Plan

### Task 1: Create Fresh Repo Structure

Start with the new `bbuckland/agents` GitHub repo (already created).

**Actions:**
1. Clone `bbuckland/agents` locally
2. Create directory structure:
   ```
   mkdir -p moltbot/{skills,deploy,config,scripts,docs}
   mkdir -p quant-trading
   mkdir -p dashboard
   mkdir -p shared/python
   mkdir -p docs/plans
   mkdir -p .github/workflows
   ```

---

### Task 2: Migrate Moltbot Content

**Actions:**
1. Copy buckbot docs:
   - `buckbot/docs/SERVER-SETUP.md` → `moltbot/docs/SERVER-SETUP.md`
   - `buckbot/docs/plans/*` → `docs/plans/` (keep for history)

2. Fetch deploy files from server:
   ```bash
   scp buckbot:/home/clawd/clawdbot-docker/docker-compose.yml moltbot/deploy/
   scp buckbot:/home/clawd/clawdbot-docker/.env moltbot/deploy/.env.example
   # Scrub secrets from .env.example
   ```

3. Create config examples (scrubbed):
   ```bash
   scp buckbot:/home/clawd/clawdbot-state/moltbot.json moltbot/config/moltbot.json.example
   # Remove bot tokens, API keys
   ```

4. Create deployment scripts (see below)

---

### Task 3: Migrate Quant-Trading Content

**Actions:**
1. Copy from quant-superpowers:
   - `src/quant/` → `quant-trading/src/quant/`
   - `tests/` → `quant-trading/tests/`
   - `pyproject.toml` → `quant-trading/pyproject.toml`
   - `.env.example` → `quant-trading/.env.example`

2. Move design docs:
   - `docs/plans/2026-01-28-quant-superpowers-design.md` → `docs/plans/`
   - `docs/plans/2026-01-28-phase*.md` → `docs/plans/`

3. Update Python paths in `pyproject.toml` if needed

4. Verify tests pass from new location:
   ```bash
   cd quant-trading && uv run pytest
   ```

---

### Task 4: Create Deployment Scripts

**moltbot/scripts/deploy.sh:**
```bash
#!/bin/bash
# Deploy moltbot to Hetzner server
set -e

SERVER="buckbot"
REMOTE_DIR="/home/clawd/clawdbot-docker"

echo "Deploying moltbot to $SERVER..."

# Sync skills to server
rsync -avz --delete ./skills/ $SERVER:$REMOTE_DIR/skills/

# Restart container
ssh $SERVER "cd $REMOTE_DIR && docker compose pull && docker compose up -d"

echo "Deployment complete. Checking logs..."
ssh $SERVER "docker logs --tail=20 clawdbot-docker-moltbot-gateway-1"
```

**moltbot/scripts/logs.sh:**
```bash
#!/bin/bash
# Tail moltbot logs
ssh buckbot "docker logs -f clawdbot-docker-moltbot-gateway-1"
```

**moltbot/scripts/sync-skills.sh:**
```bash
#!/bin/bash
# Quick skill sync without restart
rsync -avz ./skills/ buckbot:/home/clawd/clawdbot-docker/skills/
echo "Skills synced"
```

---

### Task 5: Create Quant-Trading Skill for Moltbot

**moltbot/skills/quant-trading/SKILL.md:**
```markdown
---
name: quant-trading
description: Daily trading recommendations and portfolio management
---

# Quant Trading Assistant

You help manage a quantitative trading system for F100 stocks.

## API Base URL
${QUANT_API_URL:-http://localhost:8000}

## Tools

### get_recommendations
GET /api/analyze
Returns today's trading recommendations with rationale.

### approve_trades
POST /api/execute
Body: {"trades": [{"ticker": "AAPL", "action": "buy", "size": 800}]}

### check_positions
GET /api/positions
Returns current open positions.

### portfolio_status
GET /api/portfolio
Returns portfolio summary.

## Schedule
- 6:00 AM ET: Morning briefing (get_recommendations)
- 4:00 PM ET: EOD summary (portfolio_status)
```

---

### Task 6: Create Root README

**README.md:**
```markdown
# Agents

Monorepo for AI agent projects.

## Agents

| Agent | Description | Status |
|-------|-------------|--------|
| [moltbot](./moltbot) | Personal AI assistant via Telegram | Active |
| [quant-trading](./quant-trading) | Automated F100 stock trading | Development |
| [dashboard](./dashboard) | Shared analytics dashboard | Planned |

## Quick Start

### Moltbot
```bash
cd moltbot
./scripts/deploy.sh    # Deploy to Hetzner
./scripts/logs.sh      # View logs
```

### Quant Trading
```bash
cd quant-trading
uv sync
uv run pytest
uv run uvicorn quant.api:app --reload
```

## Documentation
- [Moltbot Server Setup](./moltbot/docs/SERVER-SETUP.md)
- [Quant System Design](./docs/plans/2026-01-28-quant-superpowers-design.md)
```

---

### Task 7: Update CI/CD

**.github/workflows/quant-trading.yml:**
```yaml
name: Quant Trading CI

on:
  push:
    paths:
      - 'quant-trading/**'
  pull_request:
    paths:
      - 'quant-trading/**'

jobs:
  test:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: quant-trading
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - run: uv sync
      - run: uv run pytest
      - run: uv run mypy src/
```

---

### Task 8: Archive Old Repos

**Options:**
1. **Archive on GitHub** — Mark `quant-superpowers` and `buckbot` as archived
2. **Delete after validation** — Remove once agents repo is stable
3. **Keep as mirrors** — Useful if you want separate CI/deployment

**Recommended:** Archive after 1 week of agents repo working correctly.

---

## File Movement Summary

| Source | Destination |
|--------|-------------|
| `buckbot/docs/SERVER-SETUP.md` | `moltbot/docs/SERVER-SETUP.md` |
| `buckbot/docs/plans/*` | `docs/plans/` |
| Server: `docker-compose.yml` | `moltbot/deploy/docker-compose.yml` |
| Server: `.env` | `moltbot/deploy/.env.example` (scrubbed) |
| Server: `moltbot.json` | `moltbot/config/moltbot.json.example` (scrubbed) |
| `quant-superpowers/src/quant/` | `quant-trading/src/quant/` |
| `quant-superpowers/tests/` | `quant-trading/tests/` |
| `quant-superpowers/pyproject.toml` | `quant-trading/pyproject.toml` |
| `quant-superpowers/docs/plans/*` | `docs/plans/` |

---

## Deployment Flow (After Migration)

```
Local Development
       │
       │ git push
       ▼
GitHub (bbuckland/agents)
       │
       │ (manual for now)
       ▼
┌──────┴──────┐
│             │
▼             ▼
Hetzner       Local/Other
(moltbot)     (quant-trading)
```

**Moltbot deployment:**
```bash
cd agents/moltbot
./scripts/deploy.sh
```

**Quant-trading (local dev):**
```bash
cd agents/quant-trading
uv run uvicorn quant.api:app --reload
```

---

## Open Questions

1. **Git history:** Copy files (lose history) or use git subtree (preserve history)?
2. **Server workspace:** Should `/home/clawd/clawdbot-docker` pull from agents repo, or continue as moltbot clone with skills synced separately?
3. **Secrets management:** Continue with `.env` files or move to something like 1Password CLI / doppler?

---

*Document version: 2.0*
*Created: 2026-01-28*
