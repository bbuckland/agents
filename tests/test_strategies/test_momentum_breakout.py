"""Tests for the MomentumBreakoutStrategy."""

from decimal import Decimal

import pytest

from quant.models import Action, MarketContext, Signal
from quant.strategies import MomentumBreakoutStrategy


class TestMomentumBreakoutStrategy:
    """Test suite for MomentumBreakoutStrategy."""

    @pytest.fixture
    def strategy(self) -> MomentumBreakoutStrategy:
        """Create a strategy instance for testing."""
        return MomentumBreakoutStrategy()

    @pytest.fixture
    def bullish_context(self) -> MarketContext:
        """Create a market context where all BUY conditions are met."""
        return MarketContext(
            cash=Decimal("100000"),
            positions=[],
            futures_signal=0.0,
            indicators={
                "AAPL": {
                    "price": 155.0,  # Above SMA20
                    "sma20": 150.0,
                    "volume_ratio": 1.5,  # >= 1.2
                    "rsi": 55.0,  # < 70
                    "macd_histogram": 0.5,  # > 0
                }
            },
        )

    @pytest.fixture
    def overbought_context(self) -> MarketContext:
        """Create a market context where RSI indicates overbought."""
        return MarketContext(
            cash=Decimal("100000"),
            positions=[],
            futures_signal=0.0,
            indicators={
                "AAPL": {
                    "price": 155.0,  # Above SMA20
                    "sma20": 150.0,
                    "volume_ratio": 1.5,  # >= 1.2
                    "rsi": 75.0,  # > 70 - OVERBOUGHT
                    "macd_histogram": 0.5,  # > 0
                }
            },
        )

    def test_generates_buy_signal_when_all_conditions_met(
        self, strategy: MomentumBreakoutStrategy, bullish_context: MarketContext
    ) -> None:
        """Test that a BUY signal is generated when all conditions are met."""
        signals = strategy.analyze(bullish_context)

        assert len(signals) == 1
        signal = signals[0]

        assert signal.ticker == "AAPL"
        assert signal.action == Action.BUY
        assert 0 < signal.confidence <= 100

        # Check stop loss is 3% below entry
        expected_stop_loss = Decimal("155.0") * Decimal("0.97")
        assert signal.stop_loss == expected_stop_loss

        # Check take profit is 5% above entry
        expected_take_profit = Decimal("155.0") * Decimal("1.05")
        assert signal.take_profit == expected_take_profit

    def test_skips_when_rsi_is_overbought(
        self, strategy: MomentumBreakoutStrategy, overbought_context: MarketContext
    ) -> None:
        """Test that no signal is generated when RSI > 70 (overbought)."""
        signals = strategy.analyze(overbought_context)

        assert len(signals) == 0

    def test_explain_returns_string_with_ticker_and_confidence(
        self, strategy: MomentumBreakoutStrategy
    ) -> None:
        """Test that explain() returns a readable string with ticker and confidence."""
        signal = Signal(
            ticker="AAPL",
            action=Action.BUY,
            size=Decimal("10"),
            confidence=65,
            stop_loss=Decimal("150.35"),
            take_profit=Decimal("162.75"),
            entry_price=Decimal("155.0"),
            strategy_name="momentum_breakout",
            rationale_tags=["breakout", "volume_confirmed"],
        )

        explanation = strategy.explain(signal)

        assert isinstance(explanation, str)
        assert "AAPL" in explanation
        assert "65" in explanation  # Confidence percentage
        assert len(explanation) > 0

    def test_strategy_has_correct_name_and_version(
        self, strategy: MomentumBreakoutStrategy
    ) -> None:
        """Test that strategy has the correct name and version attributes."""
        assert strategy.name == "momentum_breakout"
        assert strategy.version == "1.0"

    def test_backtest_returns_backtest_result(
        self, strategy: MomentumBreakoutStrategy
    ) -> None:
        """Test that backtest returns a BacktestResult with zero values."""
        result = strategy.backtest(historical=None)

        assert result.total_return == Decimal("0")
        assert result.max_drawdown == Decimal("0")
        assert result.total_trades == 0
