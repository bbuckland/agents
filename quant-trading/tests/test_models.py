"""Tests for quant trading domain models."""

from datetime import datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from quant_trading.models import Action, BacktestResult, MarketContext, Position, Signal


class TestAction:
    """Tests for the Action enum."""

    def test_action_values(self) -> None:
        """Test that Action enum has expected values."""
        assert Action.BUY.value == "BUY"
        assert Action.SELL.value == "SELL"
        assert Action.HOLD.value == "HOLD"

    def test_action_is_string_enum(self) -> None:
        """Test that Action can be used as a string."""
        assert Action.BUY.value == "BUY"
        # String comparison works via the value
        assert Action.BUY == "BUY"


class TestSignal:
    """Tests for the Signal model."""

    def test_signal_creation_minimal(self) -> None:
        """Test creating a signal with minimal required fields."""
        signal = Signal(
            ticker="AAPL",
            action=Action.BUY,
            size=Decimal("100"),
            confidence=75,
        )
        assert signal.ticker == "AAPL"
        assert signal.action == Action.BUY
        assert signal.size == Decimal("100")
        assert signal.confidence == 75
        assert signal.rationale_tags == []
        assert signal.stop_loss is None
        assert signal.take_profit is None
        assert signal.entry_price is None

    def test_signal_creation_full(self) -> None:
        """Test creating a signal with all fields."""
        timestamp = datetime(2024, 1, 15, 10, 30, 0)
        signal = Signal(
            ticker="TSLA",
            action=Action.SELL,
            size=Decimal("50"),
            confidence=90,
            rationale_tags=["momentum", "resistance"],
            stop_loss=Decimal("250.00"),
            take_profit=Decimal("200.00"),
            entry_price=Decimal("230.00"),
            explanation="Breaking below support level",
            strategy_name="momentum_reversal",
            timestamp=timestamp,
        )
        assert signal.ticker == "TSLA"
        assert signal.action == Action.SELL
        assert signal.rationale_tags == ["momentum", "resistance"]
        assert signal.stop_loss == Decimal("250.00")
        assert signal.take_profit == Decimal("200.00")
        assert signal.entry_price == Decimal("230.00")
        assert signal.explanation == "Breaking below support level"
        assert signal.strategy_name == "momentum_reversal"
        assert signal.timestamp == timestamp

    def test_signal_confidence_validation(self) -> None:
        """Test that confidence must be between 0 and 100."""
        with pytest.raises(ValidationError):
            Signal(
                ticker="AAPL",
                action=Action.BUY,
                size=Decimal("100"),
                confidence=101,
            )

        with pytest.raises(ValidationError):
            Signal(
                ticker="AAPL",
                action=Action.BUY,
                size=Decimal("100"),
                confidence=-1,
            )

    def test_signal_size_validation(self) -> None:
        """Test that size must be non-negative."""
        with pytest.raises(ValidationError):
            Signal(
                ticker="AAPL",
                action=Action.BUY,
                size=Decimal("-10"),
                confidence=50,
            )

    def test_risk_reward_ratio_buy_signal(self) -> None:
        """Test risk/reward ratio calculation for a buy signal."""
        signal = Signal(
            ticker="AAPL",
            action=Action.BUY,
            size=Decimal("100"),
            confidence=80,
            entry_price=Decimal("150.00"),
            stop_loss=Decimal("145.00"),
            take_profit=Decimal("165.00"),
        )
        # Risk: 150 - 145 = 5
        # Reward: 165 - 150 = 15
        # Ratio: 15 / 5 = 3
        assert signal.risk_reward_ratio == Decimal("3")

    def test_risk_reward_ratio_sell_signal(self) -> None:
        """Test risk/reward ratio calculation for a sell signal."""
        signal = Signal(
            ticker="AAPL",
            action=Action.SELL,
            size=Decimal("100"),
            confidence=80,
            entry_price=Decimal("150.00"),
            stop_loss=Decimal("155.00"),
            take_profit=Decimal("140.00"),
        )
        # Risk: |150 - 155| = 5
        # Reward: |140 - 150| = 10
        # Ratio: 10 / 5 = 2
        assert signal.risk_reward_ratio == Decimal("2")

    def test_risk_reward_ratio_missing_prices(self) -> None:
        """Test that risk/reward is None when prices are missing."""
        signal = Signal(
            ticker="AAPL",
            action=Action.BUY,
            size=Decimal("100"),
            confidence=80,
        )
        assert signal.risk_reward_ratio is None

        signal_partial = Signal(
            ticker="AAPL",
            action=Action.BUY,
            size=Decimal("100"),
            confidence=80,
            entry_price=Decimal("150.00"),
            stop_loss=Decimal("145.00"),
        )
        assert signal_partial.risk_reward_ratio is None

    def test_risk_reward_ratio_zero_risk(self) -> None:
        """Test that risk/reward is None when risk is zero."""
        signal = Signal(
            ticker="AAPL",
            action=Action.BUY,
            size=Decimal("100"),
            confidence=80,
            entry_price=Decimal("150.00"),
            stop_loss=Decimal("150.00"),
            take_profit=Decimal("160.00"),
        )
        assert signal.risk_reward_ratio is None


