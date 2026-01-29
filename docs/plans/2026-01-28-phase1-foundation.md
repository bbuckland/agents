# Phase 1: Foundation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build the core infrastructure: project structure, data pipeline, strategy interface, and one working strategy that can paper trade on Alpaca.

**Architecture:** Python quant engine with modular strategy plugins. TypeScript API layer for Moltbot webhooks. PostgreSQL for persistence, Redis for real-time caching. Everything containerized for easy deployment.

**Tech Stack:** Python 3.12, FastAPI, pandas, numpy, alpaca-py, TypeScript, Hono (lightweight), PostgreSQL, Redis, Docker

---

## Prerequisites

Before starting:
1. Alpaca account with API keys (paper trading enabled)
2. Python 3.12+ installed
3. Node.js 20+ installed
4. Docker Desktop installed
5. PostgreSQL and Redis (will use Docker)

---

## Task 1: Project Structure

**Files:**
- Create: `pyproject.toml`
- Create: `src/quant/__init__.py`
- Create: `src/quant/py.typed`
- Create: `tests/__init__.py`
- Create: `api/package.json`
- Create: `.env.example`
- Create: `.gitignore`
- Create: `docker-compose.yml`

**Step 1: Create Python project configuration**

```toml
# pyproject.toml
[project]
name = "quant-superpowers"
version = "0.1.0"
description = "Quantitative trading system with tournament-validated strategies"
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
packages = ["src/quant"]

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

**Step 2: Create source directories and marker files**

```python
# src/quant/__init__.py
"""Quant Superpowers - Tournament-validated trading strategies."""

__version__ = "0.1.0"
```

```python
# src/quant/py.typed
# Marker file for PEP 561
```

```python
# tests/__init__.py
"""Test suite for Quant Superpowers."""
```

**Step 3: Create TypeScript API package.json**

```json
{
  "name": "quant-api",
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "tsx watch src/index.ts",
    "build": "tsc",
    "start": "node dist/index.js",
    "test": "vitest",
    "lint": "eslint src/"
  },
  "dependencies": {
    "hono": "^4.0.0",
    "@hono/node-server": "^1.8.0",
    "zod": "^3.22.0"
  },
  "devDependencies": {
    "@types/node": "^20.11.0",
    "tsx": "^4.7.0",
    "typescript": "^5.3.0",
    "vitest": "^1.2.0",
    "eslint": "^8.56.0",
    "@typescript-eslint/eslint-plugin": "^6.21.0",
    "@typescript-eslint/parser": "^6.21.0"
  }
}
```

**Step 4: Create environment template**

```bash
# .env.example

# Alpaca (Paper Trading)
ALPACA_API_KEY=your_paper_api_key
ALPACA_SECRET_KEY=your_paper_secret_key
ALPACA_BASE_URL=https://paper-api.alpaca.markets

# Database
DATABASE_URL=postgresql://quant:quant@localhost:5432/quant

# Redis
REDIS_URL=redis://localhost:6379

# API
API_PORT=3000
QUANT_ENGINE_URL=http://localhost:8000

# Risk Management
BASE_RESERVE=1000
MAX_POSITION_SIZE=1000
CONFIDENCE_THRESHOLD=70
```

**Step 5: Create .gitignore**

```gitignore
# .gitignore

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
.venv/
venv/

# TypeScript/Node
node_modules/
dist/
*.js.map

# Environment
.env
.env.local
.env.*.local

# IDE
.idea/
.vscode/
*.swp
*.swo
.DS_Store

# Testing
.coverage
htmlcov/
.pytest_cache/

