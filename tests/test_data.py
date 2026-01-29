"""Tests for the market data pipeline."""

from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from quant.data import Bar, MarketDataPipeline, compute_macd, compute_rsi
from quant.models import MarketContext, Position


class TestBar:
    """Tests for the Bar dataclass."""

    def test_bar_creation(self) -> None:
        """Test creating a Bar with all fields."""
        timestamp = datetime.now(timezone.utc)
        bar = Bar(
            open=100.0,
            high=105.0,
            low=99.0,
            close=103.0,
            volume=1000000,
            timestamp=timestamp,
        )
        assert bar.open == 100.0
        assert bar.high == 105.0
        assert bar.low == 99.0
        assert bar.close == 103.0
        assert bar.volume == 1000000
        assert bar.timestamp == timestamp


class TestComputeRSI:
    """Tests for the compute_rsi function."""

    def test_rsi_returns_value_between_0_and_100(self) -> None:
        """Test that RSI returns a value between 0 and 100."""
        # Generate synthetic price data with some ups and downs
        prices = pd.Series([100.0 + i * 0.5 + (i % 3 - 1) * 2 for i in range(30)])
        rsi = compute_rsi(prices)
        assert 0.0 <= rsi <= 100.0

    def test_rsi_overbought_condition(self) -> None:
        """Test RSI approaches 100 in strong uptrend."""
        # Strong uptrend
        prices = pd.Series([100.0 + i * 5 for i in range(30)])
        rsi = compute_rsi(prices)
        assert rsi > 70.0  # Should be overbought

    def test_rsi_oversold_condition(self) -> None:
        """Test RSI approaches 0 in strong downtrend."""
        # Strong downtrend
        prices = pd.Series([200.0 - i * 5 for i in range(30)])
        rsi = compute_rsi(prices)
        assert rsi < 30.0  # Should be oversold

    def test_rsi_insufficient_data(self) -> None:
        """Test RSI returns neutral value with insufficient data."""
        prices = pd.Series([100.0, 101.0, 102.0])
        rsi = compute_rsi(prices)
        assert rsi == 50.0


class TestComputeMACD:
    """Tests for the compute_macd function."""

    def test_macd_returns_dict_with_required_keys(self) -> None:
        """Test MACD returns dictionary with macd, signal, histogram."""
        prices = pd.Series([100.0 + i * 0.5 for i in range(50)])
        result = compute_macd(prices)
        assert "macd" in result
        assert "signal" in result
        assert "histogram" in result

    def test_macd_values_are_floats(self) -> None:
        """Test MACD values are all floats."""
        prices = pd.Series([100.0 + i * 0.5 for i in range(50)])
        result = compute_macd(prices)
        assert isinstance(result["macd"], float)
        assert isinstance(result["signal"], float)
        assert isinstance(result["histogram"], float)

    def test_macd_insufficient_data(self) -> None:
        """Test MACD returns zeros with insufficient data."""
        prices = pd.Series([100.0, 101.0, 102.0])
        result = compute_macd(prices)
        assert result == {"macd": 0.0, "signal": 0.0, "histogram": 0.0}


