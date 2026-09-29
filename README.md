# Agents

Multi-agent monorepo for AI-powered automation.

## Agents

| Agent | Description | Port |
|-------|-------------|------|
| [openclaw](./openclaw) | Telegram bot orchestrator | 18789 |

Trading moved to `bbuckland/monorepo` (`apps/quant-engine`, next to the YNAB MCP).

## Deployment

```bash
cd infra
./scripts/deploy.sh       # Pulumi deploy to the Hetzner server
./scripts/sync-skills.sh  # Push openclaw/skills to the server
./scripts/logs.sh         # Tail server logs
```

## Documentation

- [CLAUDE.md](./CLAUDE.md) — AI context and operations guide
- [Design Docs](./docs/plans/) — Architecture and planning documents
