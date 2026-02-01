# Agents Repo Restructure — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Restructure quant-superpowers into a multi-agent monorepo with openclaw/ and quant-trading/

**Architecture:** OpenClaw is the orchestrator bot with skills to call quant-trading API. Single docker-compose at root runs all services (openclaw, quant-trading, postgres).

**Tech Stack:** Python 3.12, FastAPI, Docker, PostgreSQL, uv

---

## Task 1: Create New Directory Structure

**Files:**
- Create: `quant-trading/` directory
- Create: `quant-trading/quant_trading/` directory
- Create: `quant-trading/quant_trading/strategies/` directory
- Create: `quant-trading/tests/` directory
- Create: `openclaw/config/` directory
- Create: `openclaw/scripts/` directory
- Create: `openclaw/skills/quant-trading/` directory

**Step 1: Create all directories**

```bash
mkdir -p quant-trading/quant_trading/strategies
mkdir -p quant-trading/tests
mkdir -p openclaw/config
mkdir -p openclaw/scripts
mkdir -p openclaw/skills/quant-trading
```

**Step 2: Verify directories exist**

Run: `ls -la quant-trading/ openclaw/`

**Step 3: Commit**

```bash
git add quant-trading/.gitkeep openclaw/config/.gitkeep openclaw/scripts/.gitkeep openclaw/skills/.gitkeep
git commit -m "chore: create agents directory structure"
```

---

## Task 2: Move Python Source Files

**Files:**
- Move: `src/quant/*.py` → `quant-trading/quant_trading/`
- Move: `src/quant/strategies/*.py` → `quant-trading/quant_trading/strategies/`

**Step 1: Move main source files**

```bash
cp src/quant/__init__.py quant-trading/quant_trading/
cp src/quant/api.py quant-trading/quant_trading/
cp src/quant/broker.py quant-trading/quant_trading/
cp src/quant/config.py quant-trading/quant_trading/
cp src/quant/data.py quant-trading/quant_trading/
cp src/quant/engine.py quant-trading/quant_trading/
cp src/quant/exceptions.py quant-trading/quant_trading/
cp src/quant/models.py quant-trading/quant_trading/
cp src/quant/risk.py quant-trading/quant_trading/
cp src/quant/strategy.py quant-trading/quant_trading/
```

**Step 2: Move strategies**

```bash
cp src/quant/strategies/__init__.py quant-trading/quant_trading/strategies/
cp src/quant/strategies/momentum_breakout.py quant-trading/quant_trading/strategies/
```

**Step 3: Verify files copied**

Run: `ls -la quant-trading/quant_trading/`
Expected: All .py files listed

---

## Task 3: Update All Imports (quant → quant_trading)

**Files:**
- Modify: `quant-trading/quant_trading/*.py` (all files)
- Modify: `quant-trading/quant_trading/strategies/*.py`

**Step 1: Update imports in all files**

Find and replace in all Python files under `quant-trading/quant_trading/`:
- `from quant.` → `from quant_trading.`
- `import quant.` → `import quant_trading.`

Files to update:
- `api.py` - imports from models, engine, broker, data, config, risk
- `engine.py` - imports from models, strategy, risk
- `broker.py` - imports from models, config
- `data.py` - imports from models, config
- `risk.py` - imports from models, config
- `strategy.py` - imports from models
- `strategies/__init__.py` - imports from strategies.momentum_breakout
- `strategies/momentum_breakout.py` - imports from models, strategy

**Step 2: Verify no old imports remain**

Run: `grep -r "from quant\." quant-trading/quant_trading/ || echo "No old imports found"`
Expected: "No old imports found"

**Step 3: Commit**

```bash
git add quant-trading/quant_trading/
git commit -m "feat: move quant source to quant-trading with renamed imports"
```

---

## Task 4: Move and Update Tests

**Files:**
- Move: `tests/*.py` → `quant-trading/tests/`
- Move: `tests/test_strategies/*.py` → `quant-trading/tests/test_strategies/`
- Modify: All test files to use `quant_trading.` imports

**Step 1: Copy test files**