class TestMarketDataPipeline:
    """Tests for the MarketDataPipeline class."""

    @pytest.fixture
    def mock_client(self) -> MagicMock:
        """Create a mock StockHistoricalDataClient."""
        return MagicMock()

    @pytest.fixture
    def pipeline(self, mock_client: MagicMock) -> MarketDataPipeline:
        """Create a MarketDataPipeline with mocked client."""
        with patch("quant.data.StockHistoricalDataClient", return_value=mock_client):
            pipe = MarketDataPipeline(
                api_key="test_key",
                secret_key="test_secret",
                watchlist=["AAPL", "GOOGL", "MSFT"],
            )
            pipe.client = mock_client
            return pipe

    def test_get_latest_bars_returns_bar_objects(
        self,
        pipeline: MarketDataPipeline,
        mock_client: MagicMock,
    ) -> None:
        """Test get_latest_bars returns dictionary of Bar objects."""
        # Create mock bar data
        mock_bar = MagicMock()
        mock_bar.open = 150.0
        mock_bar.high = 155.0
        mock_bar.low = 149.0
        mock_bar.close = 153.0
        mock_bar.volume = 5000000
        mock_bar.timestamp = datetime.now(timezone.utc)

        mock_response = MagicMock()
        mock_response.data = {"AAPL": [mock_bar]}
        mock_client.get_stock_bars.return_value = mock_response

        result = pipeline.get_latest_bars(tickers=["AAPL"])

        assert "AAPL" in result
        assert isinstance(result["AAPL"], Bar)
        assert result["AAPL"].open == 150.0
        assert result["AAPL"].close == 153.0
        assert result["AAPL"].volume == 5000000

    def test_get_latest_bars_empty_response(
        self,
        pipeline: MarketDataPipeline,
        mock_client: MagicMock,
    ) -> None:
        """Test get_latest_bars handles empty response."""
        mock_response = MagicMock()
        mock_response.data = {}
        mock_client.get_stock_bars.return_value = mock_response

        result = pipeline.get_latest_bars(tickers=["AAPL"])
        assert result == {}

    def test_get_historical_bars_returns_dataframe(
        self,
        pipeline: MarketDataPipeline,
        mock_client: MagicMock,
    ) -> None:
        """Test get_historical_bars returns a DataFrame."""
        # Create mock bar data
        mock_bars = []
        for i in range(10):
            bar = MagicMock()
            bar.open = 150.0 + i
            bar.high = 155.0 + i
            bar.low = 149.0 + i
            bar.close = 153.0 + i
            bar.volume = 5000000
            bar.timestamp = datetime(2024, 1, i + 1, tzinfo=timezone.utc)
            mock_bars.append(bar)

        mock_response = MagicMock()
        mock_response.data = {"AAPL": mock_bars}
        mock_client.get_stock_bars.return_value = mock_response

        result = pipeline.get_historical_bars("AAPL", days=30)

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 10
        assert "close" in result.columns
        assert "volume" in result.columns

    def test_compute_indicators_returns_all_keys(
        self,
        pipeline: MarketDataPipeline,
        mock_client: MagicMock,
    ) -> None:
        """Test compute_indicators returns all expected indicator keys."""
        # Create mock bar data with enough history
        mock_bars = []
        for i in range(60):
            bar = MagicMock()
            bar.open = 150.0 + i * 0.5
            bar.high = 155.0 + i * 0.5
            bar.low = 149.0 + i * 0.5
            bar.close = 153.0 + i * 0.5
            bar.volume = 5000000 + i * 10000
            bar.timestamp = datetime(2024, 1, 1, tzinfo=timezone.utc) + pd.Timedelta(days=i)
            mock_bars.append(bar)

        mock_response = MagicMock()
        mock_response.data = {"AAPL": mock_bars}
        mock_client.get_stock_bars.return_value = mock_response

        result = pipeline.compute_indicators("AAPL")

        expected_keys = [
            "rsi",
            "macd",
            "signal",
            "histogram",
            "sma_20",
            "sma_50",
            "volume_avg_20",
            "volume_ratio",
        ]
        for key in expected_keys:
            assert key in result, f"Missing key: {key}"
            assert isinstance(result[key], float), f"Key {key} is not a float"

    def test_build_context_creates_valid_market_context(
        self,
        pipeline: MarketDataPipeline,
        mock_client: MagicMock,
    ) -> None:
        """Test build_context creates a valid MarketContext."""
        # Create mock bar data
        mock_bar = MagicMock()
        mock_bar.open = 150.0
        mock_bar.high = 155.0
        mock_bar.low = 149.0
        mock_bar.close = 153.0
        mock_bar.volume = 5000000
        mock_bar.timestamp = datetime.now(timezone.utc)

        # Create mock historical data
        mock_bars = []
        for i in range(60):
            bar = MagicMock()
            bar.open = 150.0 + i * 0.5
            bar.high = 155.0 + i * 0.5
            bar.low = 149.0 + i * 0.5
            bar.close = 153.0 + i * 0.5
            bar.volume = 5000000 + i * 10000
            bar.timestamp = datetime(2024, 1, 1, tzinfo=timezone.utc) + pd.Timedelta(days=i)
            mock_bars.append(bar)

        mock_response = MagicMock()
        mock_response.data = {
            "AAPL": mock_bars,
            "GOOGL": mock_bars,
            "MSFT": mock_bars,
        }
        mock_client.get_stock_bars.return_value = mock_response

        # Create test positions
        positions = [
            Position(
                ticker="AAPL",
                quantity=Decimal("100"),
                avg_price=Decimal("150.0"),
                current_price=Decimal("153.0"),
            ),
        ]

        result = pipeline.build_context(
            cash=50000.0,
            positions=positions,
            futures_signal=0.5,
            vix=18.0,
        )

        assert isinstance(result, MarketContext)
        assert result.cash == 50000.0
        assert len(result.positions) == 1
        assert result.futures_signal == 0.5
        assert result.vix == 18.0
        assert isinstance(result.indicators, dict)

    def test_build_context_with_empty_positions(
        self,
        pipeline: MarketDataPipeline,
        mock_client: MagicMock,
    ) -> None:
        """Test build_context works with no positions."""
        mock_response = MagicMock()
        mock_response.data = {}
        mock_client.get_stock_bars.return_value = mock_response

        result = pipeline.build_context(
            cash=100000.0,
            positions=[],
        )

        assert isinstance(result, MarketContext)
        assert result.cash == 100000.0
        assert len(result.positions) == 0
        assert result.futures_signal == 0.0
        assert result.vix == 20.0
