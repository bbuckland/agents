# Fix Critical Issues Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix all critical issues identified by code review agents before paper trading.

**Architecture:** TDD approach - write failing tests first, then fix the code. Each fix is isolated to minimize risk. Prioritized by "could lose money" > "could crash" > "could leak secrets".

**Tech Stack:** Python 3.12, Pydantic v2, pytest, threading

---

## Task 1: Fix RSI Score Inversion (MOST CRITICAL)

The RSI confidence calculation is backwards - it rewards weak momentum (RSI 30) and penalizes strong momentum (RSI 65). This makes the entire strategy wrong.

**Files:**
- Modify: `src/quant/strategies/momentum_breakout.py:108-109`
- Modify: `tests/test_strategies/test_momentum_breakout.py`

**Step 1: Write failing test for correct RSI scoring**

Add to `tests/test_strategies/test_momentum_breakout.py`:

```python
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
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_strategies/test_momentum_breakout.py::TestConfidenceCalculation -v`

Expected: FAIL with "RSI 65 (X) should score higher than RSI 35 (Y)" where X < Y

**Step 3: Fix the RSI calculation**

In `src/quant/strategies/momentum_breakout.py`, replace lines 108-109:

```python
        # RSI room to run (0-25) - further from 70, better score
        rsi_score = (70 - rsi) / 70 * 25 if rsi < 70 else 0
```

With:

```python
        # RSI momentum strength (0-25)
        # RSI 40-70 indicates healthy momentum (not oversold, not overbought)
        # Higher RSI = stronger momentum = higher score
        if 40 <= rsi < 70:
            rsi_score = ((rsi - 40) / 30) * 25  # 0 at RSI 40, 25 at RSI 70
        else:
            rsi_score = 0  # Below 40 is weak/oversold, above 70 is overbought
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_strategies/test_momentum_breakout.py::TestConfidenceCalculation -v`

Expected: PASSED (3 tests)

**Step 5: Run all strategy tests to verify no regression**

Run: `uv run pytest tests/test_strategies/ -v`

Expected: All tests pass

**Step 6: Commit**

```bash
git add src/quant/strategies/momentum_breakout.py tests/test_strategies/test_momentum_breakout.py
git commit -m "fix: correct RSI score calculation to reward strong momentum

Previously RSI 30 scored higher than RSI 65, which is backwards for a
momentum strategy. Now RSI 40-70 range is rewarded, with higher RSI
giving higher confidence scores."
```

---

## Task 2: Fix Bad Data Defaults (Garbage In = Bad Trades)

Strategy generates signals when indicators are missing (defaults to 0.0), causing false breakouts.

**Files:**
- Modify: `src/quant/strategies/momentum_breakout.py:33-47`
- Modify: `tests/test_strategies/test_momentum_breakout.py`

**Step 1: Write failing test for missing data handling**

Add to `tests/test_strategies/test_momentum_breakout.py`:

```python
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
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_strategies/test_momentum_breakout.py::TestMissingDataHandling -v`

Expected: FAIL - signals generated even with missing data

**Step 3: Add indicator validation**

In `src/quant/strategies/momentum_breakout.py`, replace lines 33-47:

```python
        for ticker, indicators in context.indicators.items():
            # Extract indicator values
            price = float(indicators.get("price", 0.0))
            sma20 = float(indicators.get("sma20", 0.0))
            volume_ratio = float(indicators.get("volume_ratio", 0.0))
            rsi = float(indicators.get("rsi", 50.0))
            macd_histogram = float(indicators.get("macd_histogram", 0.0))

            # Check all conditions for a BUY signal
            breakout = price > sma20
            volume_confirms = volume_ratio >= 1.2
            not_overbought = rsi < 70
            bullish_momentum = macd_histogram > 0
```

With:

```python
        for ticker, indicators in context.indicators.items():
            # Validate all required indicators are present
            required_keys = ["price", "sma20", "volume_ratio", "rsi", "macd_histogram"]
            if not all(key in indicators for key in required_keys):
                continue  # Skip tickers with missing data

            # Extract indicator values (safe now that we've validated)
            price = float(indicators["price"])
            sma20 = float(indicators["sma20"])
            volume_ratio = float(indicators["volume_ratio"])
            rsi = float(indicators["rsi"])
            macd_histogram = float(indicators["macd_histogram"])

            # Additional validation: skip if values are invalid
            if price <= 0 or sma20 <= 0:
                continue

            # Check all conditions for a BUY signal
            breakout = price > sma20
            volume_confirms = volume_ratio >= 1.2
            not_overbought = rsi < 70
            bullish_momentum = macd_histogram > 0
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_strategies/test_momentum_breakout.py::TestMissingDataHandling -v`

Expected: PASSED (4 tests)

**Step 5: Run all tests**

Run: `uv run pytest tests/ -v`

Expected: All tests pass

**Step 6: Commit**

```bash
git add src/quant/strategies/momentum_breakout.py tests/test_strategies/test_momentum_breakout.py
git commit -m "fix: validate indicators exist before generating signals

Previously missing indicators defaulted to 0.0, causing false breakout
signals when price > 0 and sma20 was missing (defaulting to 0).
Now we skip tickers that are missing any required indicator."
```

---

## Task 3: Add Order Validation (Prevent Bad Orders)

Broker client accepts negative quantities which could execute reversed orders.

**Files:**
- Modify: `src/quant/broker.py:90-114`
- Modify: `tests/test_broker.py`

**Step 1: Write failing tests for order validation**

Add to `tests/test_broker.py`:

```python
class TestOrderValidation:
    """Tests for order input validation."""

    @patch("quant.broker.TradingClient")
    def test_rejects_negative_notional(self, mock_trading_client: MagicMock) -> None:
        """Should reject orders with negative notional amount."""
        from quant.broker import AlpacaClient, OrderSide

        client = AlpacaClient(api_key="test", secret_key="test", paper=True)

        with pytest.raises(ValueError, match="positive"):
            client.submit_market_order(
                ticker="AAPL",
                side=OrderSide.BUY,
                notional=Decimal("-100.00"),
            )

    @patch("quant.broker.TradingClient")
    def test_rejects_zero_notional(self, mock_trading_client: MagicMock) -> None:
        """Should reject orders with zero notional amount."""
        from quant.broker import AlpacaClient, OrderSide

        client = AlpacaClient(api_key="test", secret_key="test", paper=True)

        with pytest.raises(ValueError, match="positive"):
            client.submit_market_order(
                ticker="AAPL",
                side=OrderSide.BUY,
                notional=Decimal("0"),
            )

    @patch("quant.broker.TradingClient")
    def test_rejects_negative_quantity(self, mock_trading_client: MagicMock) -> None:
        """Should reject orders with negative quantity."""
        from quant.broker import AlpacaClient, OrderSide

        client = AlpacaClient(api_key="test", secret_key="test", paper=True)

        with pytest.raises(ValueError, match="positive"):
            client.submit_market_order(
                ticker="AAPL",
                side=OrderSide.BUY,
                quantity=Decimal("-5"),
            )

    @patch("quant.broker.TradingClient")
    def test_rejects_zero_quantity(self, mock_trading_client: MagicMock) -> None:
        """Should reject orders with zero quantity."""
        from quant.broker import AlpacaClient, OrderSide

        client = AlpacaClient(api_key="test", secret_key="test", paper=True)

        with pytest.raises(ValueError, match="positive"):
            client.submit_market_order(
                ticker="AAPL",
                side=OrderSide.BUY,
                quantity=Decimal("0"),
            )

    @patch("quant.broker.TradingClient")
    def test_rejects_empty_ticker(self, mock_trading_client: MagicMock) -> None:
        """Should reject orders with empty ticker."""
        from quant.broker import AlpacaClient, OrderSide

        client = AlpacaClient(api_key="test", secret_key="test", paper=True)

        with pytest.raises(ValueError, match="ticker"):
            client.submit_market_order(
                ticker="",
                side=OrderSide.BUY,
                notional=Decimal("100.00"),
            )
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_broker.py::TestOrderValidation -v`

