"""Tests for the Alpaca broker client."""

from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from quant.broker import AccountInfo, AlpacaClient, OrderResult, OrderSide
from quant.models import Position


class TestAlpacaClient:
    """Tests for AlpacaClient."""

    @patch("quant.broker.TradingClient")
    def test_get_account_returns_account_info(self, mock_trading_client: MagicMock) -> None:
        """Test that get_account returns AccountInfo with correct values."""
        # Setup mock
        mock_client_instance = MagicMock()
        mock_trading_client.return_value = mock_client_instance

        mock_account = MagicMock()
        mock_account.cash = "10000.50"
        mock_account.equity = "25000.75"
        mock_account.buying_power = "40000.00"
        mock_client_instance.get_account.return_value = mock_account

        # Create client and call method
        client = AlpacaClient(api_key="test_key", secret_key="test_secret", paper=True)
        account_info = client.get_account()

        # Assertions
        assert isinstance(account_info, AccountInfo)
        assert account_info.cash == Decimal("10000.50")
        assert account_info.equity == Decimal("25000.75")
        assert account_info.buying_power == Decimal("40000.00")
        mock_client_instance.get_account.assert_called_once()

    @patch("quant.broker.TradingClient")
    def test_get_positions_returns_list_of_positions(
        self, mock_trading_client: MagicMock
    ) -> None:
        """Test that get_positions returns list of Position objects."""
        # Setup mock
        mock_client_instance = MagicMock()
        mock_trading_client.return_value = mock_client_instance

        mock_position_1 = MagicMock()
        mock_position_1.symbol = "AAPL"
        mock_position_1.qty = "10"
        mock_position_1.avg_entry_price = "170.00"
        mock_position_1.current_price = "175.00"

        mock_position_2 = MagicMock()
        mock_position_2.symbol = "GOOGL"
        mock_position_2.qty = "5"
        mock_position_2.avg_entry_price = "1350.00"
        mock_position_2.current_price = "1400.00"

        mock_client_instance.get_all_positions.return_value = [
            mock_position_1,
            mock_position_2,
        ]

        # Create client and call method
        client = AlpacaClient(api_key="test_key", secret_key="test_secret", paper=True)
        positions = client.get_positions()

        # Assertions
        assert len(positions) == 2
        assert all(isinstance(pos, Position) for pos in positions)

        # Check first position
        assert positions[0].ticker == "AAPL"
        assert positions[0].quantity == Decimal("10")
        assert positions[0].avg_price == Decimal("170.00")
        assert positions[0].current_price == Decimal("175.00")
        # Check computed properties
        assert positions[0].market_value == Decimal("1750.00")
        assert positions[0].unrealized_pnl == Decimal("50.00")

        # Check second position
        assert positions[1].ticker == "GOOGL"
        assert positions[1].quantity == Decimal("5")

        mock_client_instance.get_all_positions.assert_called_once()

    @patch("quant.broker.TradingClient")
    def test_submit_market_order_with_notional_returns_order_result(
        self, mock_trading_client: MagicMock
    ) -> None:
        """Test that submit_market_order with notional returns OrderResult."""
        # Setup mock
        mock_client_instance = MagicMock()
        mock_trading_client.return_value = mock_client_instance

        mock_order = MagicMock()
        mock_order.id = "order-123"
        mock_order.status.value = "accepted"
        mock_order.symbol = "AAPL"
        mock_order.qty = None
        mock_order.notional = "1000.00"
        mock_client_instance.submit_order.return_value = mock_order

        # Create client and call method
        client = AlpacaClient(api_key="test_key", secret_key="test_secret", paper=True)
        result = client.submit_market_order(
            ticker="AAPL",
            side=OrderSide.BUY,
            notional=Decimal("1000.00"),
        )

        # Assertions
        assert isinstance(result, OrderResult)
        assert result.order_id == "order-123"
        assert result.status == "accepted"
        assert result.ticker == "AAPL"
        assert result.side == OrderSide.BUY
        assert result.quantity is None
        assert result.notional == Decimal("1000.00")
        mock_client_instance.submit_order.assert_called_once()

    @patch("quant.broker.TradingClient")
    def test_submit_market_order_with_quantity_returns_order_result(
        self, mock_trading_client: MagicMock
    ) -> None:
        """Test that submit_market_order with quantity returns OrderResult."""
        # Setup mock
        mock_client_instance = MagicMock()
        mock_trading_client.return_value = mock_client_instance

        mock_order = MagicMock()
        mock_order.id = "order-456"
        mock_order.status.value = "filled"
        mock_order.symbol = "TSLA"
        mock_order.qty = "5"
        mock_order.notional = None
        mock_client_instance.submit_order.return_value = mock_order

        # Create client and call method
        client = AlpacaClient(api_key="test_key", secret_key="test_secret", paper=True)
        result = client.submit_market_order(
            ticker="TSLA",
            side=OrderSide.SELL,
            quantity=Decimal("5"),
        )

        # Assertions
        assert isinstance(result, OrderResult)
        assert result.order_id == "order-456"
        assert result.status == "filled"
        assert result.ticker == "TSLA"
        assert result.side == OrderSide.SELL
        assert result.quantity == Decimal("5")
        assert result.notional is None

    @patch("quant.broker.TradingClient")
    def test_submit_market_order_raises_error_when_no_amount_specified(
        self, mock_trading_client: MagicMock
    ) -> None:
        """Test that submit_market_order raises ValueError when neither notional nor quantity."""
        mock_client_instance = MagicMock()
        mock_trading_client.return_value = mock_client_instance

        client = AlpacaClient(api_key="test_key", secret_key="test_secret", paper=True)

        with pytest.raises(ValueError, match="Either notional or quantity must be provided"):
            client.submit_market_order(ticker="AAPL", side=OrderSide.BUY)

    @patch("quant.broker.TradingClient")
    def test_submit_market_order_raises_error_when_both_amounts_specified(
        self, mock_trading_client: MagicMock
    ) -> None:
        """Test that submit_market_order raises ValueError when both notional and quantity."""
        mock_client_instance = MagicMock()
        mock_trading_client.return_value = mock_client_instance

        client = AlpacaClient(api_key="test_key", secret_key="test_secret", paper=True)

        with pytest.raises(ValueError, match="Cannot specify both notional and quantity"):
            client.submit_market_order(
                ticker="AAPL",
                side=OrderSide.BUY,
                notional=Decimal("1000"),
                quantity=Decimal("10"),
            )

    @patch("quant.broker.ClosePositionRequest")
    @patch("quant.broker.TradingClient")
    def test_close_position_returns_order_result(
        self, mock_trading_client: MagicMock, mock_close_request: MagicMock
    ) -> None:
        """Test that close_position returns OrderResult."""
        # Setup mock
        mock_client_instance = MagicMock()
        mock_trading_client.return_value = mock_client_instance

        mock_order = MagicMock()
        mock_order.id = "close-order-789"
        mock_order.status.value = "accepted"
        mock_order.symbol = "AAPL"
        mock_order.side.value = "sell"
        mock_order.qty = "10"
        mock_order.notional = None
        mock_client_instance.close_position.return_value = mock_order

        # Create client and call method
        client = AlpacaClient(api_key="test_key", secret_key="test_secret", paper=True)
        result = client.close_position(ticker="AAPL")

        # Assertions
        assert isinstance(result, OrderResult)
        assert result.order_id == "close-order-789"
        assert result.status == "accepted"
        assert result.ticker == "AAPL"
        assert result.side == OrderSide.SELL
        assert result.quantity == Decimal("10")
        assert result.notional is None
        mock_client_instance.close_position.assert_called_once()
        mock_close_request.assert_called_once_with(percentage="100")


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


class TestBrokerErrorHandling:
    """Tests for broker error handling."""

    @patch("quant.broker.TradingClient")
    def test_get_account_wraps_connection_error(
        self, mock_trading_client: MagicMock
    ) -> None:
        """get_account should wrap connection errors in BrokerConnectionError."""
        from quant.broker import AlpacaClient
        from quant.exceptions import BrokerConnectionError

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
        from quant.exceptions import BrokerConnectionError

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
        from quant.exceptions import BrokerOrderError

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
        from quant.exceptions import BrokerOrderError

        mock_client = MagicMock()
        mock_client.close_position.side_effect = Exception("Position not found")
        mock_trading_client.return_value = mock_client

        client = AlpacaClient(api_key="test", secret_key="test", paper=True)

        with pytest.raises(BrokerOrderError) as exc_info:
            client.close_position("AAPL")

        assert "Position not found" in str(exc_info.value.original_error)