```bash
cp tests/__init__.py quant-trading/tests/
cp tests/test_api.py quant-trading/tests/
cp tests/test_broker.py quant-trading/tests/
cp tests/test_config.py quant-trading/tests/
cp tests/test_data.py quant-trading/tests/
cp tests/test_engine.py quant-trading/tests/
cp tests/test_models.py quant-trading/tests/
cp tests/test_risk.py quant-trading/tests/
cp tests/test_strategy.py quant-trading/tests/
mkdir -p quant-trading/tests/test_strategies
cp tests/test_strategies/__init__.py quant-trading/tests/test_strategies/
cp tests/test_strategies/test_momentum_breakout.py quant-trading/tests/test_strategies/
```

**Step 2: Update imports in all test files**

Find and replace in all test files:
- `from quant.` → `from quant_trading.`
- `import quant.` → `import quant_trading.`

**Step 3: Verify no old imports remain**

Run: `grep -r "from quant\." quant-trading/tests/ || echo "No old imports found"`
Expected: "No old imports found"

**Step 4: Commit**

```bash
git add quant-trading/tests/
git commit -m "feat: move tests to quant-trading with updated imports"
```

---

## Task 5: Create quant-trading pyproject.toml

**Files:**
- Create: `quant-trading/pyproject.toml`

**Step 1: Write pyproject.toml**

```toml
[project]
name = "quant-trading"
version = "0.1.0"
description = "Quantitative trading API with tournament-validated strategies"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.109.0",
    "uvicorn>=0.27.0",
    "alpaca-py>=0.21.0",
    "pandas>=2.2.0",
    "numpy>=1.26.0",
    "httpx>=0.26.0",
    "python-dotenv>=1.0.0",
    "sqlalchemy>=2.0.0",
    "psycopg2-binary>=2.9.0",
    "redis>=5.0.0",
    "pydantic>=2.6.0",
    "pydantic-settings>=2.1.0",
    "pytz>=2025.2",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=4.1.0",
    "ruff>=0.2.0",
    "mypy>=1.8.0",
    "pandas-stubs>=2.1.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["quant_trading"]

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
addopts = "-v --tb=short"

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP"]

[tool.mypy]
python_version = "3.12"
strict = true
plugins = ["pydantic.mypy"]
```

**Step 2: Commit**

```bash
git add quant-trading/pyproject.toml
git commit -m "feat: add quant-trading pyproject.toml"
```

---

## Task 6: Create quant-trading Dockerfile

**Files:**
- Create: `quant-trading/Dockerfile`

**Step 1: Write Dockerfile**

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy dependency files
COPY pyproject.toml .

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy source code
COPY quant_trading/ quant_trading/

# Expose API port
EXPOSE 8000

