"""Market data pipeline for retrieving and processing market data."""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, cast

import pandas as pd
from alpaca.data.enums import DataFeed
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.models import BarSet
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame

from quant.models import MarketContext, Position


@dataclass
class Bar:
    """OHLCV bar data for a single time period."""

    open: float
    high: float
    low: float
    close: float
    volume: int
    timestamp: datetime


def compute_rsi(prices: pd.Series, period: int = 14) -> float:
    """
    Compute the Relative Strength Index (RSI) for a price series.

    Args:
        prices: Series of closing prices
        period: RSI lookback period (default 14)

    Returns:
        RSI value between 0 and 100
    """
    if len(prices) < period + 1:
        return 50.0  # Return neutral RSI if insufficient data

    # Calculate price changes
    delta = prices.diff()

    # Separate gains and losses
    gains = delta.where(delta > 0, 0.0)
    losses = (-delta).where(delta < 0, 0.0)

    # Calculate average gains and losses using exponential moving average
    avg_gain = gains.ewm(span=period, adjust=False).mean()
    avg_loss = losses.ewm(span=period, adjust=False).mean()

    # Calculate RS and RSI
    rs = avg_gain / avg_loss
    rsi = 100.0 - (100.0 / (1.0 + rs))

    return float(rsi.iloc[-1])


