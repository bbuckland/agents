"""Tests for risk management."""

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from quant_trading.models import Action, MarketContext, Position, Signal
from quant_trading.risk import RiskManager, ValidationResult


class TestRiskManagerValidation:
    """Tests for RiskManager.validate_signal."""

    def test_allows_trade_with_sufficient_capital(self) -> None:
        """Should allow trade when capital is available above reserve."""
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
            futures_signal=0.0,
        )

        signal = Signal(
            ticker="AAPL",
            action=Action.BUY,
            size=Decimal("800.00"),
            confidence=78,
            rationale_tags=["momentum"],
            stop_loss=Decimal("177.70"),
            take_profit=Decimal("192.36"),
            entry_price=Decimal("183.20"),
            explanation="Test signal",
            strategy_name="test",
        )

        result = manager.validate_signal(signal, context)

        assert result.allowed is True
        assert result.adjusted_size == Decimal("800.00")

    def test_blocks_trade_that_would_dip_into_reserve(self) -> None:
        """Should block trade that would reduce cash below base reserve."""
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
            futures_signal=0.0,
        )

        signal = Signal(
            ticker="AAPL",
            action=Action.BUY,
            size=Decimal("800.00"),
            confidence=78,
            rationale_tags=["momentum"],
            stop_loss=Decimal("177.70"),
            take_profit=Decimal("192.36"),
            entry_price=Decimal("183.20"),
            explanation="Test signal",
            strategy_name="test",
        )

        result = manager.validate_signal(signal, context)

        # Should be allowed but adjusted to available capital
        assert result.allowed is True
        assert result.adjusted_size == Decimal("100.00")

    def test_blocks_trade_when_at_reserve(self) -> None:
        """Should block trade when cash equals reserve."""
        manager = RiskManager(
            base_reserve=1000,
            max_position_size=1000,
            max_concurrent_positions=5,
            max_daily_loss=200,
        )

        context = MarketContext(
            timestamp=datetime.now(timezone.utc),
            cash=Decimal("1000.00"),  # Exactly at reserve
            positions=[],
            futures_signal=0.0,
        )

        signal = Signal(
            ticker="AAPL",
            action=Action.BUY,
            size=Decimal("100.00"),
            confidence=78,
            rationale_tags=["momentum"],
            stop_loss=Decimal("177.70"),
            take_profit=Decimal("192.36"),
            entry_price=Decimal("183.20"),
            explanation="Test signal",
            strategy_name="test",
        )

        result = manager.validate_signal(signal, context)

        assert result.allowed is False
        assert "reserve" in result.reason.lower()

    def test_caps_position_size_to_max_allowed(self) -> None:
        """Should reduce position size to max_position_size."""
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
            futures_signal=0.0,
        )

        signal = Signal(
            ticker="AAPL",
            action=Action.BUY,
            size=Decimal("800.00"),  # Requested $800
            confidence=78,
            rationale_tags=["momentum"],
            stop_loss=Decimal("177.70"),
            take_profit=Decimal("192.36"),
            entry_price=Decimal("183.20"),
            explanation="Test signal",
            strategy_name="test",
        )

        result = manager.validate_signal(signal, context)

        assert result.allowed is True
        assert result.adjusted_size == Decimal("500.00")

    def test_blocks_at_max_concurrent_positions(self) -> None:
        """Should block new positions when at maximum."""
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
            futures_signal=0.0,
        )

        signal = Signal(
            ticker="META",  # New ticker, not in positions
            action=Action.BUY,
            size=Decimal("800.00"),
            confidence=78,
            rationale_tags=["momentum"],
            stop_loss=Decimal("300.00"),
            take_profit=Decimal("350.00"),
            entry_price=Decimal("320.00"),
            explanation="Test signal",
            strategy_name="test",
        )

        result = manager.validate_signal(signal, context)

        assert result.allowed is False
        assert "position" in result.reason.lower()

    def test_allows_adding_to_existing_position_at_max(self) -> None:
        """Should allow adding to existing position even at max concurrent."""
        manager = RiskManager(
            base_reserve=1000,
            max_position_size=1000,
            max_concurrent_positions=2,
            max_daily_loss=200,
        )

        context = MarketContext(
            timestamp=datetime.now(timezone.utc),
            cash=Decimal("5000.00"),
            positions=[
                Position(ticker="AAPL", quantity=Decimal("5"), avg_price=Decimal("180")),
                Position(ticker="NVDA", quantity=Decimal("2"), avg_price=Decimal("500")),
            ],
            futures_signal=0.0,
        )

        signal = Signal(
            ticker="AAPL",  # Existing position
            action=Action.BUY,
            size=Decimal("800.00"),
            confidence=78,
            rationale_tags=["momentum"],
            stop_loss=Decimal("177.70"),
            take_profit=Decimal("192.36"),
            entry_price=Decimal("183.20"),
            explanation="Test signal",
            strategy_name="test",
        )

        result = manager.validate_signal(signal, context)

        assert result.allowed is True

    def test_blocks_when_daily_loss_exceeded(self) -> None:
        """Should block all trades when daily loss limit is exceeded."""
        manager = RiskManager(
            base_reserve=1000,
            max_position_size=1000,
            max_concurrent_positions=5,
            max_daily_loss=200,
        )

        # Record a loss exceeding the limit
        manager.record_pnl(Decimal("-250"))

        context = MarketContext(
            timestamp=datetime.now(timezone.utc),
            cash=Decimal("5000.00"),
            positions=[],
            futures_signal=0.0,
        )

        signal = Signal(
            ticker="AAPL",
            action=Action.BUY,
            size=Decimal("500.00"),
            confidence=90,
            rationale_tags=["momentum"],
            stop_loss=Decimal("177.70"),
            take_profit=Decimal("192.36"),
            entry_price=Decimal("183.20"),
            explanation="Test signal",
            strategy_name="test",
        )

        result = manager.validate_signal(signal, context)

        assert result.allowed is False
        assert "daily loss" in result.reason.lower()


