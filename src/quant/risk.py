"""Risk management for the quant trading system."""

from dataclasses import dataclass
from decimal import Decimal

from quant.models import Action, MarketContext, Signal


@dataclass
class ValidationResult:
    """Result of signal validation against risk rules."""

    allowed: bool
    reason: str
    adjusted_size: Decimal | None = None


class RiskManager:
    """Enforces risk limits and position sizing rules.

    The RiskManager ensures trades comply with capital preservation rules:
    - Protects the base reserve (untouchable capital floor)
    - Limits position sizes to a maximum amount
    - Restricts the number of concurrent positions
    - Tracks daily P&L and enforces daily loss limits
    """

    def __init__(
        self,
        base_reserve: Decimal | int,
        max_position_size: Decimal | int,
        max_concurrent_positions: int,
        max_daily_loss: Decimal | int,
    ) -> None:
        """Initialize the risk manager.

        Args:
            base_reserve: Minimum capital that cannot be traded.
            max_position_size: Maximum size for any single position.
            max_concurrent_positions: Maximum number of open positions allowed.
            max_daily_loss: Maximum loss allowed in a single day before trading stops.
        """
        self.base_reserve = Decimal(str(base_reserve))
        self.max_position_size = Decimal(str(max_position_size))
        self.max_concurrent_positions = max_concurrent_positions
        self.max_daily_loss = Decimal(str(max_daily_loss))
        self._daily_pnl = Decimal("0")

    def validate_signal(self, signal: Signal, context: MarketContext) -> ValidationResult:
        """Validate a trading signal against risk rules.

        Checks in order:
        1. Daily loss limit not exceeded
        2. Not at max concurrent positions (for new ticker BUY signals)
        3. Trade won't dip into base reserve
        4. Adjusts size down if needed (to max_position_size or available capital)

        Args:
            signal: The trading signal to validate.
            context: Current market context including cash and positions.

        Returns:
            ValidationResult indicating if the trade is allowed and any adjustments.
        """
        # Check 1: Daily loss limit
        if self._daily_pnl <= -self.max_daily_loss:
            return ValidationResult(
                allowed=False,
                reason="Daily loss limit exceeded. No new trades until reset.",
            )

        # Check 2: Max concurrent positions (only for BUY on new tickers)
        if signal.action == Action.BUY:
            current_tickers = {p.ticker for p in context.positions}
            if signal.ticker not in current_tickers:
                if len(context.positions) >= self.max_concurrent_positions:
                    return ValidationResult(
                        allowed=False,
                        reason=f"At maximum concurrent positions ({self.max_concurrent_positions}).",
                    )

        # Check 3: Available capital (cash minus base reserve)
        available_capital = context.cash - self.base_reserve
        if available_capital <= 0:
            return ValidationResult(
                allowed=False,
                reason="Trade would dip into base reserve.",
            )

        # Check 4: Position size limits and adjustments
        requested_size = signal.size

        # Cap at max position size
        adjusted_size = min(requested_size, self.max_position_size)

        # Cap at available capital
        adjusted_size = min(adjusted_size, available_capital)

        # If we can't do any size, block the trade
        if adjusted_size <= 0:
            return ValidationResult(
                allowed=False,
                reason="Trade would dip into base reserve.",
            )

        # Return result with any size adjustment
        if adjusted_size < requested_size:
            return ValidationResult(
                allowed=True,
                reason=f"Size adjusted from {requested_size} to {adjusted_size}.",
                adjusted_size=adjusted_size,
            )

        return ValidationResult(
            allowed=True,
            reason="Trade validated.",
            adjusted_size=adjusted_size,
        )

    def record_pnl(self, pnl: Decimal) -> None:
        """Record realized P&L for daily tracking.

        Args:
            pnl: The profit/loss amount to record (positive for profit, negative for loss).
        """
        self._daily_pnl += pnl

    def reset_daily(self) -> None:
        """Reset daily P&L tracker.

        Should be called at the start of each trading day.
        """
        self._daily_pnl = Decimal("0")

    def can_trade(self, context: MarketContext) -> bool:
        """Quick check if any trading is allowed.

        Returns False if:
        - Daily loss limit has been exceeded
        - No available capital above base reserve

        Args:
            context: Current market context.

        Returns:
            True if trading is allowed, False otherwise.
        """
        if self._daily_pnl <= -self.max_daily_loss:
            return False

        available_capital = context.cash - self.base_reserve
        return available_capital > 0

    @property
    def daily_pnl(self) -> Decimal:
        """Get the current daily P&L."""
        return self._daily_pnl
