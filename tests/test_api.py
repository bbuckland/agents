"""Tests for the FastAPI server."""

from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def mock_settings() -> MagicMock:
    """Create mock settings."""
    settings = MagicMock()
    settings.alpaca_api_key = "test_key"
    settings.alpaca_secret_key = "test_secret"
    settings.alpaca_base_url = "https://paper-api.alpaca.markets"
    settings.database_url = "postgresql://test:test@localhost/test"
    settings.redis_url = "redis://localhost:6379"
    settings.base_reserve = 1000
    settings.max_position_size = 1000
    settings.confidence_threshold = 70
    return settings


@pytest.fixture
def client(mock_settings: MagicMock) -> TestClient:
    """Create test client with mocked dependencies."""
    with patch("quant.api.get_settings", return_value=mock_settings):
        from quant.api import app

        yield TestClient(app)


class TestHealthEndpoint:
    """Tests for health endpoint."""

    def test_health_returns_ok(self, client: TestClient) -> None:
        """Health endpoint should return ok status."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["version"] == "0.1.0"


class TestAnalyzeEndpoint:
    """Tests for analyze endpoint."""

    def test_analyze_returns_recommendations(
        self, client: TestClient, mock_settings: MagicMock
    ) -> None:
        """Analyze endpoint should return recommendations."""
        with patch("quant.api.get_broker") as mock_get_broker:
            mock_broker = MagicMock()
            mock_broker.get_account.return_value = MagicMock(
                cash=Decimal("2000"),
                equity=Decimal("2000"),
                buying_power=Decimal("4000"),
            )
            mock_broker.get_positions.return_value = []
            mock_get_broker.return_value = mock_broker

            with patch("quant.api.get_data_pipeline") as mock_get_pipeline:
                from quant.models import MarketContext

                mock_pipeline = MagicMock()
                mock_pipeline.build_context.return_value = MarketContext(
                    cash=Decimal("2000"),
                    positions=[],
                    futures_signal=0.0,
                    indicators={},
                )
                mock_get_pipeline.return_value = mock_pipeline

                with patch("quant.api.get_engine") as mock_get_engine:
                    mock_engine = MagicMock()
                    mock_engine.analyze.return_value = []
                    mock_get_engine.return_value = mock_engine

                    response = client.post("/analyze")

                    assert response.status_code == 200
                    data = response.json()
                    assert "recommendations" in data
                    assert "market_context" in data
                    assert isinstance(data["recommendations"], list)

    def test_analyze_handles_errors(self, client: TestClient) -> None:
        """Analyze endpoint should handle errors gracefully."""
        with patch("quant.api.get_broker") as mock_get_broker:
            mock_get_broker.side_effect = Exception("Connection failed")

            response = client.post("/analyze")

            assert response.status_code == 500
            assert "Connection failed" in response.json()["detail"]


class TestExecuteEndpoint:
    """Tests for execute endpoint."""

    def test_execute_submits_order(self, client: TestClient) -> None:
        """Execute endpoint should submit market order."""
        with patch("quant.api.get_broker") as mock_get_broker:
            mock_broker = MagicMock()
            mock_broker.submit_market_order.return_value = MagicMock(
                order_id="order-123",
                status="accepted",
                ticker="AAPL",
                quantity=Decimal("5"),
                notional=Decimal("900"),
            )
            mock_get_broker.return_value = mock_broker

            response = client.post(
                "/execute",
                json={"ticker": "AAPL", "size": 900.0, "side": "buy"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["order_id"] == "order-123"
            assert data["status"] == "accepted"
            assert data["ticker"] == "AAPL"

    def test_execute_handles_sell_side(self, client: TestClient) -> None:
        """Execute endpoint should handle sell orders."""
        with patch("quant.api.get_broker") as mock_get_broker:
            from quant.broker import OrderSide

            mock_broker = MagicMock()
            mock_broker.submit_market_order.return_value = MagicMock(
                order_id="order-456",
                status="accepted",
                ticker="AAPL",
                quantity=Decimal("5"),
                notional=Decimal("900"),
            )
            mock_get_broker.return_value = mock_broker

            response = client.post(
                "/execute",
                json={"ticker": "AAPL", "size": 900.0, "side": "sell"},
            )

            assert response.status_code == 200
            # Verify sell side was passed
            call_args = mock_broker.submit_market_order.call_args
            assert call_args.kwargs["side"] == OrderSide.SELL


class TestPositionsEndpoint:
    """Tests for positions endpoint."""

    def test_get_positions_returns_list(self, client: TestClient) -> None:
        """Positions endpoint should return position list."""
        with patch("quant.api.get_broker") as mock_get_broker:
            from quant.models import Position

            mock_broker = MagicMock()
            mock_broker.get_positions.return_value = [
                Position(
                    ticker="AAPL",
                    quantity=Decimal("10"),
                    avg_price=Decimal("180.00"),
                    current_price=Decimal("185.00"),
                )
            ]
            mock_get_broker.return_value = mock_broker

            response = client.get("/positions")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["ticker"] == "AAPL"
            assert data[0]["quantity"] == 10.0


class TestAccountEndpoint:
    """Tests for account endpoint."""

    def test_get_account_returns_info(self, client: TestClient) -> None:
        """Account endpoint should return account info."""
        with patch("quant.api.get_broker") as mock_get_broker:
            mock_broker = MagicMock()
            mock_broker.get_account.return_value = MagicMock(
                cash=Decimal("2500.00"),
                equity=Decimal("3200.00"),
                buying_power=Decimal("5000.00"),
            )
            mock_get_broker.return_value = mock_broker

            response = client.get("/account")

            assert response.status_code == 200
            data = response.json()
            assert data["cash"] == 2500.0
            assert data["equity"] == 3200.0
            assert data["buying_power"] == 5000.0