class TestPosition:
    """Tests for the Position model."""

    def test_position_creation(self) -> None:
        """Test creating a position."""
        position = Position(
            ticker="AAPL",
            quantity=Decimal("100"),
            avg_price=Decimal("150.00"),
            current_price=Decimal("160.00"),
        )
        assert position.ticker == "AAPL"
        assert position.quantity == Decimal("100")
        assert position.avg_price == Decimal("150.00")
        assert position.current_price == Decimal("160.00")

    def test_market_value_calculation(self) -> None:
        """Test market value computed property."""
        position = Position(
            ticker="AAPL",
            quantity=Decimal("100"),
            avg_price=Decimal("150.00"),
            current_price=Decimal("160.00"),
        )
        assert position.market_value == Decimal("16000.00")

    def test_market_value_no_current_price(self) -> None:
        """Test market value is None when current price is missing."""
        position = Position(
            ticker="AAPL",
            quantity=Decimal("100"),
            avg_price=Decimal("150.00"),
        )
        assert position.market_value is None

    def test_unrealized_pnl_profit(self) -> None:
        """Test unrealized P&L calculation for a profitable position."""
        position = Position(
            ticker="AAPL",
            quantity=Decimal("100"),
            avg_price=Decimal("150.00"),
            current_price=Decimal("160.00"),
        )
        # (160 - 150) * 100 = 1000
        assert position.unrealized_pnl == Decimal("1000.00")

    def test_unrealized_pnl_loss(self) -> None:
        """Test unrealized P&L calculation for a losing position."""
        position = Position(
            ticker="AAPL",
            quantity=Decimal("100"),
            avg_price=Decimal("150.00"),
            current_price=Decimal("140.00"),
        )
        # (140 - 150) * 100 = -1000
        assert position.unrealized_pnl == Decimal("-1000.00")

    def test_unrealized_pnl_no_current_price(self) -> None:
        """Test unrealized P&L is None when current price is missing."""
        position = Position(
            ticker="AAPL",
            quantity=Decimal("100"),
            avg_price=Decimal("150.00"),
        )
        assert position.unrealized_pnl is None

    def test_short_position(self) -> None:
        """Test calculations for a short position (negative quantity)."""
        position = Position(
            ticker="AAPL",
            quantity=Decimal("-100"),
            avg_price=Decimal("150.00"),
            current_price=Decimal("140.00"),
        )
        # Market value: -100 * 140 = -14000
        assert position.market_value == Decimal("-14000.00")
        # P&L: -100 * (140 - 150) = -100 * -10 = 1000 (profit on short)
        assert position.unrealized_pnl == Decimal("1000.00")