# Run API server
CMD ["uv", "run", "uvicorn", "quant_trading.api:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Step 2: Commit**

```bash
git add quant-trading/Dockerfile
git commit -m "feat: add quant-trading Dockerfile"
```

---

## Task 7: Test quant-trading Standalone

**Step 1: Sync dependencies**

```bash
cd quant-trading && uv sync
```

**Step 2: Run tests**

Run: `cd quant-trading && uv run pytest`
Expected: All tests pass

**Step 3: Fix any import errors**

If tests fail due to imports, fix the remaining `quant.` → `quant_trading.` references.

**Step 4: Commit fixes if any**

```bash
git add -A && git commit -m "fix: resolve remaining import issues"
```

---

## Task 8: Create OpenClaw Config Examples

**Files:**
- Create: `openclaw/config/openclaw.json.example`
- Create: `openclaw/config/auth-profiles.json.example`

**Step 1: Write openclaw.json.example**

```json
{
  "agents": {
    "defaults": {
      "model": {
        "primary": "anthropic/claude-sonnet-4-20250514",
        "fallbacks": ["anthropic/claude-sonnet-4-20250514", "anthropic/claude-opus-4-5"]
      },
      "workspace": "/home/node/workspace",
      "compaction": {
        "mode": "safeguard",
        "reserveTokensFloor": 20000,
        "memoryFlush": {
          "enabled": true,
          "softThresholdTokens": 30000
        }
      },
      "maxConcurrent": 4,
      "subagents": {
        "maxConcurrent": 8
      },
      "contextTokens": 100000
    }
  },
  "messages": {
    "ackReactionScope": "group-mentions"
  },
  "commands": {
    "native": "auto",
    "nativeSkills": "auto"
  },
  "channels": {
    "telegram": {
      "enabled": true,
      "dmPolicy": "open",
      "botToken": "YOUR_TELEGRAM_BOT_TOKEN",
      "allowFrom": ["*"],
      "groupPolicy": "allowlist",
      "streamMode": "partial"
    }
  },
  "gateway": {
    "port": 18789,
    "mode": "local",
    "bind": "loopback",
    "auth": {
      "allowTailscale": true
    },
    "trustedProxies": ["0.0.0.0/0", "::/0", "127.0.0.1", "::1"],
    "tailscale": {
      "mode": "serve",
      "resetOnExit": false
    }
  },
  "plugins": {
    "entries": {
      "telegram": {
        "enabled": true
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

**Step 2: Write auth-profiles.json.example**

```json
{
  "profiles": {}
}
```

**Step 3: Commit**

```bash
git add openclaw/config/
git commit -m "feat: add openclaw config examples"
```

---

## Task 9: Create OpenClaw Deployment Scripts

**Files:**
- Create: `openclaw/scripts/deploy.sh`
- Create: `openclaw/scripts/logs.sh`
- Create: `openclaw/scripts/sync-skills.sh`

**Step 1: Write deploy.sh**

```bash
#!/bin/bash
# Deploy agents to server
# Usage: ./deploy.sh [hostname]
set -e

HOST="${1:-buckbot}"
REPO_DIR="$HOME/agents"
SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "Deploying to $HOST..."

# Push to GitHub first
echo "Pushing to GitHub..."
cd "$ROOT_DIR"
git push

# Pull on server and restart
echo "Pulling and restarting on server..."
ssh "$HOST" "cd $REPO_DIR && git pull && docker compose up -d --build"

echo "Waiting for startup..."
sleep 8

# Show logs
ssh "$HOST" "cd $REPO_DIR && docker compose logs --tail=20"

echo "Done!"
```

**Step 2: Write logs.sh**

```bash
#!/bin/bash
# Tail logs from server
# Usage: ./logs.sh [hostname] [service]
set -e

HOST="${1:-buckbot}"
SERVICE="${2:-}"
REPO_DIR="$HOME/agents"

if [ -n "$SERVICE" ]; then
    ssh "$HOST" "cd $REPO_DIR && docker compose logs -f $SERVICE"
else
    ssh "$HOST" "cd $REPO_DIR && docker compose logs -f"
fi
```

**Step 3: Write sync-skills.sh**

```bash
#!/bin/bash
# Quick skill sync without full restart
# Usage: ./sync-skills.sh [hostname]
set -e

HOST="${1:-buckbot}"
REPO_DIR="$HOME/agents"
SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "Syncing skills to $HOST..."
rsync -avz "$SCRIPT_DIR/skills/" "$HOST:$REPO_DIR/openclaw/skills/"

echo "Skills synced. Restart openclaw to pick up changes:"
echo "  ssh $HOST 'cd $REPO_DIR && docker compose restart openclaw'"
```

**Step 4: Make scripts executable**

```bash
chmod +x openclaw/scripts/deploy.sh
chmod +x openclaw/scripts/logs.sh
chmod +x openclaw/scripts/sync-skills.sh
```

**Step 5: Commit**

```bash
git add openclaw/scripts/
git commit -m "feat: add openclaw deployment scripts"
```

---

## Task 10: Create Quant-Trading Skill for OpenClaw

**Files:**
- Create: `openclaw/skills/quant-trading/SKILL.md`

**Step 1: Write SKILL.md**

```markdown
---
name: quant-trading
description: Trading recommendations and portfolio management for F100 stocks
---

# Quant Trading

You help manage a quantitative trading system for Fortune 100 stocks.

## API Base URL

http://quant-trading:8000

## Endpoints

### GET /api/analyze

Returns today's trading recommendations with confidence scores and rationale.

Response:
```json
{
  "recommendations": [
    {
      "ticker": "AAPL",
      "action": "BUY",
      "size": 800,
      "confidence": 75,
      "rationale": "Momentum breakout detected with strong volume"
    }
  ]
}
```

### POST /api/execute

Execute approved trades. **Always get user confirmation before calling this.**

Request:
```json
{
  "trades": [
    {"ticker": "AAPL", "action": "buy", "size": 800}
  ]
}
```

### GET /api/positions

Returns current open positions with P&L.

### GET /api/portfolio

Returns portfolio summary including cash balance and total value.

## Usage Guidelines

1. **Morning routine**: Call `/api/analyze` to get daily recommendations
2. **Always review** recommendations with the user before executing
3. **Never auto-execute** trades without explicit user approval
4. **Check positions** after trades to confirm execution
```

**Step 2: Commit**

```bash
git add openclaw/skills/
git commit -m "feat: add quant-trading skill for openclaw"
```

---

## Task 11: Create Root docker-compose.yml

**Files:**
- Create: `docker-compose.yml` (root)

**Step 1: Write docker-compose.yml**

```yaml
services:
  openclaw:
    build: ./openclaw
    image: openclaw-custom:latest
    ports:
      - "18789:18789"
    environment:
      HOME: /home/node
      TERM: xterm-256color
      OPENCLAW_GATEWAY_TOKEN: ${OPENCLAW_GATEWAY_TOKEN}
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
      GH_TOKEN: ${GH_TOKEN}
      GITHUB_TOKEN: ${GH_TOKEN}
    volumes:
      - openclaw-state:/home/node/.openclaw
      - ./openclaw/skills:/home/node/skills:ro
      - ${OPENCLAW_WORKSPACE_DIR:-./workspace}:/home/node/workspace
    init: true
    restart: unless-stopped
    depends_on:
      - quant-trading
    command:
      [
        "node",
        "dist/index.js",
        "gateway",
        "--bind",
        "loopback",
        "--port",
        "18789"
      ]

  quant-trading:
    build: ./quant-trading
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://postgres:postgres@postgres:5432/quant
      ALPACA_API_KEY: ${ALPACA_API_KEY}
      ALPACA_SECRET_KEY: ${ALPACA_SECRET_KEY}
      ALPACA_BASE_URL: ${ALPACA_BASE_URL:-https://paper-api.alpaca.markets}
    depends_on:
      postgres:
        condition: service_healthy
    restart: unless-stopped

  postgres:
    image: postgres:16-alpine
    volumes:
      - postgres-data:/var/lib/postgresql/data
    environment:
      POSTGRES_DB: quant
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5
    restart: unless-stopped

volumes:
  openclaw-state:
  postgres-data:
```

**Step 2: Commit**

```bash
git add docker-compose.yml
git commit -m "feat: add root docker-compose with all services"
```

---

## Task 12: Create Root .env.example

**Files:**
- Create: `.env.example` (update existing)

**Step 1: Write .env.example**

```bash
# OpenClaw
OPENCLAW_GATEWAY_TOKEN=  # Generate with: openssl rand -hex 24
OPENCLAW_WORKSPACE_DIR=./workspace
ANTHROPIC_API_KEY=
GH_TOKEN=

# Quant Trading
ALPACA_API_KEY=
ALPACA_SECRET_KEY=
ALPACA_BASE_URL=https://paper-api.alpaca.markets

# Optional: Override postgres password
# POSTGRES_PASSWORD=postgres
```

**Step 2: Commit**

```bash
git add .env.example
git commit -m "feat: update .env.example for combined services"
```

---

## Task 13: Create CLAUDE.md

**Files:**
- Create: `CLAUDE.md`

**Step 1: Write CLAUDE.md**

```markdown
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
```

**Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: add CLAUDE.md with repo context and operations guide"
```

---

## Task 14: Create Root README.md

**Files:**
- Create: `README.md`

**Step 1: Write README.md**

```markdown
# Agents

Multi-agent monorepo for AI-powered automation.

## Agents

| Agent | Description | Port |
|-------|-------------|------|
| [openclaw](./openclaw) | Telegram bot orchestrator | 18789 |
| [quant-trading](./quant-trading) | F100 stock trading API | 8000 |

## Quick Start

```bash
# Copy environment template
cp .env.example .env
# Edit .env with your API keys

# Run all services
docker compose up -d

# View logs
docker compose logs -f
```

## Development

```bash
# Quant-trading standalone
cd quant-trading
uv sync
uv run pytest
uv run uvicorn quant_trading.api:app --reload
```

## Deployment

```bash
cd openclaw
./scripts/deploy.sh  # Push to GitHub and restart on server
./scripts/logs.sh    # Tail server logs
```

## Documentation

- [CLAUDE.md](./CLAUDE.md) — AI context and operations guide
- [OpenClaw README](./openclaw/README.md) — Bot setup and configuration
- [Design Docs](./docs/plans/) — Architecture and planning documents
```

**Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add root README"
```

---

## Task 15: Create quant-trading README.md

**Files:**
- Create: `quant-trading/README.md`

**Step 1: Write README.md**

```markdown
# Quant Trading

Quantitative trading API with tournament-validated strategies for F100 stocks.

## Quick Start

```bash
# Install dependencies
uv sync

# Run tests
uv run pytest

# Run API server
uv run uvicorn quant_trading.api:app --reload
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/analyze` | GET | Get trading recommendations |
| `/api/execute` | POST | Execute trades |
| `/api/positions` | GET | Current positions |
| `/api/portfolio` | GET | Portfolio summary |

## Configuration

Set environment variables or create `.env`:

```bash
ALPACA_API_KEY=your_key
ALPACA_SECRET_KEY=your_secret
ALPACA_BASE_URL=https://paper-api.alpaca.markets
DATABASE_URL=postgresql://localhost/quant
```

## Docker

```bash
# Build image
docker build -t quant-trading .

# Run container
docker run -p 8000:8000 --env-file .env quant-trading
```
```

**Step 2: Commit**

```bash
git add quant-trading/README.md
git commit -m "docs: add quant-trading README"
```

---

## Task 16: Clean Up Old Files

**Files:**
- Delete: `src/` directory
- Delete: `api/` directory
- Delete: `openclaw/docker-compose.yml`
- Delete: `openclaw/deploy.sh` (replaced by scripts/deploy.sh)
- Delete: `openclaw/drift.sh` (replaced by scripts/drift.sh or remove)
- Delete: `openclaw/openclaw.json` (use config/openclaw.json.example)
- Keep: `openclaw/Dockerfile`, `openclaw/.env.example`, `openclaw/README.md`

**Step 1: Remove old directories**

```bash
rm -rf src/
rm -rf api/
rm -rf tests/
```

**Step 2: Clean up openclaw directory**

```bash
rm openclaw/docker-compose.yml
rm openclaw/deploy.sh
rm openclaw/drift.sh
rm openclaw/openclaw.json
```

**Step 3: Remove old root pyproject.toml**

```bash
rm pyproject.toml
```

**Step 4: Commit**

```bash
git add -A
git commit -m "chore: remove old directory structure"
```

---

## Task 17: Update .gitignore

**Files:**
- Modify: `.gitignore`

**Step 1: Update .gitignore**

Add these lines:

```gitignore
# Agents-specific
openclaw/config/openclaw.json
openclaw/config/auth-profiles.json
workspace/

# uv
.uv/
uv.lock
```

**Step 2: Commit**

```bash
git add .gitignore
git commit -m "chore: update gitignore for agents structure"
```

---

## Task 18: Final Verification

**Step 1: Run quant-trading tests**

```bash
cd quant-trading && uv sync && uv run pytest
```

Expected: All tests pass

**Step 2: Build Docker images**

```bash
docker compose build
```

Expected: Both images build successfully

**Step 3: Start services**

```bash
docker compose up -d
docker compose ps
```

Expected: All 3 services running (openclaw, quant-trading, postgres)

**Step 4: Test quant-trading API**

```bash
curl http://localhost:8000/health || curl http://localhost:8000/
```

Expected: Response from API

**Step 5: Stop services**

```bash
docker compose down
```

---

## Task 19: Update Git Remote and Push

**Step 1: Update remote origin**

```bash
git remote set-url origin git@github.com:bbuckland/agents.git
```

**Step 2: Verify remote**

```bash
git remote -v
```

Expected: origin points to bbuckland/agents

**Step 3: Push to new repo**

```bash
git push -u origin main
```

**Step 4: Final commit summary**

```bash
git log --oneline -10
```

---

## Summary

After completing all tasks:

- `openclaw/` contains bot config, scripts, skills
- `quant-trading/` contains Python trading API
- Root `docker-compose.yml` runs all services
- `CLAUDE.md` documents operations
- Old `src/`, `api/`, `tests/` directories removed
- Git remote points to bbuckland/agents
