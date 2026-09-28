# Agents

Multi-agent monorepo for AI-powered automation.

## Agents

| Agent | Description | Port |
|-------|-------------|------|
| [openclaw](./openclaw) | Telegram bot orchestrator | 18789 |

Trading moved to `bbuckland/monorepo` (`apps/quant-engine`, next to the YNAB MCP).

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
