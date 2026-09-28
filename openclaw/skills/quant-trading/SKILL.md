---
name: quant-trading
description: Trading recommendations and portfolio management for F100 stocks
---

# Quant Trading

> **Deprecated.** The quant engine moved to `bbuckland/monorepo/apps/quant-engine`,
> and QuantBot is being replaced by a Hermes facilitator skill behind the
> `quant-mcp` Worker (see `docs/plans/agentic-trading-layer.md` in the monorepo).
> The endpoints below no longer match any running service.

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
