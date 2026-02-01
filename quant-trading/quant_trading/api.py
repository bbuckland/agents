"""FastAPI server for the quant engine."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from decimal import Decimal
from functools import lru_cache
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from quant_trading.broker import AlpacaClient, OrderSide
from quant_trading.config import Settings
from quant_trading.data import MarketDataPipeline
from quant_trading.engine import DecisionEngine
from quant_trading.risk import RiskManager
from quant_trading.strategies import MomentumBreakoutStrategy
from quant_trading.strategy import StrategyRegistry

# Watchlist - Fortune 100 high liquidity + volatility sweet spot
WATCHLIST = [
    "AAPL", "NVDA", "META", "MSFT", "AMZN",
    "GOOGL", "TSLA", "JPM", "XOM", "UNH",
]


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


@lru_cache
def get_broker() -> AlpacaClient:
    """Get cached broker client."""
    settings = get_settings()
    return AlpacaClient(
        api_key=settings.alpaca_api_key.get_secret_value(),
        secret_key=settings.alpaca_secret_key.get_secret_value(),
        paper=True,
    )


@lru_cache
def get_data_pipeline() -> MarketDataPipeline:
    """Get cached data pipeline."""
    settings = get_settings()
    return MarketDataPipeline(
        api_key=settings.alpaca_api_key.get_secret_value(),
        secret_key=settings.alpaca_secret_key.get_secret_value(),
        watchlist=WATCHLIST,
    )


@lru_cache
def get_engine() -> DecisionEngine:
    """Get cached decision engine."""
    settings = get_settings()

    # Set up strategy registry
    registry = StrategyRegistry()
    registry.register(MomentumBreakoutStrategy())

    # Set up risk manager
    risk_manager = RiskManager(
        base_reserve=Decimal(settings.base_reserve),
        max_position_size=Decimal(settings.max_position_size),
        max_concurrent_positions=5,
        max_daily_loss=Decimal("200"),
    )

    return DecisionEngine(
        registry=registry,
        risk_manager=risk_manager,
        active_strategy="momentum_breakout",
        confidence_threshold=settings.confidence_threshold,
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan handler."""
    # Startup
    yield
    # Shutdown - clear caches
    get_broker.cache_clear()
    get_data_pipeline.cache_clear()
    get_engine.cache_clear()
    get_settings.cache_clear()


app = FastAPI(
    title="Quant Superpowers API",
    description="Quantitative trading engine with tournament-validated strategies",
    version="0.1.0",
    lifespan=lifespan,
)


# Response models
class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str


class RecommendationResponse(BaseModel):
    """Single recommendation in response."""

    ticker: str
    action: str
    size: float
    confidence: int
    approved: bool
    rejection_reason: str | None
    entry_price: float | None
    stop_loss: float | None
    take_profit: float | None
    explanation: str | None


class AnalyzeResponse(BaseModel):
    """Response from analyze endpoint."""

    recommendations: list[RecommendationResponse]
    market_context: dict[str, Any]


class ExecuteRequest(BaseModel):
    """Request to execute a trade."""

    ticker: str
    size: float
    side: str = "buy"


class ExecuteResponse(BaseModel):
    """Response from execute endpoint."""

    order_id: str
    status: str
    ticker: str
    size: float


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(status="ok", version="0.1.0")


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze() -> AnalyzeResponse:
    """Run analysis and return recommendations."""
    try:
        broker = get_broker()
        pipeline = get_data_pipeline()
        engine = get_engine()

        # Get current account state
        account = broker.get_account()
        positions = broker.get_positions()

        # Build market context
        context = pipeline.build_context(
            cash=float(account.cash),
            positions=positions,
        )

        # Run analysis
        recommendations = engine.analyze(context)

        return AnalyzeResponse(
            recommendations=[
                RecommendationResponse(
                    ticker=r.signal.ticker,
                    action=r.signal.action.value,
                    size=float(r.adjusted_size or r.signal.size),
                    confidence=r.signal.confidence,
                    approved=r.approved,
                    rejection_reason=r.rejection_reason,
                    entry_price=float(r.signal.entry_price) if r.signal.entry_price else None,
                    stop_loss=float(r.signal.stop_loss) if r.signal.stop_loss else None,
                    take_profit=float(r.signal.take_profit) if r.signal.take_profit else None,
                    explanation=r.signal.explanation,
                )
                for r in recommendations
            ],
            market_context={
                "cash": float(context.cash),
                "equity": float(context.total_equity),
                "position_count": len(context.positions),
                "vix": context.vix,
                "futures_signal": context.futures_signal,
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/execute", response_model=ExecuteResponse)
async def execute_trade(request: ExecuteRequest) -> ExecuteResponse:
    """Execute a trade for a given ticker."""
    try:
        broker = get_broker()

        side = OrderSide.BUY if request.side.lower() == "buy" else OrderSide.SELL

        order = broker.submit_market_order(
            ticker=request.ticker,
            side=side,
            notional=Decimal(str(request.size)),
        )

        return ExecuteResponse(
            order_id=order.order_id,
            status=order.status,
            ticker=order.ticker,
            size=request.size,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/positions")
async def get_positions() -> list[dict[str, Any]]:
    """Get current positions."""
    try:
        broker = get_broker()
        positions = broker.get_positions()

        return [
            {
                "ticker": p.ticker,
                "quantity": float(p.quantity),
                "avg_price": float(p.avg_price),
                "current_price": float(p.current_price) if p.current_price else None,
                "market_value": float(p.market_value) if p.market_value else None,
                "unrealized_pnl": float(p.unrealized_pnl) if p.unrealized_pnl else None,
            }
            for p in positions
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/account")
async def get_account() -> dict[str, Any]:
    """Get account information."""
    try:
        broker = get_broker()
        account = broker.get_account()

        return {
            "cash": float(account.cash),
            "equity": float(account.equity),
            "buying_power": float(account.buying_power),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