class TestMarketContext:
    """Tests for the MarketContext model."""

    def test_market_context_creation(self) -> None:
        """Test creating a market context."""
        context = MarketContext(
            cash=Decimal("10000.00"),
            futures_signal=0.5,
            vix=18.5,
        )
        assert context.cash == Decimal("10000.00")
        assert context.futures_signal == 0.5
        assert context.vix == 18.5
        assert context.positions == []

    def test_total_equity_cash_only(self) -> None:
        """Test total equity with only cash."""
        context = MarketContext(
            cash=Decimal("10000.00"),
            futures_signal=0.0,
        )
        assert context.total_equity == Decimal("10000.00")

    def test_total_equity_with_positions(self) -> None:
        """Test total equity with cash and positions."""
        positions = [
            Position(
                ticker="AAPL",
                quantity=Decimal("100"),
                avg_price=Decimal("150.00"),
                current_price=Decimal("160.00"),
            ),
            Position(
                ticker="GOOGL",
                quantity=Decimal("50"),
                avg_price=Decimal("100.00"),
                current_price=Decimal("110.00"),
            ),
        ]
        context = MarketContext(
            cash=Decimal("5000.00"),
            positions=positions,
            futures_signal=0.0,
        )
        # Cash: 5000
        # AAPL: 100 * 160 = 16000
        # GOOGL: 50 * 110 = 5500
        # Total: 5000 + 16000 + 5500 = 26500
        assert context.total_equity == Decimal("26500.00")

    def test_total_equity_with_missing_current_price(self) -> None:
        """Test total equity ignores positions without current price."""
        positions = [
            Position(
                ticker="AAPL",
                quantity=Decimal("100"),
                avg_price=Decimal("150.00"),
                current_price=Decimal("160.00"),
            ),
            Position(
                ticker="GOOGL",
                quantity=Decimal("50"),
                avg_price=Decimal("100.00"),
                # No current price
            ),
        ]
        context = MarketContext(
            cash=Decimal("5000.00"),
            positions=positions,
            futures_signal=0.0,
        )
        # Cash: 5000
        # AAPL: 100 * 160 = 16000
        # GOOGL: not counted
        # Total: 5000 + 16000 = 21000
        assert context.total_equity == Decimal("21000.00")

    def test_futures_signal_validation(self) -> None:
        """Test that futures signal must be between -1 and 1."""
        with pytest.raises(ValidationError):
            MarketContext(
                cash=Decimal("10000.00"),
                futures_signal=1.5,
            )

        with pytest.raises(ValidationError):
            MarketContext(
                cash=Decimal("10000.00"),
                futures_signal=-1.5,
            )


class TestBacktestResult:
    """Tests for the BacktestResult model."""

    def test_backtest_result_creation(self) -> None:
        """Test creating a backtest result."""
        result = BacktestResult(
            total_return=Decimal("0.15"),
            total_trades=100,
            winning_trades=60,
            losing_trades=40,
            gross_profit=Decimal("5000.00"),
            gross_loss=Decimal("3000.00"),
            max_drawdown=Decimal("0.10"),
            sharpe_ratio=1.5,
        )
        assert result.total_return == Decimal("0.15")
        assert result.total_trades == 100
        assert result.winning_trades == 60
        assert result.losing_trades == 40

    def test_win_rate_calculation(self) -> None:
        """Test win rate computed property."""
        result = BacktestResult(
            total_return=Decimal("0.15"),
            total_trades=100,
            winning_trades=60,
            losing_trades=40,
            gross_profit=Decimal("5000.00"),
            gross_loss=Decimal("3000.00"),
            max_drawdown=Decimal("0.10"),
        )
        assert result.win_rate == 60.0

    def test_win_rate_no_trades(self) -> None:
        """Test win rate is None when there are no trades."""
        result = BacktestResult(
            total_return=Decimal("0.00"),
            total_trades=0,
            winning_trades=0,
            losing_trades=0,
            gross_profit=Decimal("0"),
            gross_loss=Decimal("0"),
            max_drawdown=Decimal("0.00"),
        )
        assert result.win_rate is None

    def test_profit_factor_calculation(self) -> None:
        """Test profit factor computed property."""
        result = BacktestResult(
            total_return=Decimal("0.15"),
            total_trades=100,
            winning_trades=60,
            losing_trades=40,
            gross_profit=Decimal("6000.00"),
            gross_loss=Decimal("3000.00"),
            max_drawdown=Decimal("0.10"),
        )
        # 6000 / 3000 = 2.0
        assert result.profit_factor == 2.0

    def test_profit_factor_no_losses(self) -> None:
        """Test profit factor is None when there are no losses."""
        result = BacktestResult(
            total_return=Decimal("0.15"),
            total_trades=10,
            winning_trades=10,
            losing_trades=0,
            gross_profit=Decimal("5000.00"),
            gross_loss=Decimal("0"),
            max_drawdown=Decimal("0.00"),
        )
        assert result.profit_factor is None

    def test_trades_list(self) -> None:
        """Test that trades can store trade records."""
        trades = [
            {"ticker": "AAPL", "action": "BUY", "pnl": 100.0},
            {"ticker": "GOOGL", "action": "SELL", "pnl": -50.0},
        ]
        result = BacktestResult(
            total_return=Decimal("0.05"),
            total_trades=2,
            winning_trades=1,
            losing_trades=1,
            gross_profit=Decimal("100.00"),
            gross_loss=Decimal("50.00"),
            max_drawdown=Decimal("0.02"),
            trades=trades,
        )
        assert len(result.trades) == 2
        assert result.trades[0]["ticker"] == "AAPL"
