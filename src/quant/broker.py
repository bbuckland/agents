"""Alpaca broker client for the quant trading system."""

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Any

from alpaca.trading.client import TradingClient
from alpaca.trading.enums import OrderSide as AlpacaOrderSide
from alpaca.trading.requests import ClosePositionRequest, MarketOrderRequest

from quant.models import Position


class OrderSide(Enum):
    """Order side enum."""

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
    """Result of an order submission."""

    order_id: str
    status: str
    ticker: str
    side: OrderSide
    quantity: Decimal | None
    notional: Decimal | None


class AlpacaClient:
    """Wrapper for Alpaca Trading API."""

    def __init__(self, api_key: str, secret_key: str, paper: bool = True) -> None:
        """Initialize the Alpaca client.

        Args:
            api_key: Alpaca API key.
            secret_key: Alpaca secret key.
            paper: Whether to use paper trading (default True).
        """
        self._client = TradingClient(
            api_key=api_key,
            secret_key=secret_key,
            paper=paper,
        )

    def get_account(self) -> AccountInfo:
        """Get account information.

        Returns:
            AccountInfo with cash, equity, and buying power.
        """
        account = self._client.get_account()
        return AccountInfo(
            cash=Decimal(str(account.cash)),
            equity=Decimal(str(account.equity)),
            buying_power=Decimal(str(account.buying_power)),
        )

    def get_positions(self) -> list[Position]:
        """Get all open positions.

        Returns:
            List of Position objects.
        """
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

        alpaca_side = (
            AlpacaOrderSide.BUY if side == OrderSide.BUY else AlpacaOrderSide.SELL
        )

        request_params: dict[str, Any] = {
            "symbol": ticker,
            "side": alpaca_side,
            "time_in_force": "day",
        }

        if notional is not None:
            request_params["notional"] = float(notional)
        else:
            request_params["qty"] = float(quantity)  # type: ignore[arg-type]

        request = MarketOrderRequest(**request_params)
        order = self._client.submit_order(request)

        return OrderResult(
            order_id=str(order.id),
            status=str(order.status.value) if order.status else "unknown",
            ticker=str(order.symbol),
            side=side,
            quantity=Decimal(str(order.qty)) if order.qty else None,
            notional=Decimal(str(order.notional)) if order.notional else None,
        )

    def close_position(self, ticker: str) -> OrderResult:
        """Close an existing position.

        Args:
            ticker: The stock ticker symbol.

        Returns:
            OrderResult with order details.
        """
        # Close 100% of the position
        order = self._client.close_position(
            ticker,
            close_options=ClosePositionRequest(percentage="100"),
        )

        # Determine side based on order
        side = OrderSide.SELL if order.side.value == "sell" else OrderSide.BUY

        return OrderResult(
            order_id=str(order.id),
            status=str(order.status.value) if order.status else "unknown",
            ticker=str(order.symbol),
            side=side,
            quantity=Decimal(str(order.qty)) if order.qty else None,
            notional=Decimal(str(order.notional)) if order.notional else None,
        )
