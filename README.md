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