Expected: FAIL - no ValueError raised

**Step 3: Add validation to submit_market_order**

In `src/quant/broker.py`, add validation after line 114 (after the existing checks):

Replace the beginning of `submit_market_order` (lines 90-114):

```python
    def submit_market_order(
        self,
        ticker: str,
        side: OrderSide,
        notional: Decimal | None = None,
        quantity: Decimal | None = None,
    ) -> OrderResult:
        """Submit a market order.

        Args:
            ticker: The stock ticker symbol.
            side: Order side (BUY or SELL).
            notional: Dollar amount to trade (mutually exclusive with quantity).
            quantity: Number of shares to trade (mutually exclusive with notional).

        Returns:
            OrderResult with order details.

        Raises:
            ValueError: If neither or both notional and quantity are provided.
        """
        if notional is None and quantity is None:
            raise ValueError("Either notional or quantity must be provided")
        if notional is not None and quantity is not None:
            raise ValueError("Cannot specify both notional and quantity")
```

With:

```python
    def submit_market_order(
        self,
        ticker: str,
        side: OrderSide,
        notional: Decimal | None = None,
        quantity: Decimal | None = None,
    ) -> OrderResult:
        """Submit a market order.

        Args:
            ticker: The stock ticker symbol.
            side: Order side (BUY or SELL).
            notional: Dollar amount to trade (mutually exclusive with quantity).
            quantity: Number of shares to trade (mutually exclusive with notional).

        Returns:
            OrderResult with order details.

        Raises:
            ValueError: If inputs are invalid.
        """
        # Validate ticker
        if not ticker or not ticker.strip():
            raise ValueError("ticker must be a non-empty string")

        # Validate amount specification
        if notional is None and quantity is None:
            raise ValueError("Either notional or quantity must be provided")
        if notional is not None and quantity is not None:
            raise ValueError("Cannot specify both notional and quantity")

        # Validate notional is positive
        if notional is not None and notional <= 0:
            raise ValueError("notional must be positive")

        # Validate quantity is positive
        if quantity is not None and quantity <= 0:
            raise ValueError("quantity must be positive")
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_broker.py::TestOrderValidation -v`

Expected: PASSED (5 tests)

**Step 5: Run all broker tests**

Run: `uv run pytest tests/test_broker.py -v`

Expected: All tests pass

**Step 6: Commit**

```bash
git add src/quant/broker.py tests/test_broker.py
git commit -m "fix: validate order inputs to prevent bad orders

Add validation for:
- Negative/zero notional amounts
- Negative/zero quantities
- Empty ticker symbols

This prevents accidentally executing reversed or invalid orders."
```

---

## Task 4: Add Broker Error Handling (Prevent Crashes)

All broker API calls can throw exceptions that crash the system.

**Files:**
- Create: `src/quant/exceptions.py`
- Modify: `src/quant/broker.py`
- Modify: `tests/test_broker.py`

**Step 1: Create custom exception class**

Create `src/quant/exceptions.py`:

```python
"""Custom exceptions for the quant trading system."""


class QuantError(Exception):
    """Base exception for quant system errors."""

    pass


class BrokerError(QuantError):
    """Exception raised when broker operations fail."""

    def __init__(self, message: str, original_error: Exception | None = None) -> None:
        super().__init__(message)
        self.original_error = original_error


class BrokerConnectionError(BrokerError):
    """Exception raised when broker connection fails."""

    pass


class BrokerOrderError(BrokerError):
    """Exception raised when order submission fails."""

    pass
```

**Step 2: Write failing tests for error handling**

Add to `tests/test_broker.py`:

