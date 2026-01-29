"""Tests for the strategy protocol and registry."""

import threading
import time
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from quant.models import Action, BacktestResult, MarketContext, Signal
from quant.strategy import Strategy, StrategyRegistry


class MockStrategy:
    """A mock strategy that implements the Strategy protocol."""

    def __init__(
        self,
        name: str = "mock_strategy",
        version: str = "1.0.0",
        description: str = "A mock strategy for testing",
    ) -> None:
        self._name = name
        self._version = version
        self._description = description

    @property
    def name(self) -> str:
        return self._name

    @property
    def version(self) -> str:
        return self._version

    @property
    def description(self) -> str:
        return self._description

    def analyze(self, context: MarketContext) -> list[Signal]:
        return [
            Signal(
                ticker="AAPL",
                action=Action.BUY,
                size=Decimal("100"),
                confidence=85,
            )
        ]

    def explain(self, signal: Signal) -> str:
        return f"Signal for {signal.ticker}: {signal.action.value} with {signal.confidence}% confidence"

    def backtest(self, historical: list[MarketContext]) -> BacktestResult:
        return BacktestResult(
            total_return=Decimal("0.15"),
            max_drawdown=Decimal("0.10"),
            total_trades=len(historical),
            winning_trades=6,
            losing_trades=4,
            gross_profit=Decimal("1500"),
            gross_loss=Decimal("500"),
            sharpe_ratio=1.5,
        )


class TestStrategyProtocol:
    """Tests for the Strategy protocol."""

    def test_mock_strategy_is_strategy(self) -> None:
        """A class implementing the protocol is recognized as Strategy."""
        strategy = MockStrategy()
        assert isinstance(strategy, Strategy)

    def test_strategy_attributes(self) -> None:
        """Strategy has required attributes."""
        strategy = MockStrategy(
            name="test_strat",
            version="2.0.0",
            description="Test description",
        )
        assert strategy.name == "test_strat"
        assert strategy.version == "2.0.0"
        assert strategy.description == "Test description"

    def test_strategy_analyze(self) -> None:
        """Strategy can analyze market context."""
        strategy = MockStrategy()
        context = MarketContext(
            cash=Decimal("10000"),
            positions=[],
            futures_signal=0.0,
        )
        signals = strategy.analyze(context)
        assert len(signals) == 1
        assert signals[0].ticker == "AAPL"
        assert signals[0].action == Action.BUY

    def test_strategy_explain(self) -> None:
        """Strategy can explain signals."""
        strategy = MockStrategy()
        signal = Signal(
            ticker="AAPL",
            action=Action.BUY,
            size=Decimal("100"),
            confidence=85,
        )
        explanation = strategy.explain(signal)
        assert "AAPL" in explanation
        assert "BUY" in explanation

    def test_strategy_backtest(self) -> None:
        """Strategy can backtest historical data."""
        strategy = MockStrategy()
        historical = [
            MarketContext(
                cash=Decimal("10000"),
                positions=[],
                futures_signal=0.0,
            )
            for _ in range(10)
        ]
        result = strategy.backtest(historical)
        assert result.total_return == Decimal("0.15")
        assert result.total_trades == 10


class TestStrategyRegistry:
    """Tests for the StrategyRegistry class."""

    def test_register_and_get_strategy(self) -> None:
        """Registry can add and retrieve strategies."""
        registry = StrategyRegistry()
        strategy = MockStrategy(name="my_strategy")

        registry.register(strategy)
        retrieved = registry.get("my_strategy")

        assert retrieved is strategy
        assert retrieved.name == "my_strategy"

    def test_get_unknown_strategy_raises_keyerror(self) -> None:
        """Registry raises KeyError for unknown strategies."""
        registry = StrategyRegistry()

        with pytest.raises(KeyError, match="Strategy 'nonexistent' not found"):
            registry.get("nonexistent")

    def test_list_strategies(self) -> None:
        """Registry can list all registered strategy names."""
        registry = StrategyRegistry()
        registry.register(MockStrategy(name="strategy_a"))
        registry.register(MockStrategy(name="strategy_b"))

        names = registry.list_strategies()

        assert "strategy_a" in names
        assert "strategy_b" in names
        assert len(names) == 2

    def test_all_strategies(self) -> None:
        """Registry can return all registered strategies."""
        registry = StrategyRegistry()
        strategy_a = MockStrategy(name="strategy_a")
        strategy_b = MockStrategy(name="strategy_b")

        registry.register(strategy_a)
        registry.register(strategy_b)

        all_strategies = registry.all()

        assert len(all_strategies) == 2
        assert strategy_a in all_strategies
        assert strategy_b in all_strategies

    def test_register_overwrites_existing(self) -> None:
        """Registering a strategy with the same name overwrites the previous one."""
        registry = StrategyRegistry()
        strategy_v1 = MockStrategy(name="my_strategy", version="1.0.0")
        strategy_v2 = MockStrategy(name="my_strategy", version="2.0.0")

        registry.register(strategy_v1)
        registry.register(strategy_v2)

        retrieved = registry.get("my_strategy")
        assert retrieved.version == "2.0.0"

    def test_empty_registry(self) -> None:
        """Empty registry returns empty lists."""
        registry = StrategyRegistry()

        assert registry.list_strategies() == []
        assert registry.all() == []


class TestRegistryThreadSafety:
    """Tests for registry thread safety."""

    def test_concurrent_registration_is_safe(self) -> None:
        """Registry should handle concurrent registrations safely."""
        from quant.strategy import StrategyRegistry

        registry = StrategyRegistry()
        errors: list[Exception] = []

        def register_strategy(name: str) -> None:
            try:
                for i in range(100):
                    strategy = MagicMock()
                    strategy.name = f"{name}_{i}"
                    registry.register(strategy)
            except Exception as e:
                errors.append(e)

        threads = [
            threading.Thread(target=register_strategy, args=(f"thread_{i}",))
            for i in range(10)
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0, f"Errors during concurrent registration: {errors}"
        # Should have registered 10 threads * 100 strategies = 1000 strategies
        assert len(registry.list_strategies()) == 1000

    def test_concurrent_read_write_is_safe(self) -> None:
        """Registry should handle concurrent reads and writes safely."""
        from quant.strategy import StrategyRegistry

        registry = StrategyRegistry()
        errors: list[Exception] = []

        # Pre-populate with some strategies
        for i in range(10):
            strategy = MagicMock()
            strategy.name = f"initial_{i}"
            registry.register(strategy)

        def writer() -> None:
            try:
                for i in range(50):
                    strategy = MagicMock()
                    strategy.name = f"new_{i}"
                    registry.register(strategy)
                    time.sleep(0.001)
            except Exception as e:
                errors.append(e)

        def reader() -> None:
            try:
                for _ in range(100):
                    _ = registry.list_strategies()
                    _ = registry.all()
                    time.sleep(0.001)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=writer) for _ in range(3)]
        threads += [threading.Thread(target=reader) for _ in range(5)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0, f"Errors during concurrent access: {errors}"
