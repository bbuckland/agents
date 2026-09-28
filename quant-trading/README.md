# Quant Trading

> **Moved.** This package now lives in `bbuckland/monorepo` at `apps/quant-engine`
> (package `quant_engine`), where the bugs are fixed and the ML4T core is added.
> See `docs/plans/agentic-trading-layer.md` in that repo. This copy is frozen and
> will be removed once the new engine is deployed.

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