```python
from quant.exceptions import BrokerConnectionError, BrokerError, BrokerOrderError


class TestBrokerErrorHandling:
    """Tests for broker error handling."""

    @patch("quant.broker.TradingClient")
    def test_get_account_wraps_connection_error(
        self, mock_trading_client: MagicMock
    ) -> None:
        """get_account should wrap connection errors in BrokerConnectionError."""
        from quant.broker import AlpacaClient

        mock_client = MagicMock()
        mock_client.get_account.side_effect = Exception("Connection refused")
        mock_trading_client.return_value = mock_client

        client = AlpacaClient(api_key="test", secret_key="test", paper=True)

        with pytest.raises(BrokerConnectionError) as exc_info:
            client.get_account()

        assert "Connection refused" in str(exc_info.value.original_error)

    @patch("quant.broker.TradingClient")
    def test_get_positions_wraps_connection_error(
        self, mock_trading_client: MagicMock
    ) -> None:
        """get_positions should wrap connection errors in BrokerConnectionError."""
        from quant.broker import AlpacaClient

        mock_client = MagicMock()
        mock_client.get_all_positions.side_effect = Exception("Timeout")
        mock_trading_client.return_value = mock_client

        client = AlpacaClient(api_key="test", secret_key="test", paper=True)

        with pytest.raises(BrokerConnectionError) as exc_info:
            client.get_positions()

        assert "Timeout" in str(exc_info.value.original_error)

    @patch("quant.broker.TradingClient")
    def test_submit_order_wraps_order_error(
        self, mock_trading_client: MagicMock
    ) -> None:
        """submit_market_order should wrap order errors in BrokerOrderError."""
        from quant.broker import AlpacaClient, OrderSide

        mock_client = MagicMock()
        mock_client.submit_order.side_effect = Exception("Insufficient funds")
        mock_trading_client.return_value = mock_client

        client = AlpacaClient(api_key="test", secret_key="test", paper=True)

        with pytest.raises(BrokerOrderError) as exc_info:
            client.submit_market_order(
                ticker="AAPL",
                side=OrderSide.BUY,
                notional=Decimal("1000000"),
            )

        assert "Insufficient funds" in str(exc_info.value.original_error)

    @patch("quant.broker.TradingClient")
    def test_close_position_wraps_error(
        self, mock_trading_client: MagicMock
    ) -> None:
        """close_position should wrap errors in BrokerOrderError."""
        from quant.broker import AlpacaClient

        mock_client = MagicMock()
        mock_client.close_position.side_effect = Exception("Position not found")
        mock_trading_client.return_value = mock_client

        client = AlpacaClient(api_key="test", secret_key="test", paper=True)

        with pytest.raises(BrokerOrderError) as exc_info:
            client.close_position("AAPL")

        assert "Position not found" in str(exc_info.value.original_error)
```

**Step 3: Run test to verify it fails**

Run: `uv run pytest tests/test_broker.py::TestBrokerErrorHandling -v`

Expected: FAIL - wrong exception type raised

**Step 4: Add error handling to broker methods**

Update `src/quant/broker.py`. Add import at top:

```python
from quant.exceptions import BrokerConnectionError, BrokerOrderError
```

Wrap `get_account` method (lines 60-71):

```python
    def get_account(self) -> AccountInfo:
        """Get account information.

        Returns:
            AccountInfo with cash, equity, and buying power.

        Raises:
            BrokerConnectionError: If the API call fails.
        """
        try:
            account = self._client.get_account()
            return AccountInfo(
                cash=Decimal(str(account.cash)),
                equity=Decimal(str(account.equity)),
                buying_power=Decimal(str(account.buying_power)),
            )
        except Exception as e:
            raise BrokerConnectionError(
                f"Failed to get account: {e}", original_error=e
            ) from e
```

Wrap `get_positions` method (lines 73-88):

