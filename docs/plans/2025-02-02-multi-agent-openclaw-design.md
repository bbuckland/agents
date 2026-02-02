# Multi-Agent OpenClaw Design

## Overview

Single OpenClaw gateway powering multiple Telegram bots, each bound to an isolated agent with its own workspace, sessions, and persona.

## Agents

| Agent | Telegram Bot | Purpose |
|-------|--------------|---------|
| BuckBot | @BuckBot | General-purpose assistant + agent monitor |
| ExpenseBot | @ExpenseBot | Oracle Expenses automation via Playwright |
| QuantBot | @QuantBot | Trading assistant with quant-trading API |

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                 OpenClaw Gateway                     │
│                   (one process)                      │
├─────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │  BuckBot    │  │ ExpenseBot  │  │  QuantBot   │  │
│  │  (agent)    │  │  (agent)    │  │  (agent)    │  │
│  ├─────────────┤  ├─────────────┤  ├─────────────┤  │
│  │ workspace/  │  │ workspace/  │  │ workspace/  │  │
│  │ buckbot/    │  │ expense/    │  │ quant/      │  │
│  │             │  │             │  │             │  │
│  │ sessions    │  │ sessions    │  │ sessions    │  │
│  │ persona     │  │ persona     │  │ persona     │  │
│  │ skills: *   │  │ skills:     │  │ skills:     │  │
│  │             │  │  - expense  │  │  - quant    │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  │
├─────────────────────────────────────────────────────┤
│  Telegram Bindings:                                  │
│    @BuckBot    → buckbot agent                      │
│    @ExpenseBot → expense agent                      │
│    @QuantBot   → quant agent                        │
└─────────────────────────────────────────────────────┘
```

## Configuration

### openclaw.json

```json5
{
  agents: {
    defaults: {
      model: { primary: "anthropic/claude-sonnet-4-20250514" },
      contextTokens: 100000,
      compaction: {
        mode: "safeguard",
        reserveTokensFloor: 20000,
        memoryFlush: {
          enabled: true,
          softThresholdTokens: 30000
        }
      }
    },
    list: [
      {
        id: "buckbot",
        default: true,
        name: "BuckBot",
        workspace: "/home/node/workspaces/buckbot",
        agentDir: "/home/node/.openclaw/agents/buckbot"
      },
      {
        id: "expense",
        name: "ExpenseBot",
        workspace: "/home/node/workspaces/expense",
        agentDir: "/home/node/.openclaw/agents/expense"
      },
      {
        id: "quant",
        name: "QuantBot",
        workspace: "/home/node/workspaces/quant",
        agentDir: "/home/node/.openclaw/agents/quant"
      }
    ]
  },
  channels: {
    telegram: {
      enabled: true,
      accounts: {
        buckbot: {
          botToken: "${TELEGRAM_BUCKBOT_TOKEN}",
          dmPolicy: "open"
        },
        expense: {
          botToken: "${TELEGRAM_EXPENSE_TOKEN}",
          dmPolicy: "open"
        },
        quant: {
          botToken: "${TELEGRAM_QUANT_TOKEN}",
          dmPolicy: "open"
        }
      }
    }
  },
  bindings: [
    { agentId: "buckbot", match: { channel: "telegram", accountId: "buckbot" } },
    { agentId: "expense", match: { channel: "telegram", accountId: "expense" } },
    { agentId: "quant", match: { channel: "telegram", accountId: "quant" } }
  ]
}
```

## ExpenseBot Design

### Playwright Connect Architecture

```
┌─────────────────────────┐         ┌─────────────────────────┐
│      Your Mac           │         │        Server           │
│                         │  Tailscale                        │
│  ┌───────────────────┐  │◄────────│  ┌───────────────────┐  │
│  │ playwright        │  │   ws:// │  │    ExpenseBot     │  │
│  │ run-server        │  │         │  │    (agent)        │  │
│  │ :3000             │  │         │  │                   │  │
│  └───────────────────┘  │         │  │ connects to:      │  │
│          │              │         │  │ ws://mac:3000     │  │
│          ▼              │         │  └───────────────────┘  │
│  ┌───────────────────┐  │         │                         │
│  │ Chrome browser    │  │         │                         │
│  │ (with Passkey)    │  │         │                         │
│  └───────────────────┘  │         │                         │
└─────────────────────────┘         └─────────────────────────┘
```

Local setup:
```bash
npx playwright run-server --port 3000 --host 0.0.0.0
```

### Report Lifecycle

**Workspace structure:**
```
workspaces/expense/
├── SOUL.md
├── reference/
│   └── poet-codes.csv        # Parsed from budget PDF
└── reports/
    └── 2025-01-nyc-trip/     # One folder per report
        ├── expenses.csv      # Line items with POET codes
        ├── receipts/         # Images/PDFs for items ≥$75
        │   ├── 001-delta.pdf
        │   └── 002-marriott.png
        └── report.json       # Report metadata
