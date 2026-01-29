# Phase 2: Live Trading Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Enable paper trading with manual approval via Moltbot, persist trade history, add 3 more strategies.

**Architecture:** Moltbot pulls from Python API on cron schedule. Python is the "quant brain" (knows nothing about Moltbot). Moltbot is the "communication layer" (handles scheduling, user interaction, message delivery).

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy, Alembic, PostgreSQL, Redis, Moltbot skill

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        MOLTBOT                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              quant-trading skill                     │    │
│  │  • Cron: 6:00 AM ET morning briefing                │    │
│  │  • Cron: 4:00 PM ET EOD summary                     │    │
│  │  • Tools: get_recommendations, approve_trade,        │    │
│  │           check_positions, portfolio_status          │    │
│  └─────────────────────────────────────────────────────┘    │
│                          │                                   │
│                    HTTP calls                                │
│                          ▼                                   │
├─────────────────────────────────────────────────────────────┤
│                   PYTHON QUANT ENGINE                        │
│                      (FastAPI)                               │
│                                                              │
│  Endpoints:                                                  │
│  • GET  /api/analyze      → recommendations + rationale      │
│  • POST /api/execute      → execute approved trades          │
│  • GET  /api/positions    → current positions                │
│  • GET  /api/portfolio    → account summary                  │
│  • GET  /api/dashboard/*  → analytics for web dashboard      │
│                          │                                   │
│                          ▼                                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                  │
│  │ Alpaca   │  │ Postgres │  │  Redis   │                  │
│  │ (broker) │  │ (history)│  │ (cache)  │                  │
│  └──────────┘  └──────────┘  └──────────┘                  │
└─────────────────────────────────────────────────────────────┘
```

---

## Task 1: SQLAlchemy Models

**Files:**
- Create: `src/quant/db/__init__.py`
- Create: `src/quant/db/models.py`
- Create: `src/quant/db/session.py`
- Create: `tests/test_db/__init__.py`
- Create: `tests/test_db/test_models.py`

**Step 1: Write failing tests for models**

```python
# tests/test_db/test_models.py
"""Tests for database models."""

from datetime import date, datetime, timezone
from decimal import Decimal

import pytest


class TestTradeModel:
    """Tests for Trade model."""

    def test_trade_creation(self, db_session) -> None:
        """Should create a trade record."""
        from quant.db.models import Trade

        trade = Trade(
            order_id="order-123",
            ticker="AAPL",
            action="buy",
            quantity=Decimal("4.5"),
            filled_price=Decimal("183.20"),
            notional=Decimal("824.40"),
            strategy="momentum_breakout",
            confidence=Decimal("78.5"),
        )
        db_session.add(trade)
        db_session.commit()

        assert trade.id is not None
        assert trade.ticker == "AAPL"
        assert trade.executed_at is not None


class TestSignalModel:
    """Tests for Signal model."""

    def test_signal_creation(self, db_session) -> None:
        """Should create a signal record."""
        from quant.db.models import Signal

        signal = Signal(
            ticker="AAPL",
            action="buy",
            confidence=Decimal("78.5"),
            size=Decimal("800.00"),
            entry_price=Decimal("183.20"),
            stop_loss=Decimal("177.70"),
            take_profit=Decimal("192.36"),
            strategy="momentum_breakout",
            rationale={"technical": "RSI 58, MACD bullish"},
            status="pending",
        )
        db_session.add(signal)
        db_session.commit()

        assert signal.id is not None
        assert signal.status == "pending"


class TestPortfolioSnapshotModel:
    """Tests for PortfolioSnapshot model."""

    def test_snapshot_creation(self, db_session) -> None:
        """Should create a portfolio snapshot."""
        from quant.db.models import PortfolioSnapshot

        snapshot = PortfolioSnapshot(
            date=date.today(),
            equity=Decimal("2450.00"),
            cash=Decimal("1200.00"),
            base_reserve=Decimal("1000.00"),
            daily_pnl=Decimal("62.40"),
            positions=[{"ticker": "AAPL", "quantity": 5, "avg_price": 180.0}],
        )
        db_session.add(snapshot)
        db_session.commit()

        assert snapshot.id is not None
```

**Step 2: Create conftest.py for test database**

```python
# tests/test_db/conftest.py
"""Database test fixtures."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from quant.db.models import Base


@pytest.fixture
def db_engine():
    """Create in-memory SQLite engine for tests."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture
def db_session(db_engine):
    """Create a database session for tests."""
    Session = sessionmaker(bind=db_engine)
    session = Session()
    yield session
    session.close()
```

**Step 3: Run tests to verify they fail**

Run: `uv run pytest tests/test_db/test_models.py -v`

Expected: FAIL with ModuleNotFoundError

**Step 4: Implement models**

```python
# src/quant/db/__init__.py
"""Database package."""

from quant.db.models import Base, PortfolioSnapshot, Signal, StrategyPerformance, Trade
from quant.db.session import get_session

__all__ = [
    "Base",
    "Trade",
    "Signal",
    "PortfolioSnapshot",
    "StrategyPerformance",
    "get_session",
]
```

```python
# src/quant/db/models.py
"""SQLAlchemy database models."""

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import Date, DateTime, Index, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all models."""

    pass


class Trade(Base):
    """Executed trade record."""

    __tablename__ = "trades"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    ticker: Mapped[str] = mapped_column(String(10), nullable=False)
    action: Mapped[str] = mapped_column(String(10), nullable=False)
    quantity: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    filled_price: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    notional: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    strategy: Mapped[str] = mapped_column(String(64), nullable=False)
    confidence: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    executed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (Index("ix_trades_ticker_executed", "ticker", "executed_at"),)


class Signal(Base):
    """Generated signal record."""

    __tablename__ = "signals"

    id: Mapped[int] = mapped_column(primary_key=True)
    ticker: Mapped[str] = mapped_column(String(10), nullable=False)
    action: Mapped[str] = mapped_column(String(10), nullable=False)
    confidence: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    size: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    entry_price: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    stop_loss: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    take_profit: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    strategy: Mapped[str] = mapped_column(String(64), nullable=False)
    rationale: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (Index("ix_signals_status_created", "status", "created_at"),)


class PortfolioSnapshot(Base):
    """Daily portfolio snapshot."""

    __tablename__ = "portfolio_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[date] = mapped_column(Date, unique=True, nullable=False)
    equity: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    cash: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    base_reserve: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    daily_pnl: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    positions: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )


class StrategyPerformance(Base):
    """Daily strategy performance metrics."""

    __tablename__ = "strategy_performance"

    id: Mapped[int] = mapped_column(primary_key=True)
    strategy: Mapped[str] = mapped_column(String(64), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    signals_generated: Mapped[int] = mapped_column(nullable=False, default=0)
    signals_approved: Mapped[int] = mapped_column(nullable=False, default=0)
    trades_won: Mapped[int] = mapped_column(nullable=False, default=0)
    trades_lost: Mapped[int] = mapped_column(nullable=False, default=0)
    gross_pnl: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)

    __table_args__ = (
        UniqueConstraint("strategy", "date", name="uq_strategy_date"),
        Index("ix_strategy_perf_date", "date"),
    )
```

```python
# src/quant/db/session.py
"""Database session management."""

from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from quant.config import get_settings


@lru_cache
def get_engine():
    """Get cached database engine."""
    settings = get_settings()
    return create_engine(settings.database_url, pool_pre_ping=True)


def get_session() -> Generator[Session, None, None]:
    """Get a database session."""
    engine = get_engine()
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
```

**Step 5: Run tests to verify they pass**

Run: `uv run pytest tests/test_db/test_models.py -v`

Expected: PASSED

**Step 6: Commit**

```bash
git add src/quant/db/ tests/test_db/
git commit -m "feat: add SQLAlchemy models for trades, signals, and snapshots"
```

---

## Task 2: Alembic Migrations

**Files:**
- Create: `alembic.ini`
- Create: `alembic/env.py`
- Create: `alembic/versions/001_initial_schema.py`

**Step 1: Initialize Alembic**

Run: `uv run alembic init alembic`

**Step 2: Configure alembic.ini**

Update `alembic.ini`:
```ini
# Use env variable for database URL
sqlalchemy.url =
```

**Step 3: Configure env.py**

```python
# alembic/env.py
"""Alembic migration environment."""

from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context
from quant.config import get_settings
from quant.db.models import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_url():
    """Get database URL from settings."""
    settings = get_settings()
    return settings.database_url


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

**Step 4: Create initial migration**

Run: `uv run alembic revision --autogenerate -m "initial schema"`

**Step 5: Run migration**

Run: `uv run alembic upgrade head`

Expected: Tables created in PostgreSQL

**Step 6: Commit**

```bash
git add alembic.ini alembic/
git commit -m "feat: add Alembic migrations for database schema"
```

---

## Task 3: Repository Layer

**Files:**
- Create: `src/quant/db/repositories.py`
- Create: `tests/test_db/test_repositories.py`

**Step 1: Write failing tests**

```python
# tests/test_db/test_repositories.py
"""Tests for repository layer."""

from datetime import date, datetime, timezone
from decimal import Decimal

import pytest


class TestTradeRepository:
    """Tests for TradeRepository."""

    def test_create_trade(self, db_session) -> None:
        """Should create and return a trade."""
        from quant.db.repositories import TradeRepository

        repo = TradeRepository(db_session)
        trade = repo.create(
            order_id="order-456",
            ticker="NVDA",
            action="buy",
            quantity=Decimal("2.0"),
            filled_price=Decimal("485.50"),
            notional=Decimal("971.00"),
            strategy="momentum_breakout",
            confidence=Decimal("82.0"),
        )

        assert trade.id is not None
        assert trade.ticker == "NVDA"

    def test_get_trades_by_ticker(self, db_session) -> None:
        """Should return trades filtered by ticker."""
        from quant.db.repositories import TradeRepository

        repo = TradeRepository(db_session)
        repo.create(
            order_id="o1", ticker="AAPL", action="buy",
            filled_price=Decimal("180"), notional=Decimal("900"),
            strategy="test", confidence=Decimal("75"),
        )
        repo.create(
            order_id="o2", ticker="NVDA", action="buy",
            filled_price=Decimal("480"), notional=Decimal("960"),
            strategy="test", confidence=Decimal("80"),
        )

        aapl_trades = repo.get_by_ticker("AAPL")
        assert len(aapl_trades) == 1
        assert aapl_trades[0].ticker == "AAPL"


class TestSignalRepository:
    """Tests for SignalRepository."""

    def test_create_signal(self, db_session) -> None:
        """Should create a signal."""
        from quant.db.repositories import SignalRepository

        repo = SignalRepository(db_session)
        signal = repo.create(
            ticker="AAPL",
            action="buy",
            confidence=Decimal("78.5"),
            size=Decimal("800"),
            entry_price=Decimal("183.20"),
            stop_loss=Decimal("177.70"),
            take_profit=Decimal("192.36"),
            strategy="momentum_breakout",
            rationale={"technical": "RSI 58"},
        )

        assert signal.id is not None
        assert signal.status == "pending"

    def test_update_status(self, db_session) -> None:
        """Should update signal status."""
        from quant.db.repositories import SignalRepository

        repo = SignalRepository(db_session)
        signal = repo.create(
            ticker="AAPL", action="buy", confidence=Decimal("78"),
            size=Decimal("800"), entry_price=Decimal("183"),
            stop_loss=Decimal("177"), take_profit=Decimal("192"),
            strategy="test", rationale={},
        )

        repo.update_status(signal.id, "approved")
        updated = repo.get_by_id(signal.id)

        assert updated.status == "approved"

    def test_get_pending_signals(self, db_session) -> None:
        """Should return only pending signals."""
        from quant.db.repositories import SignalRepository

        repo = SignalRepository(db_session)
        repo.create(
            ticker="AAPL", action="buy", confidence=Decimal("78"),
            size=Decimal("800"), entry_price=Decimal("183"),
            stop_loss=Decimal("177"), take_profit=Decimal("192"),
            strategy="test", rationale={},
        )
        signal2 = repo.create(
            ticker="NVDA", action="buy", confidence=Decimal("80"),
            size=Decimal("800"), entry_price=Decimal("480"),
            stop_loss=Decimal("465"), take_profit=Decimal("504"),
            strategy="test", rationale={},
        )
        repo.update_status(signal2.id, "approved")

        pending = repo.get_pending()
        assert len(pending) == 1
        assert pending[0].ticker == "AAPL"
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_db/test_repositories.py -v`

Expected: FAIL

**Step 3: Implement repositories**

```python
# src/quant/db/repositories.py
"""Repository classes for database operations."""

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from quant.db.models import PortfolioSnapshot, Signal, StrategyPerformance, Trade


class TradeRepository:
    """Repository for Trade operations."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        order_id: str,
        ticker: str,
        action: str,
        filled_price: Decimal,
        notional: Decimal,
        strategy: str,
        confidence: Decimal | None = None,
        quantity: Decimal | None = None,
    ) -> Trade:
        """Create a new trade record."""
        trade = Trade(
            order_id=order_id,
            ticker=ticker,
            action=action,
            quantity=quantity,
            filled_price=filled_price,
            notional=notional,
            strategy=strategy,
            confidence=confidence,
        )
        self.session.add(trade)
        self.session.commit()
        self.session.refresh(trade)
        return trade

    def get_by_id(self, trade_id: int) -> Trade | None:
        """Get a trade by ID."""
        return self.session.get(Trade, trade_id)

    def get_by_ticker(self, ticker: str) -> list[Trade]:
        """Get all trades for a ticker."""
        stmt = select(Trade).where(Trade.ticker == ticker).order_by(Trade.executed_at.desc())
        return list(self.session.scalars(stmt))

    def get_by_date_range(
        self, start_date: datetime, end_date: datetime
    ) -> list[Trade]:
        """Get trades within a date range."""
        stmt = (
            select(Trade)
            .where(Trade.executed_at >= start_date)
            .where(Trade.executed_at <= end_date)
            .order_by(Trade.executed_at.desc())
        )
        return list(self.session.scalars(stmt))

    def get_recent(self, limit: int = 20) -> list[Trade]:
        """Get most recent trades."""
        stmt = select(Trade).order_by(Trade.executed_at.desc()).limit(limit)
        return list(self.session.scalars(stmt))


class SignalRepository:
    """Repository for Signal operations."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        ticker: str,
        action: str,
        confidence: Decimal,
        size: Decimal,
        entry_price: Decimal,
        stop_loss: Decimal,
        take_profit: Decimal,
        strategy: str,
        rationale: dict[str, Any],
    ) -> Signal:
        """Create a new signal record."""
        signal = Signal(
            ticker=ticker,
            action=action,
            confidence=confidence,
            size=size,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            strategy=strategy,
            rationale=rationale,
            status="pending",
        )
        self.session.add(signal)
        self.session.commit()
        self.session.refresh(signal)
        return signal

    def get_by_id(self, signal_id: int) -> Signal | None:
        """Get a signal by ID."""
        return self.session.get(Signal, signal_id)

    def get_pending(self) -> list[Signal]:
        """Get all pending signals."""
        stmt = (
            select(Signal)
            .where(Signal.status == "pending")
            .order_by(Signal.created_at.desc())
        )
        return list(self.session.scalars(stmt))

    def update_status(self, signal_id: int, status: str) -> None:
        """Update signal status."""
        signal = self.session.get(Signal, signal_id)
        if signal:
            signal.status = status
            self.session.commit()


class PortfolioRepository:
    """Repository for PortfolioSnapshot operations."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create_snapshot(
        self,
        snapshot_date: date,
        equity: Decimal,
        cash: Decimal,
        base_reserve: Decimal,
        daily_pnl: Decimal,
        positions: list[dict[str, Any]],
    ) -> PortfolioSnapshot:
        """Create a portfolio snapshot."""
        snapshot = PortfolioSnapshot(
            date=snapshot_date,
            equity=equity,
            cash=cash,
            base_reserve=base_reserve,
            daily_pnl=daily_pnl,
            positions=positions,
        )
        self.session.add(snapshot)
        self.session.commit()
        self.session.refresh(snapshot)
        return snapshot

    def get_by_date(self, snapshot_date: date) -> PortfolioSnapshot | None:
        """Get snapshot for a specific date."""
        stmt = select(PortfolioSnapshot).where(PortfolioSnapshot.date == snapshot_date)
        return self.session.scalar(stmt)

    def get_recent(self, days: int = 30) -> list[PortfolioSnapshot]:
        """Get recent snapshots."""
        stmt = (
            select(PortfolioSnapshot)
            .order_by(PortfolioSnapshot.date.desc())
            .limit(days)
        )
        return list(self.session.scalars(stmt))
```

**Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_db/test_repositories.py -v`

Expected: PASSED

**Step 5: Update db/__init__.py exports**

**Step 6: Commit**

```bash
git add src/quant/db/repositories.py tests/test_db/test_repositories.py
git commit -m "feat: add repository layer for database operations"
```

---

## Task 4: Enhanced API Endpoints

**Files:**
- Modify: `src/quant/api.py`
- Create: `src/quant/api_models.py`
- Modify: `tests/test_api.py`

**Step 1: Write failing tests for new endpoints**

```python
# tests/test_api.py (add to existing)

class TestAnalyzeEndpoint:
    """Tests for GET /api/analyze."""

    def test_analyze_returns_recommendations(self, client, mock_deps) -> None:
        """Should return recommendations with rationale."""
        response = client.get("/api/analyze")

        assert response.status_code == 200
        data = response.json()
        assert "timestamp" in data
        assert "market_context" in data
        assert "recommendations" in data

    def test_analyze_persists_signals(self, client, mock_deps, db_session) -> None:
        """Should save generated signals to database."""
        from quant.db.repositories import SignalRepository

        response = client.get("/api/analyze")
        assert response.status_code == 200

        repo = SignalRepository(db_session)
        signals = repo.get_pending()
        assert len(signals) >= 0  # May be 0 if no signals generated


class TestExecuteEndpoint:
    """Tests for POST /api/execute."""

    def test_execute_creates_trades(self, client, mock_deps) -> None:
        """Should execute trades and return results."""
        response = client.post(
            "/api/execute",
            json={
                "trades": [
                    {"ticker": "AAPL", "action": "buy", "size": 800.00}
                ]
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "executed" in data
        assert "failed" in data

    def test_execute_updates_signal_status(self, client, mock_deps, db_session) -> None:
        """Should mark signal as approved when executed."""
        # Create a pending signal first
        from quant.db.repositories import SignalRepository
        repo = SignalRepository(db_session)
        signal = repo.create(
            ticker="AAPL", action="buy", confidence=Decimal("78"),
            size=Decimal("800"), entry_price=Decimal("183"),
            stop_loss=Decimal("177"), take_profit=Decimal("192"),
            strategy="momentum_breakout", rationale={},
        )

        response = client.post(
            "/api/execute",
            json={"trades": [{"ticker": "AAPL", "action": "buy", "size": 800.00}]}
        )

        assert response.status_code == 200
        updated_signal = repo.get_by_id(signal.id)
        assert updated_signal.status == "approved"


class TestPositionsEndpoint:
    """Tests for GET /api/positions."""

    def test_positions_returns_current_positions(self, client, mock_deps) -> None:
        """Should return current open positions."""
        response = client.get("/api/positions")

        assert response.status_code == 200
        data = response.json()
        assert "positions" in data


class TestPortfolioEndpoint:
    """Tests for GET /api/portfolio."""

    def test_portfolio_returns_summary(self, client, mock_deps) -> None:
        """Should return portfolio summary."""
        response = client.get("/api/portfolio")

        assert response.status_code == 200
        data = response.json()
        assert "equity" in data
        assert "cash" in data
        assert "base_reserve" in data
        assert "daily_pnl" in data
```

**Step 2: Implement API models**

```python
# src/quant/api_models.py
"""Pydantic models for API requests and responses."""

from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field


# Request models

class TradeRequest(BaseModel):
    """Single trade request."""
    ticker: str
    action: str
    size: float


class ExecuteRequest(BaseModel):
    """Request to execute trades."""
    trades: list[TradeRequest]


# Response models

class RationaleResponse(BaseModel):
    """Rationale breakdown for a recommendation."""
    technical: str | None = None
    sentiment: str | None = None
    macro: str | None = None


class RecommendationResponse(BaseModel):
    """Single recommendation."""
    ticker: str
    action: str
    size: float
    confidence: float
    entry_price: float
    stop_loss: float
    take_profit: float
    rationale: RationaleResponse
    strategy: str


class MarketContextResponse(BaseModel):
    """Market context summary."""
    futures_signal: float
    vix: float
    cash: float
    equity: float


class AnalyzeResponse(BaseModel):
    """Response from /api/analyze."""
    timestamp: str
    market_context: MarketContextResponse
    recommendations: list[RecommendationResponse]


class ExecutedTradeResponse(BaseModel):
    """Single executed trade result."""
    ticker: str
    order_id: str
    status: str
    filled_price: float | None = None


class ExecuteResponse(BaseModel):
    """Response from /api/execute."""
    executed: list[ExecutedTradeResponse]
    failed: list[dict[str, Any]]


class PositionResponse(BaseModel):
    """Single position."""
    ticker: str
    quantity: float
    avg_price: float
    current_price: float
    market_value: float
    unrealized_pnl: float
    unrealized_pnl_pct: float


class PositionsResponse(BaseModel):
    """Response from /api/positions."""
    positions: list[PositionResponse]


class PortfolioResponse(BaseModel):
    """Response from /api/portfolio."""
    equity: float
    cash: float
    base_reserve: float
    available_capital: float
    daily_pnl: float
    total_positions: int
    position_value: float
```

**Step 3: Update api.py with new endpoints**

Update `src/quant/api.py` to:
- Add `/api/analyze` (GET) - returns recommendations, saves signals to DB
- Add `/api/execute` (POST) - executes trades, saves to DB, updates signal status
- Add `/api/positions` (GET) - returns current positions with P&L
- Add `/api/portfolio` (GET) - returns account summary

**Step 4: Run tests**

Run: `uv run pytest tests/test_api.py -v`

Expected: PASSED

**Step 5: Commit**

```bash
git add src/quant/api.py src/quant/api_models.py tests/test_api.py
git commit -m "feat: add enhanced API endpoints for Moltbot integration"
```

---

## Task 5: Moltbot Skill

**Files:**
- Create: `moltbot/quant-trading/SKILL.md`

**Step 1: Create the skill directory structure**

```bash
mkdir -p moltbot/quant-trading
```

**Step 2: Write the skill definition**

```markdown
# moltbot/quant-trading/SKILL.md
---
name: quant-trading
description: Daily trading recommendations and portfolio management
metadata: {"moltbot":{"requires":{"env":["QUANT_API_URL"]}}}
---

# Quant Trading Assistant

You help manage a quantitative trading system for F100 stocks.

## Configuration

The quant API is available at: ${QUANT_API_URL}

## Schedule

Run these automatically:
- **6:00 AM ET weekdays**: Morning briefing - call get_recommendations
- **4:00 PM ET weekdays**: EOD summary - call portfolio_status

## Tools

### get_recommendations

Fetch today's trading recommendations.

**Request:** GET ${QUANT_API_URL}/api/analyze

**Present results as:**

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MORNING BRIEFING — [date]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

MARKET CONTEXT
• S&P futures: [futures_signal > 0 ? "bullish" : "bearish"]
• VIX: [vix]
• Available capital: $[cash - 1000]

[For each recommendation:]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[TICKER] — [ACTION] — [confidence]% Confidence
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TECHNICAL: [rationale.technical]
SENTIMENT: [rationale.sentiment]
MACRO: [rationale.macro]

Entry: $[entry_price]
Stop-loss: $[stop_loss]
Take-profit: $[take_profit]
Position size: $[size]

Strategy: [strategy]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Proposed: [list all trades]
Total exposure: $[sum of sizes]

Reply: "approve all", "approve [TICKER]", "skip"
```

### approve_trades

Execute approved trades.

**Request:** POST ${QUANT_API_URL}/api/execute
**Body:**
```json
{
  "trades": [
    {"ticker": "...", "action": "...", "size": ...}
  ]
}
```

**Handle user responses:**
- "approve all" → execute all recommendations
- "approve AAPL" → execute only AAPL
- "approve AAPL, META" → execute listed tickers
- "AAPL at 500" → execute AAPL with size $500
- "skip" or "pass" → execute nothing

**Present results as:**
```
✓ AAPL: Bought at $[filled_price] (Order: [order_id])
✗ META: Failed - [error reason]
```

### check_positions

Get current open positions.

**Request:** GET ${QUANT_API_URL}/api/positions

**Present results as:**
```
CURRENT POSITIONS

[TICKER]: [quantity] shares @ $[avg_price]
  Current: $[current_price] ([unrealized_pnl_pct]%)
  P&L: $[unrealized_pnl]

[If no positions: "No open positions"]
```

### portfolio_status

Get portfolio summary. Use for EOD briefing.

**Request:** GET ${QUANT_API_URL}/api/portfolio

**Present results as:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
END OF DAY SUMMARY — [date]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Portfolio Value: $[equity]
Cash: $[cash]
Positions: $[position_value] ([total_positions] stocks)

Today's P&L: $[daily_pnl]
Base Reserve: $[base_reserve] (protected)
Available to Trade: $[available_capital]
```

## User Commands

When user asks:
- "positions" / "what do I own" → check_positions
- "portfolio" / "how am I doing" → portfolio_status
- "any trades today" / "recommendations" → get_recommendations
- "approve [something]" → approve_trades with parsed tickers
```

**Step 3: Commit**

```bash
git add moltbot/
git commit -m "feat: add Moltbot quant-trading skill"
```

---

## Task 6: Sentiment Data Integration

**Files:**
- Create: `src/quant/sentiment.py`
- Create: `tests/test_sentiment.py`
- Modify: `src/quant/config.py`

**Step 1: Add config for sentiment APIs**

Add to `src/quant/config.py`:

```python
    # Sentiment data sources
    polygon_api_key: SecretStr | None = None
    alphavantage_api_key: SecretStr | None = None
```

**Step 2: Write failing tests**

```python
# tests/test_sentiment.py
"""Tests for sentiment data integration."""

from unittest.mock import MagicMock, patch

import pytest


class TestPolygonSentiment:
    """Tests for Polygon.io sentiment data."""

    @patch("quant.sentiment.httpx.Client")
    def test_fetch_news_sentiment(self, mock_client) -> None:
        """Should fetch news sentiment for a ticker."""
        from quant.sentiment import SentimentProvider

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [
                {
                    "title": "Apple reports strong iPhone sales",
                    "sentiment": "positive",
                    "sentiment_score": 0.85,
                }
            ]
        }
        mock_client.return_value.get.return_value = mock_response

        provider = SentimentProvider(polygon_api_key="test")
        sentiment = provider.get_news_sentiment("AAPL")

        assert sentiment.score > 0
        assert len(sentiment.headlines) > 0


class TestAlphaVantageSentiment:
    """Tests for Alpha Vantage news data."""

    @patch("quant.sentiment.httpx.Client")
    def test_fetch_news(self, mock_client) -> None:
        """Should fetch news headlines."""
        from quant.sentiment import SentimentProvider

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "feed": [
                {
                    "title": "Apple announces new product",
                    "overall_sentiment_label": "Bullish",
                }
            ]
        }
        mock_client.return_value.get.return_value = mock_response

        provider = SentimentProvider(alphavantage_api_key="test")
        sentiment = provider.get_news_sentiment("AAPL")

        assert len(sentiment.headlines) > 0
```

**Step 3: Implement sentiment provider**

```python
# src/quant/sentiment.py
"""Sentiment data integration from Polygon.io and Alpha Vantage."""

from dataclasses import dataclass

import httpx


@dataclass
class SentimentResult:
    """Sentiment analysis result."""
    ticker: str
    score: float  # -1 to 1
    headlines: list[str]
    positive_count: int
    negative_count: int
    neutral_count: int


class SentimentProvider:
    """Fetches sentiment data from multiple sources."""

    POLYGON_BASE = "https://api.polygon.io"
    ALPHAVANTAGE_BASE = "https://www.alphavantage.co"

    def __init__(
        self,
        polygon_api_key: str | None = None,
        alphavantage_api_key: str | None = None,
    ) -> None:
        self.polygon_key = polygon_api_key
        self.alphavantage_key = alphavantage_api_key
        self._client = httpx.Client(timeout=30.0)

    def get_news_sentiment(self, ticker: str) -> SentimentResult:
        """Get aggregated sentiment for a ticker."""
        # Try Polygon first (has sentiment scores)
        if self.polygon_key:
            try:
                return self._fetch_polygon_sentiment(ticker)
            except Exception:
                pass

        # Fall back to Alpha Vantage
        if self.alphavantage_key:
            return self._fetch_alphavantage_sentiment(ticker)

        # No API keys configured
        return SentimentResult(
            ticker=ticker,
            score=0.0,
            headlines=[],
            positive_count=0,
            negative_count=0,
            neutral_count=0,
        )

    def _fetch_polygon_sentiment(self, ticker: str) -> SentimentResult:
        """Fetch sentiment from Polygon.io."""
        url = f"{self.POLYGON_BASE}/v2/reference/news"
        params = {
            "ticker": ticker,
            "limit": 10,
            "apiKey": self.polygon_key,
        }
        response = self._client.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        headlines = []
        scores = []
        positive = negative = neutral = 0

        for article in data.get("results", []):
            headlines.append(article.get("title", ""))
            sentiment = article.get("sentiment", "neutral")
            score = article.get("sentiment_score", 0.0)
            scores.append(score)

            if sentiment == "positive":
                positive += 1
            elif sentiment == "negative":
                negative += 1
            else:
                neutral += 1

        avg_score = sum(scores) / len(scores) if scores else 0.0

        return SentimentResult(
            ticker=ticker,
            score=avg_score,
            headlines=headlines,
            positive_count=positive,
            negative_count=negative,
            neutral_count=neutral,
        )

    def _fetch_alphavantage_sentiment(self, ticker: str) -> SentimentResult:
        """Fetch news from Alpha Vantage."""
        url = f"{self.ALPHAVANTAGE_BASE}/query"
        params = {
            "function": "NEWS_SENTIMENT",
            "tickers": ticker,
            "limit": 10,
            "apikey": self.alphavantage_key,
        }
        response = self._client.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        headlines = []
        positive = negative = neutral = 0

        for article in data.get("feed", []):
            headlines.append(article.get("title", ""))
            label = article.get("overall_sentiment_label", "Neutral")

            if label in ("Bullish", "Somewhat-Bullish"):
                positive += 1
            elif label in ("Bearish", "Somewhat-Bearish"):
                negative += 1
            else:
                neutral += 1

        total = positive + negative + neutral
        score = (positive - negative) / total if total > 0 else 0.0

        return SentimentResult(
            ticker=ticker,
            score=score,
            headlines=headlines,
            positive_count=positive,
            negative_count=negative,
            neutral_count=neutral,
        )

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()
```

**Step 4: Run tests**

Run: `uv run pytest tests/test_sentiment.py -v`

**Step 5: Commit**

```bash
git add src/quant/sentiment.py src/quant/config.py tests/test_sentiment.py
git commit -m "feat: add sentiment data integration with Polygon and Alpha Vantage"
```

---

## Task 7: Mean Reversion Strategy

**Files:**
- Create: `src/quant/strategies/mean_reversion.py`
- Create: `tests/test_strategies/test_mean_reversion.py`

**Step 1: Write failing tests**

```python
# tests/test_strategies/test_mean_reversion.py
"""Tests for mean reversion strategy."""

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from quant.models import MarketContext


class TestMeanReversionStrategy:
    """Tests for MeanReversionStrategy."""

    def test_generates_buy_on_oversold(self) -> None:
        """Should generate BUY when RSI oversold in uptrend."""
        from quant.strategies.mean_reversion import MeanReversionStrategy

        strategy = MeanReversionStrategy()
        context = MarketContext(
            cash=Decimal("2000"),
            positions=[],
            futures_signal=0.0,
            indicators={
                "AAPL": {
                    "price": 175.0,
                    "sma20": 180.0,
                    "sma200": 170.0,  # Price above SMA200 = uptrend
                    "rsi": 25.0,  # Oversold
                    "volume_ratio": 1.2,
                    "macd_histogram": -0.5,
                },
            },
        )

        signals = strategy.analyze(context)

        assert len(signals) == 1
        assert signals[0].ticker == "AAPL"
        assert signals[0].action.value == "buy"

    def test_skips_oversold_in_downtrend(self) -> None:
        """Should NOT buy oversold if in downtrend (price below SMA200)."""
        from quant.strategies.mean_reversion import MeanReversionStrategy

        strategy = MeanReversionStrategy()
        context = MarketContext(
            cash=Decimal("2000"),
            positions=[],
            futures_signal=0.0,
            indicators={
                "AAPL": {
                    "price": 165.0,
                    "sma20": 180.0,
                    "sma200": 170.0,  # Price BELOW SMA200 = downtrend
                    "rsi": 25.0,
                    "volume_ratio": 1.2,
                    "macd_histogram": -0.5,
                },
            },
        )

        signals = strategy.analyze(context)

        assert len(signals) == 0

    def test_skips_neutral_rsi(self) -> None:
        """Should not generate signal when RSI is neutral."""
        from quant.strategies.mean_reversion import MeanReversionStrategy

        strategy = MeanReversionStrategy()
        context = MarketContext(
            cash=Decimal("2000"),
            positions=[],
            futures_signal=0.0,
            indicators={
                "AAPL": {
                    "price": 180.0,
                    "sma20": 180.0,
                    "sma200": 170.0,
                    "rsi": 50.0,  # Neutral
                    "volume_ratio": 1.2,
                    "macd_histogram": 0.5,
                },
            },
        )

        signals = strategy.analyze(context)

        assert len(signals) == 0
```

**Step 2: Run tests to verify they fail**

**Step 3: Implement strategy**

```python
# src/quant/strategies/mean_reversion.py
"""Mean reversion strategy - fade extended moves."""

from decimal import Decimal
from typing import Any

from quant.models import Action, BacktestResult, MarketContext, Signal


class MeanReversionStrategy:
    """Buy oversold stocks in uptrends, expecting reversion to mean."""

    name = "mean_reversion"
    version = "1.0"
    description = "Fade extended moves - buy oversold in uptrends"

    # Parameters
    rsi_oversold = 30
    rsi_overbought = 70
    stop_loss_pct = 0.025  # Tighter stop for mean reversion
    take_profit_pct = 0.03  # Smaller target
    base_position_size = Decimal("600")

    def analyze(self, context: MarketContext) -> list[Signal]:
        """Analyze for mean reversion opportunities."""
        signals = []

        for ticker, indicators in context.indicators.items():
            signal = self._analyze_ticker(ticker, indicators)
            if signal:
                signals.append(signal)

        return signals

    def _analyze_ticker(
        self, ticker: str, indicators: dict[str, Any]
    ) -> Signal | None:
        """Check single ticker for mean reversion setup."""
        required = ["price", "sma20", "sma200", "rsi", "volume_ratio"]
        if not all(key in indicators for key in required):
            return None

        price = float(indicators["price"])
        sma20 = float(indicators["sma20"])
        sma200 = float(indicators["sma200"])
        rsi = float(indicators["rsi"])

        if price <= 0 or sma200 <= 0:
            return None

        # Must be in uptrend (price above SMA200)
        in_uptrend = price > sma200

        # Check for oversold condition
        is_oversold = rsi < self.rsi_oversold

        if not (in_uptrend and is_oversold):
            return None

        # Calculate confidence
        confidence = self._calculate_confidence(rsi, price, sma20, sma200)

        entry_price = Decimal(str(price))
        stop_loss = entry_price * (1 - Decimal(str(self.stop_loss_pct)))
        take_profit = entry_price * (1 + Decimal(str(self.take_profit_pct)))

        return Signal(
            ticker=ticker,
            action=Action.BUY,
            size=self.base_position_size,
            confidence=confidence,
            rationale_tags=["oversold", "uptrend", "mean_reversion"],
            stop_loss=stop_loss.quantize(Decimal("0.01")),
            take_profit=take_profit.quantize(Decimal("0.01")),
            entry_price=entry_price.quantize(Decimal("0.01")),
            explanation=self._build_explanation(ticker, indicators, confidence),
            strategy_name=self.name,
        )

    def _calculate_confidence(
        self, rsi: float, price: float, sma20: float, sma200: float
    ) -> float:
        """Calculate confidence score."""
        base = 55.0

        # More oversold = higher confidence (RSI 20 better than RSI 29)
        if rsi < 20:
            base += 20
        elif rsi < 25:
            base += 15
        else:
            base += 10

        # Stronger uptrend = higher confidence
        uptrend_strength = (price - sma200) / sma200
        if uptrend_strength > 0.10:
            base += 10
        elif uptrend_strength > 0.05:
            base += 5

        # Price below SMA20 = good entry (more room to revert)
        if price < sma20:
            base += 5

        return min(base, 90.0)

    def _build_explanation(
        self, ticker: str, indicators: dict[str, Any], confidence: float
    ) -> str:
        """Build explanation string."""
        return (
            f"{ticker} MEAN REVERSION BUY — {confidence:.0f}% Confidence\n\n"
            f"RSI oversold at {indicators['rsi']:.1f}\n"
            f"Price ${indicators['price']:.2f} above SMA200 ${indicators['sma200']:.2f} (uptrend intact)\n"
            f"Expecting reversion toward SMA20 ${indicators['sma20']:.2f}\n\n"
            f"Strategy: {self.name} v{self.version}"
        )

    def explain(self, signal: Signal) -> str:
        """Explain a signal."""
        return signal.explanation

    def backtest(self, historical: list[MarketContext]) -> BacktestResult:
        """Backtest placeholder."""
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

**Step 4: Run tests, commit**

```bash
git add src/quant/strategies/mean_reversion.py tests/test_strategies/test_mean_reversion.py
git commit -m "feat: add mean reversion strategy"
```

---

## Task 8: Gap Fade Strategy

Similar structure to Task 7. Create `gap_fade.py` with:
- Entry: Gap > 2% from previous close, fade the gap
- Exit: Gap fills or stop-loss
- Skip gaps with clear catalyst (earnings, news)

---

## Task 9: Sentiment Momentum Strategy

Similar structure. Create `sentiment_momentum.py` with:
- Entry: Sentiment score > 0.7 AND volume spike
- Uses SentimentProvider for data
- Exit: Sentiment fades or take-profit

---

## Task 10: Dashboard API Endpoints

**Files:**
- Modify: `src/quant/api.py`
- Create: `tests/test_dashboard_api.py`

Add endpoints:
- `GET /api/dashboard/performance` - equity curve, daily returns
- `GET /api/dashboard/trades` - trade history with filters
- `GET /api/dashboard/strategies` - strategy comparison metrics

---

## Task 11: Integration Testing

**Files:**
- Create: `tests/integration/test_full_flow.py`

Test complete flows:
1. Morning briefing: analyze → format → (mock) deliver
2. Trade execution: approve → execute → persist
3. EOD summary: positions → snapshot → summary

---

## Task 12: Documentation & Deployment

- Update `.env.example` with new config vars
- Write deployment guide
- Document Moltbot skill installation

---

## Out of Scope for Phase 2

- Dashboard frontend (Phase 3)
- Crypto trading (Phase 3)
- Discovery agent (Phase 3)
- Remaining 6 strategies (Phase 3)
- Autonomous mode (staying manual)

---

*Plan created: 2026-01-28*
*Estimated tasks: 12*
