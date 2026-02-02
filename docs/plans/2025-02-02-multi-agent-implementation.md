# Multi-Agent OpenClaw Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Configure OpenClaw gateway to run three isolated Telegram bots (BuckBot, ExpenseBot, QuantBot) with dedicated workspaces and skills.

**Architecture:** Single OpenClaw gateway with `agents.list` configuration, Telegram multi-account setup with bindings routing each bot to its agent. ExpenseBot has Playwright Connect integration for browser automation.

**Tech Stack:** OpenClaw, Telegram Bot API, Playwright (for ExpenseBot)

---

## Pre-Implementation Setup

Before starting, you need 3 Telegram bot tokens from @BotFather:
1. Create @BuckBot (or your preferred name)
2. Create @ExpenseBot
3. Create @QuantBot

Add tokens to `.env` on server after Task 2.

---

### Task 1: Create Directory Structure

**Files:**
- Create: `openclaw/workspaces/buckbot/SOUL.md`
- Create: `openclaw/workspaces/expense/SOUL.md`
- Create: `openclaw/workspaces/expense/reference/.gitkeep`
- Create: `openclaw/workspaces/quant/SOUL.md`

**Step 1: Create workspace directories**

```bash
mkdir -p openclaw/workspaces/buckbot
mkdir -p openclaw/workspaces/expense/reference
mkdir -p openclaw/workspaces/expense/reports
mkdir -p openclaw/workspaces/quant/notes
```

**Step 2: Create BuckBot persona**

Create `openclaw/workspaces/buckbot/SOUL.md`:

```markdown
# BuckBot

You are Bradley's general-purpose personal assistant and the overseer of other agents in this system.

## Personality
- Helpful and proactive
- Concise but thorough
- You have access to all skills

## Capabilities
- General assistance with any task
- Monitor status of other agents (ExpenseBot, QuantBot)
- Access to quant-trading and other skills as needed

## Other Agents
- **ExpenseBot**: Handles Oracle Expenses automation
- **QuantBot**: Handles trading and portfolio management
```

**Step 3: Create ExpenseBot persona**

Create `openclaw/workspaces/expense/SOUL.md`:

```markdown
# ExpenseBot

You help Bradley manage work expense reports for Oracle Expenses.

## Personality
- Efficient and detail-oriented
- Always confirm POET codes before adding expenses
- Summarize totals after each addition

## Workflow
1. User starts a new expense report
2. User sends expenses (text or receipt images)
3. You extract details and track in CSV
4. When ready, you submit via Playwright to Oracle

## POET Codes
POET = Project.Org.ExpenditureType.Task
- Reference: `reference/poet-codes.csv`
- Ask user to confirm POET for each expense
- Can set a default POET for the current report

## Receipt Threshold
- $75 and above: Receipt required
- Under $75: No receipt needed, just log the expense

## Report Storage
Each report is stored in `reports/<report-name>/`:
- `expenses.csv` - Line items
- `receipts/` - Images and PDFs
- `report.json` - Metadata
```

**Step 4: Create QuantBot persona**

Create `openclaw/workspaces/quant/SOUL.md`:

```markdown
# QuantBot

You are a trading assistant focused on the quant-trading API.

## Personality
- Concise and numbers-focused
- Lead with key metrics
- Never execute trades without explicit user confirmation

## Daily Routine
When greeted in the morning, proactively:
1. Fetch /api/portfolio for current positions
2. Fetch /api/analyze for today's recommendations
3. Present a brief summary with key numbers

## Communication Style
- Use tables for positions and recommendations
- Bold the most important numbers
- Keep explanations brief
```

**Step 5: Create placeholder files**

```bash
touch openclaw/workspaces/expense/reference/.gitkeep
touch openclaw/workspaces/expense/reports/.gitkeep
touch openclaw/workspaces/quant/notes/.gitkeep
```

**Step 6: Commit**

```bash
git add openclaw/workspaces/
git commit -m "feat: add multi-agent workspace structure with personas"
```

---

### Task 2: Update docker-compose.yml

**Files:**
- Modify: `docker-compose.yml`

**Step 1: Update environment variables**

In `docker-compose.yml`, update the `openclaw` service environment section:

```yaml
    environment:
      HOME: /home/node
      TERM: xterm-256color
      OPENCLAW_GATEWAY_TOKEN: ${OPENCLAW_GATEWAY_TOKEN}
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
      GH_TOKEN: ${GH_TOKEN}
      GITHUB_TOKEN: ${GH_TOKEN}
      TELEGRAM_BUCKBOT_TOKEN: ${TELEGRAM_BUCKBOT_TOKEN}
      TELEGRAM_EXPENSE_TOKEN: ${TELEGRAM_EXPENSE_TOKEN}
      TELEGRAM_QUANT_TOKEN: ${TELEGRAM_QUANT_TOKEN}
```

**Step 2: Update volumes**

In `docker-compose.yml`, update the `openclaw` service volumes section:

```yaml
    volumes:
      - openclaw-state:/home/node/.openclaw
      - ./openclaw/skills:/home/node/skills:ro
      - ./openclaw/workspaces:/home/node/workspaces
      - ${OPENCLAW_WORKSPACE_DIR:-./workspace}:/home/node/workspace
```

**Step 3: Commit**

```bash
git add docker-compose.yml
git commit -m "feat: add multi-agent environment variables and workspace volume"
```

---

### Task 3: Update .env.example

**Files:**
- Modify: `.env.example`

**Step 1: Add new token variables**

Append to `.env.example`:

```bash
# Multi-agent Telegram tokens
TELEGRAM_BUCKBOT_TOKEN=your_buckbot_token_from_botfather
TELEGRAM_EXPENSE_TOKEN=your_expense_token_from_botfather
TELEGRAM_QUANT_TOKEN=your_quant_token_from_botfather
```

**Step 2: Commit**

```bash
git add .env.example
git commit -m "docs: add multi-agent telegram tokens to .env.example"
```

---

### Task 4: Create Multi-Agent OpenClaw Config

**Files:**
- Create: `openclaw/config/openclaw.multi-agent.json.example`

**Step 1: Create the config file**

Create `openclaw/config/openclaw.multi-agent.json.example`:

```json
{
  "agents": {
    "defaults": {
      "model": {
        "primary": "anthropic/claude-sonnet-4-20250514",
        "fallbacks": ["anthropic/claude-sonnet-4-20250514", "anthropic/claude-opus-4-5"]
      },
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
    },
    "list": [
      {
        "id": "buckbot",
        "default": true,
        "name": "BuckBot",
        "workspace": "/home/node/workspaces/buckbot",
        "agentDir": "/home/node/.openclaw/agents/buckbot"
      },
      {
        "id": "expense",
        "name": "ExpenseBot",
        "workspace": "/home/node/workspaces/expense",
        "agentDir": "/home/node/.openclaw/agents/expense"
      },
      {
        "id": "quant",
        "name": "QuantBot",
        "workspace": "/home/node/workspaces/quant",
        "agentDir": "/home/node/.openclaw/agents/quant"
      }
    ]
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
      "accounts": {
        "buckbot": {
          "botToken": "${TELEGRAM_BUCKBOT_TOKEN}",
          "dmPolicy": "open"
        },
        "expense": {
          "botToken": "${TELEGRAM_EXPENSE_TOKEN}",
          "dmPolicy": "open"
        },
        "quant": {
          "botToken": "${TELEGRAM_QUANT_TOKEN}",
          "dmPolicy": "open"
        }
      }
    }
  },
  "bindings": [
    { "agentId": "buckbot", "match": { "channel": "telegram", "accountId": "buckbot" } },
    { "agentId": "expense", "match": { "channel": "telegram", "accountId": "expense" } },
    { "agentId": "quant", "match": { "channel": "telegram", "accountId": "quant" } }
  ],
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

**Step 2: Commit**

```bash
git add openclaw/config/openclaw.multi-agent.json.example
git commit -m "feat: add multi-agent openclaw config example"
```

---

### Task 5: Create ExpenseBot Skill

**Files:**
- Create: `openclaw/skills/expense/SKILL.md`

**Step 1: Create the skill file**

Create `openclaw/skills/expense/SKILL.md`:

```markdown
---
name: expense
description: Oracle Expenses report management and submission
---

# Expense Report Management

You manage expense reports for Oracle Expenses.

## Report Lifecycle

### Starting a Report

When user says "start new report for <name>":
1. Create directory: `reports/<date>-<slugified-name>/`
2. Create `expenses.csv` with headers: `id,date,vendor,amount,poet,description,receipt_file,needs_receipt`
3. Create `report.json` with metadata
4. Create `receipts/` subdirectory
5. Confirm: "Started report '<name>'. Ready to add expenses."

