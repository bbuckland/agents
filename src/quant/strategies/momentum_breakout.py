"""Momentum Breakout Strategy implementation."""

from decimal import Decimal
from typing import Any

from quant.models import Action, BacktestResult, MarketContext, Signal


class MomentumBreakoutStrategy:
    """
    Momentum breakout strategy that generates BUY signals when:
    - Price breaks above SMA20 (breakout)
    - Volume ratio >= 1.2 (volume confirms)
    - RSI < 70 (not overbought)
    - MACD histogram > 0 (bullish momentum)
    """

    name: str = "momentum_breakout"
    version: str = "1.0"

    def analyze(self, context: MarketContext) -> list[Signal]:
        """
        Analyze market context and generate trading signals.

        Args:
            context: MarketContext containing indicators for each ticker

        Returns:
            List of Signal objects for tickers meeting breakout criteria
        """
        signals: list[Signal] = []

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

            if breakout and volume_confirms and not_overbought and bullish_momentum:
                # Calculate confidence based on signal strength (0-100 scale)
                confidence = self._calculate_confidence(
                    price=price,
                    sma20=sma20,
                    volume_ratio=volume_ratio,
                    rsi=rsi,
                    macd_histogram=macd_histogram,
                )

                # Set stop loss at 3% below entry, take profit at 5% above
                entry_price = Decimal(str(price))
                stop_loss = entry_price * Decimal("0.97")
                take_profit = entry_price * Decimal("1.05")

                signal = Signal(
                    ticker=ticker,
                    action=Action.BUY,
                    size=Decimal("0"),  # Size to be determined by position sizing
                    confidence=confidence,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    entry_price=entry_price,
                    strategy_name=self.name,
                    rationale_tags=[
                        "breakout",
                        "volume_confirmed",
                        "momentum_positive",
                    ],
                )
                signals.append(signal)

        return signals

    def _calculate_confidence(
        self,
        price: float,
        sma20: float,
        volume_ratio: float,
        rsi: float,
        macd_histogram: float,
    ) -> int:
        """
        Calculate confidence score based on signal strength.

        Confidence is based on:
        - How far price is above SMA20 (stronger breakout = higher confidence)
        - Volume ratio strength (higher volume = higher confidence)
        - RSI distance from overbought (more room to run = higher confidence)
        - MACD histogram strength (stronger momentum = higher confidence)

        Returns:
            Confidence score from 0 to 100
        """
        # Price breakout strength (0-25)
        breakout_pct = (price - sma20) / sma20 if sma20 > 0 else 0
        breakout_score = min(breakout_pct * 500, 25)  # Cap at 25

        # Volume strength (0-25)
        volume_score = min((volume_ratio - 1.0) * 50, 25)

        # RSI momentum strength (0-25)
        # RSI 40-70 indicates healthy momentum (not oversold, not overbought)
        # Higher RSI = stronger momentum = higher score
        if 40 <= rsi < 70:
            rsi_score = ((rsi - 40) / 30) * 25  # 0 at RSI 40, 25 at RSI 70
        else:
            rsi_score = 0  # Below 40 is weak/oversold, above 70 is overbought

        # MACD momentum (0-25)
        macd_score = min(macd_histogram * 10, 25)

        # Total confidence (0-100)
        confidence = breakout_score + volume_score + rsi_score + macd_score

        # Ensure confidence is between 0 and 100, return as integer
        return max(0, min(100, int(confidence)))

    def explain(self, signal: Signal) -> str:
        """
        Generate a human-readable explanation of the signal.

        Args:
            signal: The Signal to explain

        Returns:
            Human-readable string explaining the signal
        """
        explanation = (
            f"{signal.ticker}: {signal.action.value} signal with "
            f"{signal.confidence}% confidence."
        )

        if signal.entry_price is not None:
            explanation += f" Entry at ${signal.entry_price:.2f}"

        if signal.stop_loss is not None:
            explanation += f", stop loss at ${signal.stop_loss:.2f}"

        if signal.take_profit is not None:
            explanation += f", take profit at ${signal.take_profit:.2f}"

        explanation += "."

        if signal.rationale_tags:
            explanation += f" Tags: {', '.join(signal.rationale_tags)}."

        return explanation

    def backtest(self, historical: Any) -> BacktestResult:
        """
        Backtest the strategy on historical data.

        Args:
            historical: Historical market data (placeholder)

        Returns:
            BacktestResult with performance metrics (placeholder returning zeros)
        """
        return BacktestResult(
            total_return=Decimal("0"),
            total_trades=0,
            winning_trades=0,
            losing_trades=0,
            gross_profit=Decimal("0"),
            gross_loss=Decimal("0"),
            max_drawdown=Decimal("0"),
            sharpe_ratio=0.0,
            trades=[],
        )