```python
    def get_positions(self) -> list[Position]:
        """Get all open positions.

        Returns:
            List of Position objects.

        Raises:
            BrokerConnectionError: If the API call fails.
        """
        try:
            positions = self._client.get_all_positions()
            return [
                Position(
                    ticker=str(pos.symbol),
                    quantity=Decimal(str(pos.qty)),
                    avg_price=Decimal(str(pos.avg_entry_price)),
                    current_price=Decimal(str(pos.current_price)),
                )
                for pos in positions
            ]
        except Exception as e:
            raise BrokerConnectionError(
                f"Failed to get positions: {e}", original_error=e
            ) from e
```

Wrap the order submission in `submit_market_order` (around line 131-141):

```python
        request = MarketOrderRequest(**request_params)

        try:
            order = self._client.submit_order(request)
        except Exception as e:
            raise BrokerOrderError(
                f"Failed to submit order for {ticker}: {e}", original_error=e
            ) from e

        return OrderResult(
            order_id=str(order.id),
            status=str(order.status.value) if order.status else "unknown",
            ticker=str(order.symbol),
            side=side,
            quantity=Decimal(str(order.qty)) if order.qty else None,
            notional=Decimal(str(order.notional)) if order.notional else None,
        )
```

Wrap `close_position` method (lines 143-168):

```python
    def close_position(self, ticker: str) -> OrderResult:
        """Close an existing position.

        Args:
            ticker: The stock ticker symbol.

        Returns:
            OrderResult with order details.

        Raises:
            BrokerOrderError: If closing the position fails.
        """
        try:
            order = self._client.close_position(
                ticker,
                close_options=ClosePositionRequest(percentage="100"),
            )
        except Exception as e:
            raise BrokerOrderError(
                f"Failed to close position for {ticker}: {e}", original_error=e
            ) from e

        side = OrderSide.SELL if order.side.value == "sell" else OrderSide.BUY

        return OrderResult(
            order_id=str(order.id),
            status=str(order.status.value) if order.status else "unknown",
            ticker=str(order.symbol),
            side=side,
            quantity=Decimal(str(order.qty)) if order.qty else None,
            notional=Decimal(str(order.notional)) if order.notional else None,
        )
```

**Step 5: Run test to verify it passes**

Run: `uv run pytest tests/test_broker.py::TestBrokerErrorHandling -v`

Expected: PASSED (4 tests)

**Step 6: Run all tests**

Run: `uv run pytest tests/ -v`

Expected: All tests pass

**Step 7: Commit**

```bash
git add src/quant/exceptions.py src/quant/broker.py tests/test_broker.py
git commit -m "fix: add error handling to broker client

Wrap all API calls in try/except blocks and raise custom exceptions:
- BrokerConnectionError for get_account/get_positions failures
- BrokerOrderError for order submission/close failures

This prevents network issues from crashing the entire system."
```

---

## Task 5: Protect Secrets with SecretStr

API keys are exposed in logs and error messages.

**Files:**
- Modify: `src/quant/config.py`
- Modify: `src/quant/broker.py`
- Modify: `src/quant/data.py`
- Modify: `src/quant/api.py`
- Modify: `tests/test_config.py`

**Step 1: Write test for secret protection**

Add to `tests/test_config.py`:

```python
class TestSecretProtection:
    """Tests for secret field protection."""

    def test_api_key_not_in_repr(self) -> None:
        """API key should not appear in repr output."""
        env = {
            "ALPACA_API_KEY": "super_secret_key_12345",
            "ALPACA_SECRET_KEY": "even_more_secret",
            "ALPACA_BASE_URL": "https://paper-api.alpaca.markets",
            "DATABASE_URL": "postgresql://user:pass@localhost/db",
            "REDIS_URL": "redis://localhost:6379",
        }
        with patch.dict(os.environ, env, clear=True):
            settings = Settings()
            repr_str = repr(settings)

            assert "super_secret_key_12345" not in repr_str
            assert "even_more_secret" not in repr_str

    def test_api_key_not_in_str(self) -> None:
        """API key should not appear in str output."""
        env = {
            "ALPACA_API_KEY": "super_secret_key_12345",
            "ALPACA_SECRET_KEY": "even_more_secret",
            "ALPACA_BASE_URL": "https://paper-api.alpaca.markets",
            "DATABASE_URL": "postgresql://user:pass@localhost/db",
            "REDIS_URL": "redis://localhost:6379",
        }
        with patch.dict(os.environ, env, clear=True):
            settings = Settings()
            str_output = str(settings)

            assert "super_secret_key_12345" not in str_output
            assert "even_more_secret" not in str_output

    def test_can_access_secret_value(self) -> None:
        """Should be able to access the secret value when needed."""
        env = {
            "ALPACA_API_KEY": "super_secret_key_12345",
            "ALPACA_SECRET_KEY": "even_more_secret",
            "ALPACA_BASE_URL": "https://paper-api.alpaca.markets",
            "DATABASE_URL": "postgresql://user:pass@localhost/db",
            "REDIS_URL": "redis://localhost:6379",
        }
        with patch.dict(os.environ, env, clear=True):
            settings = Settings()

            # Can get the actual value using get_secret_value()
            assert settings.alpaca_api_key.get_secret_value() == "super_secret_key_12345"
            assert settings.alpaca_secret_key.get_secret_value() == "even_more_secret"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_config.py::TestSecretProtection -v`

Expected: FAIL - secrets appear in repr/str, get_secret_value() doesn't exist

**Step 3: Update config to use SecretStr**

In `src/quant/config.py`, update imports:

```python
from pydantic import Field, SecretStr, field_validator
```

Update the secret fields:

```python
    # Alpaca broker settings
    alpaca_api_key: SecretStr
    alpaca_secret_key: SecretStr
    alpaca_base_url: str
```

**Step 4: Update broker.py to use get_secret_value()**

In `src/quant/broker.py`, the `__init__` now receives `SecretStr`, but we need to get the actual value. The caller (api.py) needs to pass the secret value.

Update `src/quant/api.py` where `AlpacaClient` is instantiated (around line 35):

```python
@lru_cache
def get_broker() -> AlpacaClient:
    """Get cached broker client."""
    settings = get_settings()
    return AlpacaClient(
        api_key=settings.alpaca_api_key.get_secret_value(),
        secret_key=settings.alpaca_secret_key.get_secret_value(),
        paper=True,
    )
```

Update `src/quant/api.py` where `MarketDataPipeline` is instantiated (around line 45):

```python
@lru_cache
def get_data_pipeline() -> MarketDataPipeline:
    """Get cached data pipeline."""
    settings = get_settings()
    return MarketDataPipeline(
        api_key=settings.alpaca_api_key.get_secret_value(),
        secret_key=settings.alpaca_secret_key.get_secret_value(),
        watchlist=WATCHLIST,
    )
```

**Step 5: Run test to verify it passes**

Run: `uv run pytest tests/test_config.py::TestSecretProtection -v`

Expected: PASSED (3 tests)

**Step 6: Run all tests**

Run: `uv run pytest tests/ -v`

Expected: All tests pass

**Step 7: Commit**

```bash
git add src/quant/config.py src/quant/api.py tests/test_config.py
git commit -m "fix: protect API keys with SecretStr

API keys now use Pydantic's SecretStr type which:
- Masks values in repr() and str() output
- Requires explicit .get_secret_value() to access
- Prevents accidental logging of secrets"
```

---

## Task 6: Add Thread Safety to Registry

Registry can corrupt under concurrent access.

**Files:**
- Modify: `src/quant/strategy.py`
- Modify: `tests/test_strategy.py`

**Step 1: Write failing test for thread safety**

Add to `tests/test_strategy.py`:

```python
import threading
import time


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
```

**Step 2: Run test to verify potential issues**

Run: `uv run pytest tests/test_strategy.py::TestRegistryThreadSafety -v`

Note: This may pass sometimes due to race condition timing, but the code is still unsafe.