class TestRiskManagerDailyPnL:
    """Tests for daily P&L tracking."""

    def test_record_pnl_accumulates(self) -> None:
        """Should accumulate P&L recordings."""
        manager = RiskManager(
            base_reserve=1000,
            max_position_size=1000,
            max_concurrent_positions=5,
            max_daily_loss=200,
        )

        manager.record_pnl(Decimal("50"))
        manager.record_pnl(Decimal("-30"))
        manager.record_pnl(Decimal("20"))

        assert manager.daily_pnl == Decimal("40")

    def test_reset_daily_clears_pnl(self) -> None:
        """Should reset daily P&L to zero."""
        manager = RiskManager(
            base_reserve=1000,
            max_position_size=1000,
            max_concurrent_positions=5,
            max_daily_loss=200,
        )

        manager.record_pnl(Decimal("-100"))
        assert manager.daily_pnl == Decimal("-100")

        manager.reset_daily()
        assert manager.daily_pnl == Decimal("0")


class TestRiskManagerCanTrade:
    """Tests for can_trade quick check."""

    def test_can_trade_with_available_capital(self) -> None:
        """Should return True when trading is allowed."""
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
            futures_signal=0.0,
        )

        assert manager.can_trade(context) is True

    def test_cannot_trade_at_reserve(self) -> None:
        """Should return False when at base reserve."""
        manager = RiskManager(
            base_reserve=1000,
            max_position_size=1000,
            max_concurrent_positions=5,
            max_daily_loss=200,
        )

        context = MarketContext(
            timestamp=datetime.now(timezone.utc),
            cash=Decimal("1000.00"),
            positions=[],
            futures_signal=0.0,
        )

        assert manager.can_trade(context) is False

    def test_cannot_trade_after_daily_loss(self) -> None:
        """Should return False after daily loss limit hit."""
        manager = RiskManager(
            base_reserve=1000,
            max_position_size=1000,
            max_concurrent_positions=5,
            max_daily_loss=200,
        )

        manager.record_pnl(Decimal("-200"))

        context = MarketContext(
            timestamp=datetime.now(timezone.utc),
            cash=Decimal("5000.00"),
            positions=[],
            futures_signal=0.0,
        )

        assert manager.can_trade(context) is False
