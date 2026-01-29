"""Tests for the decision engine."""

from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from quant.engine import DecisionEngine, Recommendation
from quant.models import Action, MarketContext, Signal
from quant.risk import RiskManager
from quant.strategy import StrategyRegistry


class TestDecisionEngine:
    """Tests for DecisionEngine."""

    @pytest.fixture
    def mock_strategy(self) -> MagicMock:
        """Create a mock strategy."""
        strategy = MagicMock()
        strategy.name = "test_strategy"
        strategy.version = "1.0"
        strategy.description = "Test strategy"
        return strategy

    @pytest.fixture
    def registry(self, mock_strategy: MagicMock) -> StrategyRegistry:
        """Create a registry with mock strategy."""
        registry = StrategyRegistry()
        registry.register(mock_strategy)
        return registry

    @pytest.fixture
    def risk_manager(self) -> RiskManager:
        """Create a risk manager."""
        return RiskManager(
            base_reserve=Decimal("1000"),
            max_position_size=Decimal("1000"),
            max_concurrent_positions=5,
            max_daily_loss=Decimal("200"),
        )

    @pytest.fixture
    def engine(
        self, registry: StrategyRegistry, risk_manager: RiskManager
    ) -> DecisionEngine:
        """Create a decision engine."""
        return DecisionEngine(
            registry=registry,
            risk_manager=risk_manager,
            active_strategy="test_strategy",
            confidence_threshold=70,
        )

    @pytest.fixture
    def context(self) -> MarketContext:
        """Create a market context."""
        return MarketContext(
            timestamp=datetime.now(timezone.utc),
            cash=Decimal("2000.00"),
            positions=[],
            futures_signal=0.0,
        )

    @pytest.fixture
    def high_confidence_signal(self) -> Signal:
        """Create a high confidence signal."""
        return Signal(
            ticker="AAPL",
            action=Action.BUY,
            size=Decimal("800"),
            confidence=78,
            rationale_tags=["momentum"],
            stop_loss=Decimal("177.70"),
            take_profit=Decimal("192.36"),
            entry_price=Decimal("183.20"),
            explanation="Test signal",
            strategy_name="test_strategy",
        )

    @pytest.fixture
    def low_confidence_signal(self) -> Signal:
        """Create a low confidence signal."""
        return Signal(
            ticker="AAPL",
            action=Action.BUY,
            size=Decimal("800"),
            confidence=65,
            rationale_tags=["weak"],
            stop_loss=Decimal("177.70"),
            take_profit=Decimal("192.36"),
            entry_price=Decimal("183.20"),
            explanation="Weak signal",
            strategy_name="test_strategy",
        )

    def test_analyze_returns_recommendations(
        self,
        engine: DecisionEngine,
        mock_strategy: MagicMock,
        context: MarketContext,
        high_confidence_signal: Signal,
    ) -> None:
        """Engine should return recommendations for high confidence signals."""
        mock_strategy.analyze.return_value = [high_confidence_signal]

        recommendations = engine.analyze(context)

        assert len(recommendations) == 1
        assert recommendations[0].signal.ticker == "AAPL"
        assert recommendations[0].approved is True

    def test_analyze_filters_low_confidence(
        self,
        engine: DecisionEngine,
        mock_strategy: MagicMock,
        context: MarketContext,
        low_confidence_signal: Signal,
    ) -> None:
        """Engine should filter signals below confidence threshold."""
        mock_strategy.analyze.return_value = [low_confidence_signal]

        recommendations = engine.analyze(context)

        assert len(recommendations) == 0

    def test_analyze_validates_through_risk_manager(
        self,
        engine: DecisionEngine,
        mock_strategy: MagicMock,
        high_confidence_signal: Signal,
    ) -> None:
        """Engine should validate signals through risk manager."""
        mock_strategy.analyze.return_value = [high_confidence_signal]

        # Context with only $1100 (only $100 above reserve)
        context = MarketContext(
            timestamp=datetime.now(timezone.utc),
            cash=Decimal("1100.00"),
            positions=[],
            futures_signal=0.0,
        )

        recommendations = engine.analyze(context)

        assert len(recommendations) == 1
        assert recommendations[0].approved is True
        # Size should be adjusted down to available capital
        assert recommendations[0].adjusted_size == Decimal("100.00")

    def test_set_active_strategy(
        self,
        engine: DecisionEngine,
        registry: StrategyRegistry,
    ) -> None:
        """Should change active strategy."""
        # Add another strategy
        other_strategy = MagicMock()
        other_strategy.name = "other_strategy"
        registry.register(other_strategy)

        engine.set_active_strategy("other_strategy")

        assert engine.active_strategy == "other_strategy"

    def test_set_active_strategy_unknown_raises(
        self,
        engine: DecisionEngine,
    ) -> None:
        """Should raise for unknown strategy."""
        with pytest.raises(KeyError):
            engine.set_active_strategy("nonexistent")

    def test_set_confidence_threshold(
        self,
        engine: DecisionEngine,
    ) -> None:
        """Should update confidence threshold."""
        engine.set_confidence_threshold(80)
        assert engine.confidence_threshold == 80

    def test_set_confidence_threshold_invalid_raises(
        self,
        engine: DecisionEngine,
    ) -> None:
        """Should raise for invalid threshold."""
        with pytest.raises(ValueError):
            engine.set_confidence_threshold(150)

        with pytest.raises(ValueError):
            engine.set_confidence_threshold(-10)


class TestRecommendation:
    """Tests for Recommendation dataclass."""

    def test_rejection_reason_when_approved(self) -> None:
        """Should return None when approved."""
        from quant.risk import ValidationResult

        rec = Recommendation(
            signal=MagicMock(),
            validation=ValidationResult(
                allowed=True, reason="OK", adjusted_size=Decimal("800")
            ),
            approved=True,
        )

        assert rec.rejection_reason is None

    def test_rejection_reason_when_rejected(self) -> None:
        """Should return reason when rejected."""
        from quant.risk import ValidationResult

        rec = Recommendation(
            signal=MagicMock(),
            validation=ValidationResult(
                allowed=False, reason="Insufficient capital", adjusted_size=None
            ),
            approved=False,
        )

        assert rec.rejection_reason == "Insufficient capital"