def compute_macd(
    prices: pd.Series,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> dict[str, float]:
    """
    Compute MACD (Moving Average Convergence Divergence) indicator.

    Args:
        prices: Series of closing prices
        fast: Fast EMA period (default 12)
        slow: Slow EMA period (default 26)
        signal: Signal line EMA period (default 9)

    Returns:
        Dictionary with 'macd', 'signal', and 'histogram' values
    """
    if len(prices) < slow + signal:
        return {"macd": 0.0, "signal": 0.0, "histogram": 0.0}

    # Calculate EMAs
    ema_fast = prices.ewm(span=fast, adjust=False).mean()
    ema_slow = prices.ewm(span=slow, adjust=False).mean()

    # MACD line
    macd_line = ema_fast - ema_slow

    # Signal line
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()

    # Histogram
    histogram = macd_line - signal_line

    return {
        "macd": float(macd_line.iloc[-1]),
        "signal": float(signal_line.iloc[-1]),
        "histogram": float(histogram.iloc[-1]),
    }


class MarketDataPipeline:
    """Pipeline for fetching and processing market data from Alpaca."""

    def __init__(
        self,
        api_key: str,
        secret_key: str,
        watchlist: list[str],
    ) -> None:
        """
        Initialize the market data pipeline.

        Args:
            api_key: Alpaca API key
            secret_key: Alpaca secret key
            watchlist: List of ticker symbols to track
        """
        self.api_key = api_key
        self.secret_key = secret_key
        self.watchlist = watchlist
        self.client = StockHistoricalDataClient(api_key, secret_key)

    def get_latest_bars(
        self,
        tickers: list[str] | None = None,
        days: int = 30,
    ) -> dict[str, Bar]:
        """
        Get the latest bar for each ticker.

        Args:
            tickers: List of tickers to fetch (defaults to watchlist)
            days: Number of days to look back for data

        Returns:
            Dictionary mapping ticker symbols to their latest Bar
        """
        symbols = tickers or self.watchlist
        if not symbols:
            return {}

        end = datetime.now(timezone.utc)
        start = end - timedelta(days=days)

        request = StockBarsRequest(
            symbol_or_symbols=symbols,
            timeframe=TimeFrame.Day,
            start=start,
            end=end,
            feed=DataFeed.IEX,  # Use free IEX feed instead of SIP
        )

        bars_response = cast(BarSet, self.client.get_stock_bars(request))
        result: dict[str, Bar] = {}

        for symbol in symbols:
            symbol_bars = bars_response.data.get(symbol, [])
            if symbol_bars:
                latest = symbol_bars[-1]
                result[symbol] = Bar(
                    open=float(latest.open),
                    high=float(latest.high),
                    low=float(latest.low),
                    close=float(latest.close),
                    volume=int(latest.volume),
                    timestamp=latest.timestamp,
                )

        return result

    def get_historical_bars(
        self,
        ticker: str,
        days: int = 60,
    ) -> pd.DataFrame:
        """
        Get historical daily bars for a single ticker.

        Args:
            ticker: The ticker symbol
            days: Number of days of historical data

        Returns:
            DataFrame with OHLCV data indexed by timestamp
        """
        end = datetime.now(timezone.utc)
        start = end - timedelta(days=days)

        request = StockBarsRequest(
            symbol_or_symbols=[ticker],
            timeframe=TimeFrame.Day,
            start=start,
            end=end,
            feed=DataFeed.IEX,  # Use free IEX feed instead of SIP
        )

        bars_response = cast(BarSet, self.client.get_stock_bars(request))
        symbol_bars = bars_response.data.get(ticker, [])

        if not symbol_bars:
            return pd.DataFrame(
                columns=["open", "high", "low", "close", "volume"],
            )

        data = [
            {
                "timestamp": bar.timestamp,
                "open": float(bar.open),
                "high": float(bar.high),
                "low": float(bar.low),
                "close": float(bar.close),
                "volume": int(bar.volume),
            }
            for bar in symbol_bars
        ]

        df = pd.DataFrame(data)
        df.set_index("timestamp", inplace=True)
        return df

    def compute_indicators(self, ticker: str) -> dict[str, float]:
        """
        Compute technical indicators for a ticker.

        Args:
            ticker: The ticker symbol

        Returns:
            Dictionary with indicator values: rsi, macd, sma_20, sma_50,
            volume_avg_20, volume_ratio
        """
        # Get enough historical data for all indicators
        df = self.get_historical_bars(ticker, days=60)

        if df.empty or len(df) < 2:
            return {
                "rsi": 50.0,
                "macd": 0.0,
                "signal": 0.0,
                "histogram": 0.0,
                "sma_20": 0.0,
                "sma_50": 0.0,
                "volume_avg_20": 0.0,
                "volume_ratio": 1.0,
            }

        prices = df["close"]
        volumes = df["volume"]

        # Compute RSI
        rsi = compute_rsi(prices)

        # Compute MACD
        macd_values = compute_macd(prices)

        # Compute SMAs
        sma_20 = float(prices.rolling(window=20).mean().iloc[-1]) if len(prices) >= 20 else 0.0
        sma_50 = float(prices.rolling(window=50).mean().iloc[-1]) if len(prices) >= 50 else 0.0

        # Compute volume metrics
        volume_avg_20 = (
            float(volumes.rolling(window=20).mean().iloc[-1]) if len(volumes) >= 20 else 0.0
        )
        current_volume = float(volumes.iloc[-1])
        volume_ratio = current_volume / volume_avg_20 if volume_avg_20 > 0 else 1.0

        return {
            "rsi": rsi,
            "macd": macd_values["macd"],
            "signal": macd_values["signal"],
            "histogram": macd_values["histogram"],
            "sma_20": sma_20,
            "sma_50": sma_50,
            "volume_avg_20": volume_avg_20,
            "volume_ratio": volume_ratio,
        }

    def build_context(
        self,
        cash: float,
        positions: list[Position],
        futures_signal: float = 0.0,
        vix: float = 20.0,
    ) -> MarketContext:
        """
        Build a complete market context for strategy evaluation.

        Args:
            cash: Available cash in the account
            positions: List of current positions
            futures_signal: Pre-market futures signal (-1 to 1)
            vix: Current VIX value

        Returns:
            MarketContext with indicators for all watchlist symbols
        """
        # Get latest bars for all watched symbols (stored internally for indicator computation)
        self._latest_bars = self.get_latest_bars()

        # Compute indicators for all symbols
        indicators: dict[str, Any] = {}
        for ticker in self.watchlist:
            indicators[ticker] = self.compute_indicators(ticker)

        return MarketContext(
            cash=Decimal(str(cash)),
            positions=positions,
            indicators=indicators,
            futures_signal=futures_signal,
            vix=vix,
            timestamp=datetime.now(),
        )
