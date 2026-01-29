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


class TestConfidenceCalculation:
    """Tests for confidence score calculation."""

    def test_rsi_score_rewards_strong_momentum(self) -> None:
        """Higher RSI (40-70 range) should give higher confidence."""
        from quant.strategies.momentum_breakout import MomentumBreakoutStrategy

        strategy = MomentumBreakoutStrategy()

        # Strong momentum (RSI 65) should score higher than weak (RSI 35)
        strong_confidence = strategy._calculate_confidence(
            price=185.0, sma20=180.0, volume_ratio=1.5, rsi=65.0, macd_histogram=1.0
        )
        weak_confidence = strategy._calculate_confidence(
            price=185.0, sma20=180.0, volume_ratio=1.5, rsi=35.0, macd_histogram=1.0
        )

        assert strong_confidence > weak_confidence, (
            f"RSI 65 ({strong_confidence}) should score higher than RSI 35 ({weak_confidence})"
        )

    def test_rsi_below_40_scores_zero(self) -> None:
        """RSI below 40 indicates weak momentum, should score zero."""
        from quant.strategies.momentum_breakout import MomentumBreakoutStrategy

        strategy = MomentumBreakoutStrategy()

        # RSI 30 is not momentum - it's oversold/weak
        confidence_rsi30 = strategy._calculate_confidence(
            price=185.0, sma20=180.0, volume_ratio=1.5, rsi=30.0, macd_histogram=1.0
        )
        confidence_rsi50 = strategy._calculate_confidence(
            price=185.0, sma20=180.0, volume_ratio=1.5, rsi=50.0, macd_histogram=1.0
        )

        assert confidence_rsi50 > confidence_rsi30

    def test_rsi_at_70_scores_maximum(self) -> None:
        """RSI at 69 (just under overbought) should score maximum RSI points."""
        from quant.strategies.momentum_breakout import MomentumBreakoutStrategy

        strategy = MomentumBreakoutStrategy()

        # RSI 69 is strong momentum without being overbought
        confidence = strategy._calculate_confidence(
            price=185.0, sma20=180.0, volume_ratio=1.5, rsi=69.0, macd_histogram=1.0
        )

        # Should be high confidence (other factors contribute too)
        assert confidence >= 50


class TestMissingDataHandling:
    """Tests for handling missing or invalid indicator data."""

    def test_skips_ticker_with_missing_price(self) -> None:
        """Should not generate signal when price is missing."""
        from decimal import Decimal
        from quant.models import MarketContext
        from quant.strategies.momentum_breakout import MomentumBreakoutStrategy

        strategy = MomentumBreakoutStrategy()
        context = MarketContext(
            cash=Decimal("2000"),
            positions=[],
            futures_signal=0.0,
            indicators={
                "AAPL": {
                    # Missing "price" key
                    "sma20": 180.0,
                    "volume_ratio": 1.5,
                    "rsi": 55.0,
                    "macd_histogram": 1.0,
                },
            },
        )

        signals = strategy.analyze(context)
        assert len(signals) == 0, "Should not generate signal with missing price"

    def test_skips_ticker_with_missing_sma20(self) -> None:
        """Should not generate signal when SMA20 is missing."""
        from decimal import Decimal
        from quant.models import MarketContext
        from quant.strategies.momentum_breakout import MomentumBreakoutStrategy

        strategy = MomentumBreakoutStrategy()
        context = MarketContext(
            cash=Decimal("2000"),
            positions=[],
            futures_signal=0.0,
            indicators={
                "AAPL": {
                    "price": 185.0,
                    # Missing "sma20" key
                    "volume_ratio": 1.5,
                    "rsi": 55.0,
                    "macd_histogram": 1.0,
                },
            },
        )

        signals = strategy.analyze(context)
        assert len(signals) == 0, "Should not generate signal with missing SMA20"

    def test_skips_ticker_with_any_missing_indicator(self) -> None:
        """Should not generate signal when any required indicator is missing."""
        from decimal import Decimal
        from quant.models import MarketContext
        from quant.strategies.momentum_breakout import MomentumBreakoutStrategy

        strategy = MomentumBreakoutStrategy()

        required_keys = ["price", "sma20", "volume_ratio", "rsi", "macd_histogram"]

        for missing_key in required_keys:
            indicators = {
                "price": 185.0,
                "sma20": 180.0,
                "volume_ratio": 1.5,
                "rsi": 55.0,
                "macd_histogram": 1.0,
            }
            del indicators[missing_key]

            context = MarketContext(
                cash=Decimal("2000"),
                positions=[],
                futures_signal=0.0,
                indicators={"AAPL": indicators},
            )

            signals = strategy.analyze(context)
            assert len(signals) == 0, f"Should skip when {missing_key} is missing"

    def test_generates_signal_when_all_indicators_present(self) -> None:
        """Should generate signal when all required indicators are present."""
        from decimal import Decimal
        from quant.models import MarketContext
        from quant.strategies.momentum_breakout import MomentumBreakoutStrategy

        strategy = MomentumBreakoutStrategy()
        context = MarketContext(
            cash=Decimal("2000"),
            positions=[],
            futures_signal=0.0,
            indicators={
                "AAPL": {
                    "price": 185.0,
                    "sma20": 180.0,
                    "volume_ratio": 1.5,
                    "rsi": 55.0,
                    "macd_histogram": 1.0,
                },
            },
        )

        signals = strategy.analyze(context)
        assert len(signals) == 1, "Should generate signal when all data present"