# Data
*.parquet
*.csv
!datasets/*.csv

# Logs
*.log
logs/
```

**Step 6: Create Docker Compose for local dev**

```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: quant
      POSTGRES_PASSWORD: quant
      POSTGRES_DB: quant
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U quant"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
  redis_data:
```

**Step 7: Install dependencies and verify**

Run:
```bash
python -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"
```
Expected: Successfully installed packages

Run:
```bash
cd api && npm install && cd ..
```
Expected: Added packages

**Step 8: Start infrastructure and verify**

Run:
```bash
docker compose up -d
```
Expected: postgres and redis containers running

Run:
```bash
docker compose ps
```
Expected: Both services "healthy"

**Step 9: Commit**

```bash
git add -A
git commit -m "feat: initialize project structure with Python and TypeScript setup"
```

---

## Task 2: Configuration and Settings

**Files:**
- Create: `src/quant/config.py`
- Create: `tests/test_config.py`

**Step 1: Write the failing test**

```python
# tests/test_config.py
"""Tests for configuration loading."""

import os
from unittest.mock import patch


def test_settings_loads_from_env():
    """Settings should load values from environment variables."""
    env = {
        "ALPACA_API_KEY": "test_key",
        "ALPACA_SECRET_KEY": "test_secret",
        "ALPACA_BASE_URL": "https://paper-api.alpaca.markets",
        "DATABASE_URL": "postgresql://test:test@localhost:5432/test",
        "REDIS_URL": "redis://localhost:6379",
        "BASE_RESERVE": "1000",
        "MAX_POSITION_SIZE": "1000",
        "CONFIDENCE_THRESHOLD": "70",
    }
    with patch.dict(os.environ, env, clear=True):
        from quant.config import Settings
        settings = Settings()

        assert settings.alpaca_api_key == "test_key"
        assert settings.base_reserve == 1000
        assert settings.confidence_threshold == 70


def test_settings_validates_base_reserve_positive():
    """Base reserve must be positive."""
    env = {
        "ALPACA_API_KEY": "test_key",
        "ALPACA_SECRET_KEY": "test_secret",
        "ALPACA_BASE_URL": "https://paper-api.alpaca.markets",
        "DATABASE_URL": "postgresql://test:test@localhost:5432/test",
        "REDIS_URL": "redis://localhost:6379",
        "BASE_RESERVE": "-100",
        "MAX_POSITION_SIZE": "1000",
        "CONFIDENCE_THRESHOLD": "70",
    }
    with patch.dict(os.environ, env, clear=True):
        import importlib
        import quant.config
        importlib.reload(quant.config)
        from quant.config import Settings
        import pytest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            Settings()
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_config.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'quant.config'"

**Step 3: Write minimal implementation**

```python
# src/quant/config.py
"""Application configuration using pydantic-settings."""

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Alpaca
    alpaca_api_key: str = Field(..., description="Alpaca API key")
    alpaca_secret_key: str = Field(..., description="Alpaca secret key")
    alpaca_base_url: str = Field(
        default="https://paper-api.alpaca.markets",
        description="Alpaca API base URL",
    )

    # Database
    database_url: str = Field(..., description="PostgreSQL connection string")

    # Redis
    redis_url: str = Field(default="redis://localhost:6379", description="Redis URL")

    # Risk Management
    base_reserve: int = Field(default=1000, description="Untouchable reserve amount")
    max_position_size: int = Field(default=1000, description="Maximum position size")
    confidence_threshold: int = Field(
        default=70, description="Minimum confidence to trade"
    )

    @field_validator("base_reserve", "max_position_size")
    @classmethod
    def must_be_positive(cls, v: int) -> int:
        """Validate that monetary values are positive."""
        if v <= 0:
            raise ValueError("Must be positive")
        return v

    @field_validator("confidence_threshold")
    @classmethod
    def must_be_valid_percentage(cls, v: int) -> int:
        """Validate confidence is 0-100."""
        if not 0 <= v <= 100:
            raise ValueError("Must be between 0 and 100")
        return v

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_config.py -v`
Expected: PASSED

**Step 5: Commit**

```bash
git add src/quant/config.py tests/test_config.py
git commit -m "feat: add configuration management with pydantic-settings"
```

---

## Task 3: Domain Models

**Files:**
- Create: `src/quant/models.py`
- Create: `tests/test_models.py`

**Step 1: Write the failing test**

```python
# tests/test_models.py
"""Tests for domain models."""

from datetime import datetime, timezone
from decimal import Decimal


def test_signal_creation():
    """Signal should be created with required fields."""
    from quant.models import Signal, Action

    signal = Signal(
        ticker="AAPL",
        action=Action.BUY,
        size=Decimal("800.00"),
        confidence=78.5,
        rationale_tags=["momentum", "sentiment_positive"],
        stop_loss=Decimal("177.70"),
        take_profit=Decimal("192.36"),
        entry_price=Decimal("183.20"),
        explanation="Breakout above 20-day resistance with volume confirmation.",
        strategy_name="momentum_sentiment_v2",
    )

    assert signal.ticker == "AAPL"
    assert signal.action == Action.BUY
    assert signal.confidence == 78.5
    assert "momentum" in signal.rationale_tags


def test_signal_risk_reward_calculation():
    """Signal should calculate risk/reward ratio."""
    from quant.models import Signal, Action

    signal = Signal(
        ticker="AAPL",
        action=Action.BUY,
        size=Decimal("800.00"),
        confidence=78.5,
        rationale_tags=["momentum"],
        stop_loss=Decimal("177.70"),
        take_profit=Decimal("192.36"),
        entry_price=Decimal("183.20"),
        explanation="Test signal",
        strategy_name="test",
    )

    # Risk: 183.20 - 177.70 = 5.50
    # Reward: 192.36 - 183.20 = 9.16
    # Ratio: 9.16 / 5.50 = 1.665
    assert 1.6 < signal.risk_reward_ratio < 1.7


def test_market_context_creation():
    """MarketContext should hold all market data."""
    from quant.models import MarketContext, Position

    context = MarketContext(
        timestamp=datetime.now(timezone.utc),
        cash=Decimal("2000.00"),
        positions=[
            Position(ticker="AAPL", quantity=Decimal("5"), avg_price=Decimal("180.00"))
        ],
        futures_signal=0.3,  # Bullish
        vix=18.5,
        watchlist_sentiment={"AAPL": 0.72, "NVDA": 0.45},
        indicators={
            "AAPL": {"rsi": 58.0, "macd_signal": "bullish"},
        },
    )

    assert context.cash == Decimal("2000.00")
    assert len(context.positions) == 1
    assert context.futures_signal > 0  # Bullish


def test_backtest_result_metrics():
    """BacktestResult should compute derived metrics."""
    from quant.models import BacktestResult

    result = BacktestResult(
        total_return=0.25,
        total_trades=100,
        winning_trades=62,
        losing_trades=38,
        gross_profit=Decimal("5000.00"),
        gross_loss=Decimal("2500.00"),
        max_drawdown=0.08,
        sharpe_ratio=1.8,
    )

    assert result.win_rate == 0.62
    assert result.profit_factor == 2.0  # 5000 / 2500
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_models.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'quant.models'"

**Step 3: Write minimal implementation**

```python
# src/quant/models.py
"""Domain models for the quant trading system."""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, computed_field


class Action(str, Enum):
    """Trading action."""

    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


class Signal(BaseModel):
    """A trading signal generated by a strategy."""

    ticker: str = Field(..., description="Stock ticker symbol")
    action: Action = Field(..., description="Recommended action")
    size: Decimal = Field(..., description="Position size in dollars")
    confidence: float = Field(..., ge=0, le=100, description="Confidence 0-100")
    rationale_tags: list[str] = Field(default_factory=list)
    stop_loss: Decimal = Field(..., description="Stop loss price")
    take_profit: Decimal = Field(..., description="Take profit price")
    entry_price: Decimal = Field(..., description="Expected entry price")
    explanation: str = Field(..., description="Human-readable explanation")
    strategy_name: str = Field(..., description="Name of strategy that generated this")
    timestamp: datetime = Field(default_factory=lambda: datetime.now())

    @computed_field  # type: ignore[misc]
    @property
    def risk_reward_ratio(self) -> float:
        """Calculate risk/reward ratio for the signal."""
        if self.action == Action.BUY:
            risk = float(self.entry_price - self.stop_loss)
            reward = float(self.take_profit - self.entry_price)
        elif self.action == Action.SELL:
            risk = float(self.stop_loss - self.entry_price)
            reward = float(self.entry_price - self.take_profit)
        else:
            return 0.0

        if risk <= 0:
            return 0.0
        return reward / risk


class Position(BaseModel):
    """A current position in the portfolio."""

    ticker: str
    quantity: Decimal
    avg_price: Decimal
    current_price: Decimal | None = None

    @computed_field  # type: ignore[misc]
    @property
    def market_value(self) -> Decimal:
        """Current market value of position."""
        price = self.current_price or self.avg_price
        return self.quantity * price

    @computed_field  # type: ignore[misc]
    @property
    def unrealized_pnl(self) -> Decimal:
        """Unrealized profit/loss."""
        if self.current_price is None:
            return Decimal("0")
        return self.quantity * (self.current_price - self.avg_price)


class MarketContext(BaseModel):
    """All market data needed for strategy analysis."""

    timestamp: datetime
    cash: Decimal
    positions: list[Position] = Field(default_factory=list)
    futures_signal: float = Field(
        default=0.0, ge=-1, le=1, description="S&P futures direction -1 to 1"
    )
    vix: float = Field(default=20.0, description="VIX level")
    watchlist_sentiment: dict[str, float] = Field(
        default_factory=dict, description="Ticker -> sentiment score"
    )
    indicators: dict[str, dict[str, Any]] = Field(
        default_factory=dict, description="Ticker -> indicator values"
    )
    news: dict[str, list[str]] = Field(
        default_factory=dict, description="Ticker -> recent headlines"
    )

    @computed_field  # type: ignore[misc]
    @property
    def total_equity(self) -> Decimal:
        """Total account equity."""
        position_value = sum(p.market_value for p in self.positions)
        return self.cash + position_value


class BacktestResult(BaseModel):
    """Results from backtesting a strategy."""

    total_return: float = Field(..., description="Total return as decimal")
    total_trades: int
    winning_trades: int
    losing_trades: int
    gross_profit: Decimal
    gross_loss: Decimal
    max_drawdown: float = Field(..., description="Maximum drawdown as decimal")
    sharpe_ratio: float
    trades: list[dict[str, Any]] = Field(default_factory=list)

    @computed_field  # type: ignore[misc]
    @property
    def win_rate(self) -> float:
        """Percentage of winning trades."""
        if self.total_trades == 0:
            return 0.0
        return self.winning_trades / self.total_trades

    @computed_field  # type: ignore[misc]
    @property
    def profit_factor(self) -> float:
        """Ratio of gross profit to gross loss."""
        if self.gross_loss == 0:
            return float("inf") if self.gross_profit > 0 else 0.0
        return float(self.gross_profit / self.gross_loss)
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_models.py -v`
Expected: PASSED (4 tests)

**Step 5: Commit**

```bash
git add src/quant/models.py tests/test_models.py
git commit -m "feat: add domain models for signals, positions, and market context"
```

---

## Task 4: Strategy Protocol

**Files:**
- Create: `src/quant/strategy.py`
- Create: `tests/test_strategy.py`

**Step 1: Write the failing test**

```python
# tests/test_strategy.py
"""Tests for strategy protocol and base class."""

from datetime import datetime, timezone
from decimal import Decimal

import pytest


def test_strategy_protocol_compliance():
    """A strategy must implement the protocol."""
    from quant.strategy import Strategy
    from quant.models import MarketContext, Signal, BacktestResult

    class MockStrategy:
        name = "mock"
        version = "1.0"
        description = "A mock strategy for testing"

        def analyze(self, context: MarketContext) -> list[Signal]:
            return []

        def explain(self, signal: Signal) -> str:
            return "Mock explanation"

        def backtest(self, historical: list[MarketContext]) -> BacktestResult:
            return BacktestResult(
                total_return=0.0,
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                gross_profit=Decimal("0"),
                gross_loss=Decimal("0"),
                max_drawdown=0.0,
                sharpe_ratio=0.0,
            )

    # Should be able to use as Strategy type
    strategy: Strategy = MockStrategy()
    assert strategy.name == "mock"


def test_strategy_registry_add_and_get():
    """Registry should store and retrieve strategies."""
    from quant.strategy import StrategyRegistry, Strategy
    from quant.models import MarketContext, Signal, BacktestResult

    class TestStrategy:
        name = "test_strat"
        version = "1.0"
        description = "Test"

        def analyze(self, context: MarketContext) -> list[Signal]:
            return []

        def explain(self, signal: Signal) -> str:
            return ""

        def backtest(self, historical: list[MarketContext]) -> BacktestResult:
            return BacktestResult(
                total_return=0.0, total_trades=0, winning_trades=0,
                losing_trades=0, gross_profit=Decimal("0"), gross_loss=Decimal("0"),
                max_drawdown=0.0, sharpe_ratio=0.0,
            )

    registry = StrategyRegistry()
    registry.register(TestStrategy())

    assert "test_strat" in registry.list_strategies()
    assert registry.get("test_strat").name == "test_strat"


def test_strategy_registry_unknown_raises():
    """Getting unknown strategy should raise."""
    from quant.strategy import StrategyRegistry

    registry = StrategyRegistry()

    with pytest.raises(KeyError):
        registry.get("nonexistent")
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_strategy.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'quant.strategy'"

**Step 3: Write minimal implementation**

```python
# src/quant/strategy.py
"""Strategy protocol and registry."""

from typing import Protocol, runtime_checkable

from quant.models import BacktestResult, MarketContext, Signal


@runtime_checkable
class Strategy(Protocol):
    """Protocol that all trading strategies must implement."""

    name: str
    version: str
    description: str

    def analyze(self, context: MarketContext) -> list[Signal]:
        """Analyze market context and return trading signals."""
        ...

    def explain(self, signal: Signal) -> str:
        """Generate human-readable explanation for a signal."""
        ...

    def backtest(self, historical: list[MarketContext]) -> BacktestResult:
        """Run strategy against historical market data."""
        ...


class StrategyRegistry:
    """Registry for strategy instances."""

    def __init__(self) -> None:
        self._strategies: dict[str, Strategy] = {}

    def register(self, strategy: Strategy) -> None:
        """Register a strategy instance."""
        self._strategies[strategy.name] = strategy

    def get(self, name: str) -> Strategy:
        """Get a strategy by name. Raises KeyError if not found."""
        if name not in self._strategies:
            raise KeyError(f"Strategy '{name}' not found")
        return self._strategies[name]

    def list_strategies(self) -> list[str]:
        """List all registered strategy names."""
        return list(self._strategies.keys())

    def all(self) -> list[Strategy]:
        """Get all registered strategies."""
        return list(self._strategies.values())
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_strategy.py -v`
Expected: PASSED (3 tests)

**Step 5: Commit**

```bash
git add src/quant/strategy.py tests/test_strategy.py
git commit -m "feat: add strategy protocol and registry"
```

---

## Task 5: Risk Manager

**Files:**
- Create: `src/quant/risk.py`
- Create: `tests/test_risk.py`

**Step 1: Write the failing test**

```python
# tests/test_risk.py
"""Tests for risk management."""

from datetime import datetime, timezone
from decimal import Decimal

import pytest


def test_risk_manager_allows_trade_with_sufficient_capital():
    """Should allow trade when capital is available."""
    from quant.risk import RiskManager
    from quant.models import Signal, Action, MarketContext

    manager = RiskManager(
        base_reserve=1000,
        max_position_size=1000,
        max_concurrent_positions=5,
        max_daily_loss=200,
    )

    context = MarketContext(
        timestamp=datetime.now(timezone.utc),
        cash=Decimal("2000.00"),
        positions=[],
    )

    signal = Signal(
        ticker="AAPL",
        action=Action.BUY,
        size=Decimal("800.00"),
        confidence=78.0,
        rationale_tags=["momentum"],
        stop_loss=Decimal("177.70"),
        take_profit=Decimal("192.36"),
        entry_price=Decimal("183.20"),
        explanation="Test",
        strategy_name="test",
    )

    result = manager.validate_signal(signal, context)
    assert result.allowed is True


def test_risk_manager_blocks_trade_below_reserve():
    """Should block trade that would dip into base reserve."""
    from quant.risk import RiskManager
    from quant.models import Signal, Action, MarketContext

    manager = RiskManager(
        base_reserve=1000,
        max_position_size=1000,
        max_concurrent_positions=5,
        max_daily_loss=200,
    )

    # Only $1100 cash, $1000 is reserve, only $100 available
    context = MarketContext(
        timestamp=datetime.now(timezone.utc),
        cash=Decimal("1100.00"),
        positions=[],
    )

    signal = Signal(
        ticker="AAPL",
        action=Action.BUY,
        size=Decimal("800.00"),
        confidence=78.0,
        rationale_tags=["momentum"],
        stop_loss=Decimal("177.70"),
        take_profit=Decimal("192.36"),
        entry_price=Decimal("183.20"),
        explanation="Test",
        strategy_name="test",
    )

    result = manager.validate_signal(signal, context)
    assert result.allowed is False
    assert "reserve" in result.reason.lower()


def test_risk_manager_caps_position_size():
    """Should reduce position size to max allowed."""
    from quant.risk import RiskManager
    from quant.models import Signal, Action, MarketContext

    manager = RiskManager(
        base_reserve=1000,
        max_position_size=500,  # Max $500
        max_concurrent_positions=5,
        max_daily_loss=200,
    )

    context = MarketContext(
        timestamp=datetime.now(timezone.utc),
        cash=Decimal("3000.00"),
        positions=[],
    )

    signal = Signal(
        ticker="AAPL",
        action=Action.BUY,
        size=Decimal("800.00"),  # Requested $800
        confidence=78.0,
        rationale_tags=["momentum"],
        stop_loss=Decimal("177.70"),
        take_profit=Decimal("192.36"),
        entry_price=Decimal("183.20"),
        explanation="Test",
        strategy_name="test",
    )

    result = manager.validate_signal(signal, context)
    assert result.allowed is True
    assert result.adjusted_size == Decimal("500.00")


def test_risk_manager_blocks_at_max_positions():
    """Should block new positions when at limit."""
    from quant.risk import RiskManager
    from quant.models import Signal, Action, MarketContext, Position

    manager = RiskManager(
        base_reserve=1000,
        max_position_size=1000,
        max_concurrent_positions=2,  # Only 2 allowed
        max_daily_loss=200,
    )

    context = MarketContext(
        timestamp=datetime.now(timezone.utc),
        cash=Decimal("5000.00"),
        positions=[
            Position(ticker="AAPL", quantity=Decimal("5"), avg_price=Decimal("180")),
            Position(ticker="NVDA", quantity=Decimal("2"), avg_price=Decimal("500")),
        ],
    )

    signal = Signal(
        ticker="META",
        action=Action.BUY,
        size=Decimal("800.00"),
        confidence=78.0,
        rationale_tags=["momentum"],
        stop_loss=Decimal("300.00"),
        take_profit=Decimal("350.00"),
        entry_price=Decimal("320.00"),
        explanation="Test",
        strategy_name="test",
    )

    result = manager.validate_signal(signal, context)
    assert result.allowed is False
    assert "position" in result.reason.lower()
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_risk.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'quant.risk'"

**Step 3: Write minimal implementation**

```python
# src/quant/risk.py
"""Risk management and position sizing."""

from dataclasses import dataclass
from decimal import Decimal

from quant.models import Action, MarketContext, Signal


@dataclass
class ValidationResult:
    """Result of validating a signal against risk rules."""

    allowed: bool
    reason: str
    adjusted_size: Decimal | None = None


class RiskManager:
    """Enforces risk limits and position sizing rules."""

    def __init__(
        self,
        base_reserve: int,
        max_position_size: int,
        max_concurrent_positions: int,
        max_daily_loss: int,
    ) -> None:
        self.base_reserve = Decimal(base_reserve)
        self.max_position_size = Decimal(max_position_size)
        self.max_concurrent_positions = max_concurrent_positions
        self.max_daily_loss = Decimal(max_daily_loss)
        self._daily_pnl = Decimal("0")

    def validate_signal(
        self, signal: Signal, context: MarketContext
    ) -> ValidationResult:
        """Validate a signal against all risk rules."""
        # Check daily loss limit
        if self._daily_pnl <= -self.max_daily_loss:
            return ValidationResult(
                allowed=False,
                reason="Daily loss limit reached. No new positions until tomorrow.",
            )

        # Check position count for new buys
        if signal.action == Action.BUY:
            current_tickers = {p.ticker for p in context.positions}
            if (
                signal.ticker not in current_tickers
                and len(context.positions) >= self.max_concurrent_positions
            ):
                return ValidationResult(
                    allowed=False,
                    reason=f"Maximum concurrent positions ({self.max_concurrent_positions}) reached.",
                )

        # Check available capital (cash - reserve)
        available = context.cash - self.base_reserve
        if available <= 0:
            return ValidationResult(
                allowed=False,
                reason="Cannot trade: would dip into base reserve.",
            )

        # Adjust position size if needed
        adjusted_size = min(signal.size, self.max_position_size, available)

        if adjusted_size < signal.size:
            return ValidationResult(
                allowed=True,
                reason=f"Position size adjusted from ${signal.size} to ${adjusted_size}",
                adjusted_size=adjusted_size,
            )

        return ValidationResult(
            allowed=True,
            reason="Signal validated",
            adjusted_size=signal.size,
        )

    def record_pnl(self, pnl: Decimal) -> None:
        """Record realized P&L for daily tracking."""
        self._daily_pnl += pnl

    def reset_daily(self) -> None:
        """Reset daily P&L tracker (call at market open)."""
        self._daily_pnl = Decimal("0")

    def can_trade(self, context: MarketContext) -> bool:
        """Quick check if any trading is allowed."""
        if self._daily_pnl <= -self.max_daily_loss:
            return False
        available = context.cash - self.base_reserve
        return available > 0
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_risk.py -v`
Expected: PASSED (4 tests)

**Step 5: Commit**

```bash
git add src/quant/risk.py tests/test_risk.py
git commit -m "feat: add risk manager with position limits and reserve protection"
```

---

## Task 6: Alpaca Client Wrapper

**Files:**
- Create: `src/quant/broker.py`
- Create: `tests/test_broker.py`

**Step 1: Write the failing test**

```python
# tests/test_broker.py
"""Tests for broker integration."""

from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest


def test_alpaca_client_get_account():
    """Should fetch account info from Alpaca."""
    from quant.broker import AlpacaClient

    mock_api = MagicMock()
    mock_api.get_account.return_value = MagicMock(
        cash="2500.00",
        equity="3200.00",
        buying_power="5000.00",
    )

    with patch("quant.broker.TradingClient", return_value=mock_api):
        client = AlpacaClient(
            api_key="test",
            secret_key="test",
            paper=True,
        )
        account = client.get_account()

        assert account.cash == Decimal("2500.00")
        assert account.equity == Decimal("3200.00")


def test_alpaca_client_get_positions():
    """Should fetch current positions."""
    from quant.broker import AlpacaClient

    mock_api = MagicMock()
    mock_api.get_all_positions.return_value = [
        MagicMock(
            symbol="AAPL",
            qty="5",
            avg_entry_price="180.50",
            current_price="185.20",
        ),
    ]

    with patch("quant.broker.TradingClient", return_value=mock_api):
        client = AlpacaClient(
            api_key="test",
            secret_key="test",
            paper=True,
        )
        positions = client.get_positions()

        assert len(positions) == 1
        assert positions[0].ticker == "AAPL"
        assert positions[0].quantity == Decimal("5")


def test_alpaca_client_submit_order():
    """Should submit market order."""
    from quant.broker import AlpacaClient, OrderSide

    mock_api = MagicMock()
    mock_api.submit_order.return_value = MagicMock(
        id="order-123",
        status="accepted",
        symbol="AAPL",
        qty="5",
        side="buy",
    )

    with patch("quant.broker.TradingClient", return_value=mock_api):
        client = AlpacaClient(
            api_key="test",
            secret_key="test",
            paper=True,
        )
        order = client.submit_market_order(
            ticker="AAPL",
            side=OrderSide.BUY,
            notional=Decimal("900.00"),
        )

        assert order.order_id == "order-123"
        assert order.status == "accepted"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_broker.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'quant.broker'"

**Step 3: Write minimal implementation**

```python
# src/quant/broker.py
"""Alpaca broker integration."""

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

from alpaca.trading.client import TradingClient
from alpaca.trading.enums import OrderSide as AlpacaOrderSide
from alpaca.trading.enums import TimeInForce
from alpaca.trading.requests import MarketOrderRequest

from quant.models import Position


class OrderSide(str, Enum):
    """Order side."""

    BUY = "buy"
    SELL = "sell"


@dataclass
class AccountInfo:
    """Account information from broker."""

    cash: Decimal
    equity: Decimal
    buying_power: Decimal


@dataclass
class OrderResult:
    """Result of order submission."""

    order_id: str
    status: str
    ticker: str
    side: OrderSide
    quantity: Decimal | None = None
    notional: Decimal | None = None


class AlpacaClient:
    """Wrapper around Alpaca trading API."""

    def __init__(
        self,
        api_key: str,
        secret_key: str,
        paper: bool = True,
    ) -> None:
        self._client = TradingClient(
            api_key=api_key,
            secret_key=secret_key,
            paper=paper,
        )

    def get_account(self) -> AccountInfo:
        """Fetch current account information."""
        account = self._client.get_account()
        return AccountInfo(
            cash=Decimal(str(account.cash)),
            equity=Decimal(str(account.equity)),
            buying_power=Decimal(str(account.buying_power)),
        )

    def get_positions(self) -> list[Position]:
        """Fetch all current positions."""
        positions = self._client.get_all_positions()
        return [
            Position(
                ticker=p.symbol,
                quantity=Decimal(str(p.qty)),
                avg_price=Decimal(str(p.avg_entry_price)),
                current_price=Decimal(str(p.current_price))
                if p.current_price
                else None,
            )
            for p in positions
        ]

    def submit_market_order(
        self,
        ticker: str,
        side: OrderSide,
        notional: Decimal | None = None,
        quantity: Decimal | None = None,
    ) -> OrderResult:
        """Submit a market order by notional amount or quantity."""
        alpaca_side = (
            AlpacaOrderSide.BUY if side == OrderSide.BUY else AlpacaOrderSide.SELL
        )

        request = MarketOrderRequest(
            symbol=ticker,
            side=alpaca_side,
            time_in_force=TimeInForce.DAY,
            notional=float(notional) if notional else None,
            qty=float(quantity) if quantity else None,
        )

        order = self._client.submit_order(request)

        return OrderResult(
            order_id=str(order.id),
            status=str(order.status),
            ticker=order.symbol,
            side=side,
            quantity=Decimal(str(order.qty)) if order.qty else None,
            notional=notional,
        )

    def close_position(self, ticker: str) -> OrderResult:
        """Close entire position for a ticker."""
        order = self._client.close_position(ticker)
        return OrderResult(
            order_id=str(order.id),
            status=str(order.status),
            ticker=order.symbol,
            side=OrderSide.SELL,
            quantity=Decimal(str(order.qty)) if order.qty else None,
        )
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_broker.py -v`
Expected: PASSED (3 tests)

**Step 5: Commit**

```bash
git add src/quant/broker.py tests/test_broker.py
git commit -m "feat: add Alpaca broker client wrapper"
```

---

## Task 7: Market Data Pipeline

**Files:**
- Create: `src/quant/data.py`
- Create: `tests/test_data.py`

**Step 1: Write the failing test**

```python
# tests/test_data.py
"""Tests for market data pipeline."""

from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest


def test_market_data_fetches_bars():
    """Should fetch OHLCV bars for watchlist."""
    from quant.data import MarketDataPipeline

    mock_client = MagicMock()
    mock_bar = MagicMock(
        open=180.0,
        high=185.0,
        low=179.0,
        close=184.0,
        volume=50000000,
        timestamp=datetime.now(timezone.utc),
    )
    mock_client.get_stock_bars.return_value = {"AAPL": [mock_bar]}

    with patch("quant.data.StockHistoricalDataClient", return_value=mock_client):
        pipeline = MarketDataPipeline(
            api_key="test",
            secret_key="test",
            watchlist=["AAPL", "NVDA"],
        )
        bars = pipeline.get_latest_bars(["AAPL"])

        assert "AAPL" in bars
        assert bars["AAPL"].close == 184.0


def test_market_data_computes_indicators():
    """Should compute technical indicators from bars."""
    from quant.data import MarketDataPipeline, compute_rsi
    import pandas as pd

    # Create sample price data
    closes = pd.Series([
        100, 102, 101, 103, 105, 104, 106, 108, 107, 109,
        111, 110, 112, 114, 113,
    ])

    rsi = compute_rsi(closes, period=14)

    # RSI should be between 0 and 100
    assert 0 <= rsi <= 100


def test_market_data_builds_context():
    """Should build MarketContext from all data sources."""
    from quant.data import MarketDataPipeline
    from quant.models import Position

    mock_client = MagicMock()
    mock_bar = MagicMock(
        open=180.0, high=185.0, low=179.0, close=184.0,
        volume=50000000, timestamp=datetime.now(timezone.utc),
    )
    mock_client.get_stock_bars.return_value = {
        "AAPL": [mock_bar],
        "NVDA": [mock_bar],
    }

    with patch("quant.data.StockHistoricalDataClient", return_value=mock_client):
        pipeline = MarketDataPipeline(
            api_key="test",
            secret_key="test",
            watchlist=["AAPL", "NVDA"],
        )

        context = pipeline.build_context(
            cash=Decimal("2000.00"),
            positions=[],
        )

        assert context.cash == Decimal("2000.00")
        assert "AAPL" in context.indicators
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_data.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'quant.data'"

**Step 3: Write minimal implementation**

```python
# src/quant/data.py
"""Market data pipeline."""

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

import pandas as pd
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame

from quant.models import MarketContext, Position


@dataclass
class Bar:
    """OHLCV bar data."""

    open: float
    high: float
    low: float
    close: float
    volume: int
    timestamp: datetime


def compute_rsi(prices: pd.Series, period: int = 14) -> float:
    """Compute Relative Strength Index."""
    delta = prices.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)

    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    return float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else 50.0


def compute_macd(
    prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9
) -> dict[str, float]:
    """Compute MACD indicator."""
    exp1 = prices.ewm(span=fast, adjust=False).mean()
    exp2 = prices.ewm(span=slow, adjust=False).mean()
    macd = exp1 - exp2
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    histogram = macd - signal_line

    return {
        "macd": float(macd.iloc[-1]),
        "signal": float(signal_line.iloc[-1]),
        "histogram": float(histogram.iloc[-1]),
    }


class MarketDataPipeline:
    """Fetches and processes market data for strategies."""

    def __init__(
        self,
        api_key: str,
        secret_key: str,
        watchlist: list[str],
    ) -> None:
        self._client = StockHistoricalDataClient(
            api_key=api_key,
            secret_key=secret_key,
        )
        self.watchlist = watchlist

    def get_latest_bars(
        self, tickers: list[str] | None = None, days: int = 30
    ) -> dict[str, Bar]:
        """Fetch latest bars for tickers."""
        symbols = tickers or self.watchlist

        request = StockBarsRequest(
            symbol_or_symbols=symbols,
            timeframe=TimeFrame.Day,
            limit=days,
        )

        bars_data = self._client.get_stock_bars(request)

        result = {}
        for symbol, bars in bars_data.items():
            if bars:
                latest = bars[-1]
                result[symbol] = Bar(
                    open=float(latest.open),
                    high=float(latest.high),
                    low=float(latest.low),
                    close=float(latest.close),
                    volume=int(latest.volume),
                    timestamp=latest.timestamp,
                )

        return result

    def get_historical_bars(
        self, ticker: str, days: int = 60
    ) -> pd.DataFrame:
        """Fetch historical bars as DataFrame."""
        request = StockBarsRequest(
            symbol_or_symbols=[ticker],
            timeframe=TimeFrame.Day,
            limit=days,
        )

        bars = self._client.get_stock_bars(request)

        if ticker not in bars or not bars[ticker]:
            return pd.DataFrame()

        data = [
            {
                "open": float(b.open),
                "high": float(b.high),
                "low": float(b.low),
                "close": float(b.close),
                "volume": int(b.volume),
                "timestamp": b.timestamp,
            }
            for b in bars[ticker]
        ]

        return pd.DataFrame(data)

    def compute_indicators(self, ticker: str) -> dict[str, Any]:
        """Compute technical indicators for a ticker."""
        df = self.get_historical_bars(ticker, days=60)

        if df.empty:
            return {}

        closes = df["close"]

        return {
            "rsi": compute_rsi(closes),
            "macd": compute_macd(closes),
            "sma_20": float(closes.rolling(20).mean().iloc[-1]),
            "sma_50": float(closes.rolling(50).mean().iloc[-1]) if len(closes) >= 50 else None,
            "volume_avg_20": float(df["volume"].rolling(20).mean().iloc[-1]),
            "volume_ratio": float(df["volume"].iloc[-1] / df["volume"].rolling(20).mean().iloc[-1]),
        }

    def build_context(
        self,
        cash: Decimal,
        positions: list[Position],
        futures_signal: float = 0.0,
        vix: float = 20.0,
    ) -> MarketContext:
        """Build complete market context for strategy analysis."""
        # Get latest bars for all watchlist
        latest_bars = self.get_latest_bars()

        # Update position prices
        for position in positions:
            if position.ticker in latest_bars:
                position.current_price = Decimal(str(latest_bars[position.ticker].close))

        # Compute indicators for each ticker
        indicators = {}
        for ticker in self.watchlist:
            try:
                indicators[ticker] = self.compute_indicators(ticker)
            except Exception:
                indicators[ticker] = {}

        return MarketContext(
            timestamp=datetime.now(timezone.utc),
            cash=cash,
            positions=positions,
            futures_signal=futures_signal,
            vix=vix,
            indicators=indicators,
        )
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_data.py -v`
Expected: PASSED (3 tests)

**Step 5: Commit**

```bash
git add src/quant/data.py tests/test_data.py
git commit -m "feat: add market data pipeline with technical indicators"
```

---

## Task 8: First Strategy - Momentum Breakout

**Files:**
- Create: `src/quant/strategies/__init__.py`
- Create: `src/quant/strategies/momentum_breakout.py`
- Create: `tests/test_strategies/test_momentum_breakout.py`

**Step 1: Write the failing test**

```python
# tests/test_strategies/__init__.py
"""Strategy tests."""
```

```python
# tests/test_strategies/test_momentum_breakout.py
"""Tests for momentum breakout strategy."""

from datetime import datetime, timezone
from decimal import Decimal


def test_momentum_breakout_generates_buy_signal():
    """Should generate BUY signal on breakout with volume."""
    from quant.strategies.momentum_breakout import MomentumBreakoutStrategy
    from quant.models import MarketContext, Action

    strategy = MomentumBreakoutStrategy()

    context = MarketContext(
        timestamp=datetime.now(timezone.utc),
        cash=Decimal("2000.00"),
        positions=[],
        indicators={
            "AAPL": {
                "rsi": 58.0,  # Not overbought
                "macd": {"macd": 1.5, "signal": 1.0, "histogram": 0.5},  # Bullish
                "sma_20": 180.0,
                "volume_ratio": 1.5,  # Above average volume
                "current_price": 185.0,  # Above SMA20
            },
        },
    )

    signals = strategy.analyze(context)

    # Should find AAPL as a buy
    aapl_signals = [s for s in signals if s.ticker == "AAPL"]
    assert len(aapl_signals) == 1
    assert aapl_signals[0].action == Action.BUY
    assert aapl_signals[0].confidence >= 70


def test_momentum_breakout_skips_overbought():
    """Should skip when RSI is overbought."""
    from quant.strategies.momentum_breakout import MomentumBreakoutStrategy
    from quant.models import MarketContext

    strategy = MomentumBreakoutStrategy()

    context = MarketContext(
        timestamp=datetime.now(timezone.utc),
        cash=Decimal("2000.00"),
        positions=[],
        indicators={
            "AAPL": {
                "rsi": 75.0,  # Overbought
                "macd": {"macd": 1.5, "signal": 1.0, "histogram": 0.5},
                "sma_20": 180.0,
                "volume_ratio": 1.5,
                "current_price": 185.0,
            },
        },
    )

    signals = strategy.analyze(context)

    # Should not generate signal for overbought stock
    aapl_signals = [s for s in signals if s.ticker == "AAPL"]
    assert len(aapl_signals) == 0


def test_momentum_breakout_explain():
    """Should generate human-readable explanation."""
    from quant.strategies.momentum_breakout import MomentumBreakoutStrategy
    from quant.models import Signal, Action

    strategy = MomentumBreakoutStrategy()

    signal = Signal(
        ticker="AAPL",
        action=Action.BUY,
        size=Decimal("800"),
        confidence=78.0,
        rationale_tags=["breakout", "volume_confirm", "macd_bullish"],
        stop_loss=Decimal("177.70"),
        take_profit=Decimal("192.36"),
        entry_price=Decimal("183.20"),
        explanation="",
        strategy_name="momentum_breakout",
    )

    explanation = strategy.explain(signal)

    assert "AAPL" in explanation
    assert "breakout" in explanation.lower()
    assert "78" in explanation  # Confidence
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_strategies/test_momentum_breakout.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

```python
# src/quant/strategies/__init__.py
"""Trading strategies."""

from quant.strategies.momentum_breakout import MomentumBreakoutStrategy

__all__ = ["MomentumBreakoutStrategy"]
```

```python
# src/quant/strategies/momentum_breakout.py
"""Momentum breakout strategy.

Buys when:
- Price breaks above 20-day SMA
- Volume is above average (confirms breakout)
- RSI is not overbought (<70)
- MACD is bullish (histogram > 0)
"""

from decimal import Decimal
from typing import Any

from quant.models import Action, BacktestResult, MarketContext, Signal


class MomentumBreakoutStrategy:
    """Buy on price/volume breakouts above resistance."""

    name = "momentum_breakout"
    version = "1.0"
    description = "Buy when price breaks above SMA20 with volume confirmation"

    # Configurable parameters
    rsi_overbought = 70
    rsi_oversold = 30
    volume_threshold = 1.2  # 20% above average
    stop_loss_pct = 0.03  # 3%
    take_profit_pct = 0.05  # 5%
    base_position_size = Decimal("800")

    def analyze(self, context: MarketContext) -> list[Signal]:
        """Analyze market and return trading signals."""
        signals = []

        for ticker, indicators in context.indicators.items():
            signal = self._analyze_ticker(ticker, indicators, context)
            if signal:
                signals.append(signal)

        return signals

    def _analyze_ticker(
        self, ticker: str, indicators: dict[str, Any], context: MarketContext
    ) -> Signal | None:
        """Analyze a single ticker for breakout conditions."""
        # Skip if missing required indicators
        required = ["rsi", "macd", "sma_20", "volume_ratio", "current_price"]
        if not all(k in indicators for k in required):
            return None

        rsi = indicators["rsi"]
        macd = indicators["macd"]
        sma_20 = indicators["sma_20"]
        volume_ratio = indicators["volume_ratio"]
        current_price = indicators["current_price"]

        # Check conditions
        conditions = {
            "breakout": current_price > sma_20,
            "volume_confirm": volume_ratio >= self.volume_threshold,
            "not_overbought": rsi < self.rsi_overbought,
            "macd_bullish": macd["histogram"] > 0,
        }

        # Need all conditions for a signal
        if not all(conditions.values()):
            return None

        # Calculate confidence based on strength of signals
        confidence = self._calculate_confidence(indicators, conditions)

        # Calculate stop loss and take profit
        entry_price = Decimal(str(current_price))
        stop_loss = entry_price * (1 - Decimal(str(self.stop_loss_pct)))
        take_profit = entry_price * (1 + Decimal(str(self.take_profit_pct)))

        # Build rationale tags
        rationale_tags = [k for k, v in conditions.items() if v]

        return Signal(
            ticker=ticker,
            action=Action.BUY,
            size=self.base_position_size,
            confidence=confidence,
            rationale_tags=rationale_tags,
            stop_loss=stop_loss.quantize(Decimal("0.01")),
            take_profit=take_profit.quantize(Decimal("0.01")),
            entry_price=entry_price.quantize(Decimal("0.01")),
            explanation=self._build_explanation(ticker, indicators, conditions, confidence),
            strategy_name=self.name,
        )

    def _calculate_confidence(
        self, indicators: dict[str, Any], conditions: dict[str, bool]
    ) -> float:
        """Calculate confidence score 0-100."""
        base = 60.0  # Start at 60 if all conditions met

        # Add for RSI in healthy range (40-60)
        rsi = indicators["rsi"]
        if 40 <= rsi <= 60:
            base += 10
        elif 30 <= rsi < 40 or 60 < rsi <= 70:
            base += 5

        # Add for strong volume
        volume_ratio = indicators["volume_ratio"]
        if volume_ratio >= 1.5:
            base += 10
        elif volume_ratio >= 1.3:
            base += 5

        # Add for strong MACD
        histogram = indicators["macd"]["histogram"]
        if histogram > 1.0:
            base += 10
        elif histogram > 0.5:
            base += 5

        return min(base, 95.0)  # Cap at 95

    def _build_explanation(
        self,
        ticker: str,
        indicators: dict[str, Any],
        conditions: dict[str, bool],
        confidence: float,
    ) -> str:
        """Build human-readable explanation."""
        lines = [
            f"{ticker} BUY SIGNAL — {confidence:.0f}% Confidence",
            "",
            "TECHNICAL ANALYSIS",
            f"• Price: ${indicators['current_price']:.2f} (above SMA20 ${indicators['sma_20']:.2f})",
            f"• RSI: {indicators['rsi']:.1f} ({'healthy' if indicators['rsi'] < 70 else 'elevated'})",
            f"• MACD Histogram: {indicators['macd']['histogram']:.2f} (bullish)",
            f"• Volume: {indicators['volume_ratio']:.1f}x average",
            "",
            "CONDITIONS MET",
        ]

        for condition, met in conditions.items():
            status = "✓" if met else "✗"
            lines.append(f"  {status} {condition.replace('_', ' ').title()}")

        lines.extend([
            "",
            f"STRATEGY: {self.name} v{self.version}",
        ])

        return "\n".join(lines)

    def explain(self, signal: Signal) -> str:
        """Generate human-readable explanation for a signal."""
        lines = [
            f"{signal.ticker} {signal.action.value.upper()} — {signal.confidence:.0f}% Confidence",
            "",
            f"Entry: ${signal.entry_price}",
            f"Stop Loss: ${signal.stop_loss} ({self.stop_loss_pct*100:.0f}%)",
            f"Take Profit: ${signal.take_profit} ({self.take_profit_pct*100:.0f}%)",
            f"Risk/Reward: 1:{signal.risk_reward_ratio:.2f}",
            "",
            "Rationale:",
        ]

        for tag in signal.rationale_tags:
            lines.append(f"  • {tag.replace('_', ' ').title()}")

        lines.extend([
            "",
            f"Strategy: {self.name} v{self.version}",
        ])

        return "\n".join(lines)

    def backtest(self, historical: list[MarketContext]) -> BacktestResult:
        """Run strategy against historical market data."""
        # Placeholder - will implement full backtesting later
        return BacktestResult(
            total_return=0.0,
            total_trades=0,
            winning_trades=0,
            losing_trades=0,
            gross_profit=Decimal("0"),
            gross_loss=Decimal("0"),
            max_drawdown=0.0,
            sharpe_ratio=0.0,
        )
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_strategies/test_momentum_breakout.py -v`
Expected: PASSED (3 tests)

**Step 5: Commit**

```bash
git add src/quant/strategies/ tests/test_strategies/
git commit -m "feat: add momentum breakout strategy"
```

---

## Task 9: Decision Engine

**Files:**
- Create: `src/quant/engine.py`
- Create: `tests/test_engine.py`

**Step 1: Write the failing test**

```python
# tests/test_engine.py
"""Tests for the decision engine."""

from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock


def test_engine_runs_strategy_and_validates():
    """Engine should run strategy and validate through risk manager."""
    from quant.engine import DecisionEngine
    from quant.models import MarketContext, Signal, Action
    from quant.strategy import StrategyRegistry
    from quant.risk import RiskManager

    # Create a mock strategy
    mock_strategy = MagicMock()
    mock_strategy.name = "test_strategy"
    mock_strategy.analyze.return_value = [
        Signal(
            ticker="AAPL",
            action=Action.BUY,
            size=Decimal("800"),
            confidence=78.0,
            rationale_tags=["momentum"],
            stop_loss=Decimal("177.70"),
            take_profit=Decimal("192.36"),
            entry_price=Decimal("183.20"),
            explanation="Test signal",
            strategy_name="test_strategy",
        )
    ]

    registry = StrategyRegistry()
    registry.register(mock_strategy)

    risk_manager = RiskManager(
        base_reserve=1000,
        max_position_size=1000,
        max_concurrent_positions=5,
        max_daily_loss=200,
    )

    engine = DecisionEngine(
        registry=registry,
        risk_manager=risk_manager,
        active_strategy="test_strategy",
        confidence_threshold=70,
    )

    context = MarketContext(
        timestamp=datetime.now(timezone.utc),
        cash=Decimal("2000.00"),
        positions=[],
    )

    recommendations = engine.analyze(context)

    assert len(recommendations) == 1
    assert recommendations[0].signal.ticker == "AAPL"
    assert recommendations[0].approved is True


def test_engine_filters_low_confidence():
    """Engine should filter signals below confidence threshold."""
    from quant.engine import DecisionEngine
    from quant.models import MarketContext, Signal, Action
    from quant.strategy import StrategyRegistry
    from quant.risk import RiskManager

    mock_strategy = MagicMock()
    mock_strategy.name = "test_strategy"
    mock_strategy.analyze.return_value = [
        Signal(
            ticker="AAPL",
            action=Action.BUY,
            size=Decimal("800"),
            confidence=65.0,  # Below threshold
            rationale_tags=["momentum"],
            stop_loss=Decimal("177.70"),
            take_profit=Decimal("192.36"),
            entry_price=Decimal("183.20"),
            explanation="Test signal",
            strategy_name="test_strategy",
        )
    ]

    registry = StrategyRegistry()
    registry.register(mock_strategy)

    risk_manager = RiskManager(
        base_reserve=1000,
        max_position_size=1000,
        max_concurrent_positions=5,
        max_daily_loss=200,
    )

    engine = DecisionEngine(
        registry=registry,
        risk_manager=risk_manager,
        active_strategy="test_strategy",
        confidence_threshold=70,  # Threshold is 70
    )

    context = MarketContext(
        timestamp=datetime.now(timezone.utc),
        cash=Decimal("2000.00"),
        positions=[],
    )

    recommendations = engine.analyze(context)

    assert len(recommendations) == 0
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_engine.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'quant.engine'"

**Step 3: Write minimal implementation**

```python
# src/quant/engine.py
"""Decision engine that orchestrates strategies and risk management."""

from dataclasses import dataclass
from decimal import Decimal

from quant.models import MarketContext, Signal
from quant.risk import RiskManager, ValidationResult
from quant.strategy import Strategy, StrategyRegistry


@dataclass
class Recommendation:
    """A validated trading recommendation."""

    signal: Signal
    validation: ValidationResult
    approved: bool
    adjusted_size: Decimal | None = None

    @property
    def rejection_reason(self) -> str | None:
        """Get reason for rejection if not approved."""
        if self.approved:
            return None
        return self.validation.reason


class DecisionEngine:
    """Orchestrates strategy execution and risk validation."""

    def __init__(
        self,
        registry: StrategyRegistry,
        risk_manager: RiskManager,
        active_strategy: str,
        confidence_threshold: float = 70.0,
    ) -> None:
        self.registry = registry
        self.risk_manager = risk_manager
        self.active_strategy = active_strategy
        self.confidence_threshold = confidence_threshold

    def get_strategy(self) -> Strategy:
        """Get the currently active strategy."""
        return self.registry.get(self.active_strategy)

    def analyze(self, context: MarketContext) -> list[Recommendation]:
        """Run analysis and return validated recommendations."""
        strategy = self.get_strategy()
        signals = strategy.analyze(context)

        recommendations = []
        for signal in signals:
            # Filter by confidence threshold
            if signal.confidence < self.confidence_threshold:
                continue

            # Validate against risk rules
            validation = self.risk_manager.validate_signal(signal, context)

            recommendation = Recommendation(
                signal=signal,
                validation=validation,
                approved=validation.allowed,
                adjusted_size=validation.adjusted_size,
            )
            recommendations.append(recommendation)

        return recommendations

    def set_active_strategy(self, name: str) -> None:
        """Change the active strategy."""
        # Verify it exists
        self.registry.get(name)
        self.active_strategy = name

    def set_confidence_threshold(self, threshold: float) -> None:
        """Update the confidence threshold."""
        if not 0 <= threshold <= 100:
            raise ValueError("Threshold must be between 0 and 100")
        self.confidence_threshold = threshold
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_engine.py -v`
Expected: PASSED (2 tests)

**Step 5: Commit**

```bash
git add src/quant/engine.py tests/test_engine.py
git commit -m "feat: add decision engine to orchestrate strategies and risk"
```

---

## Task 10: FastAPI Server

**Files:**
- Create: `src/quant/api.py`
- Create: `tests/test_api.py`

**Step 1: Write the failing test**

```python
# tests/test_api.py
"""Tests for the FastAPI server."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client with mocked dependencies."""
    with patch("quant.api.get_settings") as mock_settings:
        mock_settings.return_value = MagicMock(
            alpaca_api_key="test",
            alpaca_secret_key="test",
            alpaca_base_url="https://paper-api.alpaca.markets",
            base_reserve=1000,
            max_position_size=1000,
            confidence_threshold=70,
        )

        from quant.api import app
        yield TestClient(app)


def test_health_endpoint(client):
    """Health endpoint should return ok."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_analyze_endpoint(client):
    """Analyze endpoint should return recommendations."""
    with patch("quant.api.get_engine") as mock_get_engine:
        mock_engine = MagicMock()
        mock_engine.analyze.return_value = []
        mock_get_engine.return_value = mock_engine

        with patch("quant.api.get_data_pipeline") as mock_get_pipeline:
            mock_pipeline = MagicMock()
            mock_pipeline.build_context.return_value = MagicMock()
            mock_get_pipeline.return_value = mock_pipeline

            with patch("quant.api.get_broker") as mock_get_broker:
                mock_broker = MagicMock()
                mock_broker.get_account.return_value = MagicMock(cash=2000)
                mock_broker.get_positions.return_value = []
                mock_get_broker.return_value = mock_broker

                response = client.post("/analyze")
                assert response.status_code == 200
                assert "recommendations" in response.json()
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_api.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'quant.api'"

**Step 3: Write minimal implementation**

```python
# src/quant/api.py
"""FastAPI server for the quant engine."""

from contextlib import asynccontextmanager
from decimal import Decimal
from functools import lru_cache
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from quant.broker import AlpacaClient
from quant.config import Settings, get_settings
from quant.data import MarketDataPipeline
from quant.engine import DecisionEngine, Recommendation
from quant.risk import RiskManager
from quant.strategies import MomentumBreakoutStrategy
from quant.strategy import StrategyRegistry

# Watchlist
WATCHLIST = ["AAPL", "NVDA", "META", "MSFT", "AMZN", "GOOGL", "TSLA", "JPM", "XOM", "UNH"]


@lru_cache
def get_broker() -> AlpacaClient:
    """Get cached broker client."""
    settings = get_settings()
    return AlpacaClient(
        api_key=settings.alpaca_api_key,
        secret_key=settings.alpaca_secret_key,
        paper=True,
    )


@lru_cache
def get_data_pipeline() -> MarketDataPipeline:
    """Get cached data pipeline."""
    settings = get_settings()
    return MarketDataPipeline(
        api_key=settings.alpaca_api_key,
        secret_key=settings.alpaca_secret_key,
        watchlist=WATCHLIST,
    )


@lru_cache
def get_engine() -> DecisionEngine:
    """Get cached decision engine."""
    settings = get_settings()

    # Set up strategy registry
    registry = StrategyRegistry()
    registry.register(MomentumBreakoutStrategy())

    # Set up risk manager
    risk_manager = RiskManager(
        base_reserve=settings.base_reserve,
        max_position_size=settings.max_position_size,
        max_concurrent_positions=5,
        max_daily_loss=200,
    )

    return DecisionEngine(
        registry=registry,
        risk_manager=risk_manager,
        active_strategy="momentum_breakout",
        confidence_threshold=settings.confidence_threshold,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    yield
    # Shutdown
    get_broker.cache_clear()
    get_data_pipeline.cache_clear()
    get_engine.cache_clear()


app = FastAPI(
    title="Quant Superpowers API",
    description="Quantitative trading engine with tournament-validated strategies",
    version="0.1.0",
    lifespan=lifespan,
)


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str


class RecommendationResponse(BaseModel):
    """Single recommendation in response."""
    ticker: str
    action: str
    size: float
    confidence: float
    approved: bool
    rejection_reason: str | None
    entry_price: float
    stop_loss: float
    take_profit: float
    explanation: str


class AnalyzeResponse(BaseModel):
    """Response from analyze endpoint."""
    recommendations: list[RecommendationResponse]
    market_context: dict[str, Any]


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint."""
    return HealthResponse(status="ok", version="0.1.0")


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze():
    """Run analysis and return recommendations."""
    try:
        broker = get_broker()
        pipeline = get_data_pipeline()
        engine = get_engine()

        # Get current account state
        account = broker.get_account()
        positions = broker.get_positions()

        # Build market context
        context = pipeline.build_context(
            cash=account.cash,
            positions=positions,
        )

        # Run analysis
        recommendations = engine.analyze(context)

        return AnalyzeResponse(
            recommendations=[
                RecommendationResponse(
                    ticker=r.signal.ticker,
                    action=r.signal.action.value,
                    size=float(r.adjusted_size or r.signal.size),
                    confidence=r.signal.confidence,
                    approved=r.approved,
                    rejection_reason=r.rejection_reason,
                    entry_price=float(r.signal.entry_price),
                    stop_loss=float(r.signal.stop_loss),
                    take_profit=float(r.signal.take_profit),
                    explanation=r.signal.explanation,
                )
                for r in recommendations
            ],
            market_context={
                "cash": float(context.cash),
                "equity": float(context.total_equity),
                "position_count": len(context.positions),
                "vix": context.vix,
                "futures_signal": context.futures_signal,
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/execute/{ticker}")
async def execute_trade(ticker: str, size: float):
    """Execute a trade for a given ticker."""
    try:
        broker = get_broker()
        from quant.broker import OrderSide

        order = broker.submit_market_order(
            ticker=ticker,
            side=OrderSide.BUY,
            notional=Decimal(str(size)),
        )

        return {
            "order_id": order.order_id,
            "status": order.status,
            "ticker": order.ticker,
            "size": size,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_api.py -v`
Expected: PASSED (2 tests)

**Step 5: Commit**

```bash
git add src/quant/api.py tests/test_api.py
git commit -m "feat: add FastAPI server with analyze and execute endpoints"
```

---

## Task 11: Run All Tests and Verify

**Step 1: Run complete test suite**

Run: `pytest tests/ -v --cov=quant --cov-report=term-missing`

Expected: All tests pass with good coverage

**Step 2: Run type checking**

Run: `mypy src/quant/`

Expected: No errors (or minor ones to fix)

**Step 3: Run linting**

Run: `ruff check src/ tests/`

Expected: No errors

**Step 4: Test the API manually**

Run: `cp .env.example .env` (then edit with your Alpaca keys)

Run: `docker compose up -d`

Run: `uvicorn quant.api:app --reload`

Then in another terminal:
```bash
curl http://localhost:8000/health
curl -X POST http://localhost:8000/analyze
```

Expected: Health returns ok, analyze returns recommendations (may be empty if market is closed)

**Step 5: Final commit**

```bash
git add -A
git commit -m "chore: verify all tests pass and system is functional"
```

---

## Phase 1 Complete

At this point you have:
- Project structure with Python and TypeScript
- Configuration management
- Domain models (Signal, Position, MarketContext)
- Strategy protocol and registry
- Risk manager with capital protection
- Alpaca broker integration
- Market data pipeline with indicators
- One working strategy (momentum breakout)
- Decision engine orchestrating everything
- FastAPI server exposing endpoints

**Next: Phase 2** covers:
- TypeScript API layer for Moltbot
- Database persistence
- Additional strategies
- Tournament system

---

*Document version: 1.0*
*Created: 2026-01-28*