**Step 3: Add thread safety to registry**

Update `src/quant/strategy.py`:

```python
"""Strategy protocol and registry for the quant trading system."""

import threading
from typing import Protocol, runtime_checkable

from quant.models import BacktestResult, MarketContext, Signal


@runtime_checkable
class Strategy(Protocol):
    """Protocol defining the interface for trading strategies."""

    @property
    def name(self) -> str:
        """The unique name of the strategy."""
        ...

    @property
    def version(self) -> str:
        """The version of the strategy."""
        ...

    @property
    def description(self) -> str:
        """A description of what the strategy does."""
        ...

    def analyze(self, context: MarketContext) -> list[Signal]:
        """Analyze market context and generate trading signals."""
        ...

    def explain(self, signal: Signal) -> str:
        """Explain the reasoning behind a trading signal."""
        ...

    def backtest(self, historical: list[MarketContext]) -> BacktestResult:
        """Backtest the strategy against historical market data."""
        ...


class StrategyRegistry:
    """Thread-safe registry for managing trading strategies."""

    def __init__(self) -> None:
        """Initialize an empty strategy registry."""
        self._strategies: dict[str, Strategy] = {}
        self._lock = threading.RLock()

    def register(self, strategy: Strategy) -> None:
        """Register a strategy in the registry.

        Args:
            strategy: The strategy to register.
        """
        with self._lock:
            self._strategies[strategy.name] = strategy

    def get(self, name: str) -> Strategy:
        """Get a strategy by name.

        Args:
            name: The name of the strategy to retrieve.

        Returns:
            The strategy with the given name.

        Raises:
            KeyError: If no strategy with the given name exists.
        """
        with self._lock:
            if name not in self._strategies:
                raise KeyError(f"Strategy '{name}' not found in registry")
            return self._strategies[name]

    def list_strategies(self) -> list[str]:
        """List all registered strategy names.

        Returns:
            A list of strategy names.
        """
        with self._lock:
            return list(self._strategies.keys())

    def all(self) -> list[Strategy]:
        """Get all registered strategies.

        Returns:
            A list of all registered strategies.
        """
        with self._lock:
            return list(self._strategies.values())
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_strategy.py::TestRegistryThreadSafety -v`

Expected: PASSED (2 tests)

**Step 5: Run all tests**

Run: `uv run pytest tests/ -v`

Expected: All tests pass

**Step 6: Commit**

```bash
git add src/quant/strategy.py tests/test_strategy.py
git commit -m "fix: add thread safety to strategy registry

All registry operations now use RLock for thread-safe access.
This prevents crashes and data corruption under concurrent load."
```

---

## Task 7: Final Verification

Run all tests and verify the system works.

**Step 1: Run full test suite**

Run: `uv run pytest tests/ -v --tb=short`

Expected: All tests pass (should be 110+ tests now)

**Step 2: Run type checking**

Run: `uv run mypy src/quant/ --ignore-missing-imports`

Expected: No errors (or document known issues)

**Step 3: Run linting**

Run: `uv run ruff check src/ tests/`

Expected: No errors

**Step 4: Update critique findings**

Mark fixed issues in `docs/critique-findings.md`:

Add at the top:

```markdown
## Fixed Issues

| Issue | Fixed In | Commit |
|-------|----------|--------|
| RSI Score Inverted | Task 1 | fix: correct RSI score... |
| Bad Data Defaults | Task 2 | fix: validate indicators... |
| No Order Validation | Task 3 | fix: validate order inputs... |
| No Error Handling | Task 4 | fix: add error handling... |
| Secrets Exposure | Task 5 | fix: protect API keys... |
| No Thread Safety | Task 6 | fix: add thread safety... |
```

**Step 5: Final commit**

```bash
git add docs/critique-findings.md
git commit -m "docs: mark critical issues as fixed"
```

---

*Plan created: 2026-01-28*
*Estimated time: 2-3 hours*
*Tests added: ~25 new tests*