```

**expenses.csv format:**
```csv
id,date,vendor,amount,poet,description,receipt_file,needs_receipt
001,2025-01-15,Delta Airlines,487.20,PROJ-123.FIN.TRAVEL.T1,Flight to NYC,001-delta.pdf,true
002,2025-01-15,Uber,24.50,PROJ-123.FIN.TRAVEL.T1,Airport to hotel,,false
003,2025-01-16,PF Changs,26.94,PROJ-123.FIN.MEALS.T1,Client lunch,,false
```

**POET codes:**
- Project.Org.ExpenditureType.Task format
- Reference file parsed from budget PDF
- Bot suggests matching POET based on vendor/category
- One-offs can be specified inline

**Receipt threshold:** $75 (items under don't require receipt tracking)

### Interaction Examples

| You say | Bot does |
|---------|----------|
| "Start new report for NYC trip" | Creates report folder and CSV |
| "Lunch at PF Changs $26.94" | Adds row, infers MEALS type, no receipt needed |
| [sends receipt image] "Hotel $312" | OCR extracts details, saves image, adds row |
| "Use POET PROJ-456.OPS.MISC.T2" | Updates last entry or sets default |
| "Show me the report" | Displays CSV summary with totals |
| "Submit it" | Connects to Playwright, fills Oracle forms |

### Authentication

- Oracle uses Okta SSO with Passkey
- Passkey requires local browser (device-bound credential)
- Bot prompts "Please approve Okta on your device" when auth needed
- Session persists between submissions

## QuantBot Design

### Workspace Structure

```
workspaces/quant/
├── SOUL.md              # Persona: terse, trading-focused
└── notes/               # Persistent analysis notes
```

### Persona (SOUL.md)

```markdown
# QuantBot

You are a trading assistant focused on the quant-trading API.

## Style
- Be concise and numbers-focused
- Lead with the key metrics
- Ask for confirmation before any trade execution

## Daily routine
When greeted in the morning, proactively:
1. Fetch /api/portfolio for current positions
2. Fetch /api/analyze for today's recommendations
3. Present a brief summary
```

### Skills

Uses existing `skills/quant-trading/SKILL.md` unchanged.

### Future Enhancements (not in initial scope)

- Scheduled morning analysis notifications
- Alert thresholds (position up/down X%)
- Performance dashboards

## BuckBot Design

### Workspace Structure

```
workspaces/buckbot/
├── SOUL.md              # General assistant persona
└── notes/               # Reminders, notes, etc.
```

### Agent Monitoring

BuckBot can check on other agents via `agent-status` skill:

**Capabilities:**
- View recent activity summaries
- Check ExpenseBot's current report status
- See QuantBot's last recommendations

**Limitations:**
- Cannot execute trades for QuantBot
- Cannot submit expenses for ExpenseBot
- Read-only visibility into other agents

## Infrastructure Changes

### docker-compose.yml

```yaml
services:
  openclaw:
    environment:
      TELEGRAM_BUCKBOT_TOKEN: ${TELEGRAM_BUCKBOT_TOKEN}
      TELEGRAM_EXPENSE_TOKEN: ${TELEGRAM_EXPENSE_TOKEN}
      TELEGRAM_QUANT_TOKEN: ${TELEGRAM_QUANT_TOKEN}
      # ... existing vars ...
    volumes:
      - ./openclaw/workspaces:/home/node/workspaces
      - ./openclaw/skills:/home/node/skills:ro
      # ... existing volumes ...
```

### .env additions

```bash
TELEGRAM_BUCKBOT_TOKEN=your_buckbot_token
TELEGRAM_EXPENSE_TOKEN=your_expense_token
TELEGRAM_QUANT_TOKEN=your_quant_token
```

### Directory Structure

```
openclaw/
├── workspaces/
│   ├── buckbot/
│   │   └── SOUL.md
│   ├── expense/
│   │   ├── SOUL.md
│   │   ├── reference/
│   │   │   └── poet-codes.csv
│   │   └── reports/
│   └── quant/
│       └── SOUL.md
├── skills/
│   ├── quant-trading/
│   │   └── SKILL.md          # Existing
│   ├── expense/
│   │   ├── SKILL.md
│   │   └── oracle-expenses.md
│   └── agent-status/
│       └── SKILL.md
└── config/
    └── openclaw.json
```

### Telegram Setup

1. Create 3 bots via @BotFather
2. Get tokens for each
3. Add to `.env`

## Not in Initial Scope

- Scheduled QuantBot notifications
- Additional bots beyond these three
- Agent-to-agent task delegation (BuckBot monitors only)