### Adding Expenses

**From text** (e.g., "Lunch at PF Changs $26.94"):
1. Parse vendor and amount
2. Determine if receipt needed (≥$75)
3. Ask for POET code (or use report default)
4. Add row to CSV
5. Confirm with running total

**From image/receipt**:
1. Extract vendor, amount, date via vision
2. Save image to `receipts/<id>-<vendor-slug>.<ext>`
3. Ask for POET code
4. Add row to CSV with receipt_file reference
5. Confirm with running total

### POET Codes

Format: `PROJECT.ORG.EXPENDITURE_TYPE.TASK`

Reference file: `reference/poet-codes.csv`

If user provides partial POET, try to match from reference file.

User can set default POET for a report: "Use POET XYZ for this report"

### Viewing Report

When user asks to see the report:
1. Read current `expenses.csv`
2. Display as formatted table
3. Show totals by POET code
4. Show overall total

### Submitting Report

When user says "submit it":
1. Confirm report summary
2. Connect to Playwright server at `ws://<tailscale-hostname>:3000`
3. Navigate to Oracle Expenses
4. If Okta auth needed, prompt: "Please approve Okta on your device"
5. Fill form with each expense
6. Confirm submission

## Playwright Connection

The browser runs on user's local machine via Playwright Connect.

**Connection URL:** `ws://<configured-tailscale-host>:3000`

**User must run locally:**
```bash
npx playwright run-server --port 3000 --host 0.0.0.0
```

## CSV Format

```csv
id,date,vendor,amount,poet,description,receipt_file,needs_receipt
001,2025-01-15,Delta Airlines,487.20,PROJ-123.FIN.TRAVEL.T1,Flight to NYC,001-delta.pdf,true
002,2025-01-15,Uber,24.50,PROJ-123.FIN.TRAVEL.T1,Airport to hotel,,false
```
```

**Step 2: Commit**

```bash
git add openclaw/skills/expense/
git commit -m "feat: add expense skill for Oracle Expenses automation"
```

---

### Task 6: Create Agent Status Skill for BuckBot

**Files:**
- Create: `openclaw/skills/agent-status/SKILL.md`

**Step 1: Create the skill file**

Create `openclaw/skills/agent-status/SKILL.md`:

```markdown
---
name: agent-status
description: Monitor status of other agents in the gateway
---

# Agent Status Monitoring

As BuckBot, you can check on other agents in this gateway.

## Available Agents

| Agent | Purpose |
|-------|---------|
| expense | ExpenseBot - Oracle Expenses automation |
| quant | QuantBot - Trading and portfolio management |

## What You Can See

- Recent activity summaries
- Current report status (ExpenseBot)
- Last recommendations (QuantBot)

## What You Cannot Do

- Execute actions on behalf of other agents
- Modify other agents' sessions
- Submit expenses or execute trades for them

## Usage

When user asks about other agents:
- "What's ExpenseBot working on?" → Check expense agent's recent activity
- "Status of all agents" → Summary of each agent
- "What did QuantBot recommend today?" → Check quant agent's last analysis
```

**Step 2: Commit**

```bash
git add openclaw/skills/agent-status/
git commit -m "feat: add agent-status skill for BuckBot monitoring"
```

---

### Task 7: Update CLAUDE.md Documentation

**Files:**
- Modify: `CLAUDE.md`

**Step 1: Add multi-agent section**

Add after the "Adding a New Agent" section in `CLAUDE.md`:

```markdown
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
```

**Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: add multi-agent setup documentation"
```

---

### Task 8: Update README.md

**Files:**
- Modify: `openclaw/README.md`

**Step 1: Add multi-agent section**

Add a "Multi-Agent Setup" section after "Adding Skills":

```markdown
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
```

**Step 2: Commit**

```bash
git add openclaw/README.md
git commit -m "docs: add multi-agent setup to openclaw README"
```

---

## Post-Implementation

After all tasks complete:

1. **Create Telegram bots** via @BotFather (if not done)
2. **Add tokens** to server `.env`
3. **Copy config** on server: `cp config/openclaw.multi-agent.json.example config/openclaw.json`
4. **Deploy**: `./scripts/deploy.sh`
5. **Test** each bot responds correctly

### Future Tasks (not in this plan)

- Parse budget PDF into `poet-codes.csv`
- Implement Playwright Oracle form navigation
- Add scheduled QuantBot notifications
