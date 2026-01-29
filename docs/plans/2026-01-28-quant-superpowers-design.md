# Quant Superpowers — System Design

**Date:** 2026-01-28
**Status:** Draft
**Goal:** Turn $2,000 into $100k over a year (stretch: 5-10x realistic, 50x moonshot)

---

## Overview

An automated trading system that uses quantitative analysis, news sentiment, and social signals to make daily trading decisions across three asset classes:

1. **F100 Core** — Fortune 100 stocks, low risk, primary strategy
2. **Discovery Agent** — Mid-cap momentum plays, high risk, separate budget
3. **Crypto** — BTC/ETH/SOL, medium risk, separate budget

All communication flows through **Moltbot** (molt.bot). A **performance dashboard** provides analytics and trade history.

---

## Core Principles

- Never risk base capital ($1,000 floor is untouchable)
- Every trade has documented rationale and confidence score
- Strategy is consistent and versioned in the Quant Guide
- Tournament system validates strategies before live deployment
- Start with manual approval, evolve to autonomous

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                          MOLTBOT                                │
│              (Communication & Interaction Layer)                │
│         Morning briefs • Trade approvals • Alerts               │
├─────────────────────────────────────────────────────────────────┤
│                    PERFORMANCE DASHBOARD                        │
│                        (Vercel)                                 │
│           Analytics • Trade journal • Agent comparison          │
├─────────────────────────────────────────────────────────────────┤
│                      DECISION ENGINE                            │
│                       (Hetzner/Python)                          │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                   Strategy Runner                        │   │
│  │    Load strategies • Run signals • Score confidence      │   │
│  ├──────────────┬──────────────┬──────────────┬───────────┤   │
│  │   F100 Core  │  Discovery   │    Crypto    │  Future   │   │
│  │   10 stocks  │   Scanner    │   BTC/ETH/SOL│  Agents   │   │
│  │   Low risk   │  High risk   │   Med risk   │           │   │
│  │   Budget: $1k│  Budget: $500│  Budget: $500│           │   │
│  └──────────────┴──────────────┴──────────────┴───────────┘   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                   Risk Manager                           │   │
│  │   Position limits • Stop-losses • Circuit breakers       │   │
│  │   BASE RESERVE $1000 — UNTOUCHABLE                       │   │
│  └─────────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────────┤
│                      DATA PIPELINE                              │
│  Market Data    News/Sentiment    Social         On-Chain      │
│  (Alpaca)       (Polygon)         (X/Reddit)     (Glassnode)   │
├─────────────────────────────────────────────────────────────────┤
│                    EXECUTION LAYER                              │
│              Alpaca (Stocks)    Coinbase (Crypto)              │
├─────────────────────────────────────────────────────────────────┤
│                     TOURNAMENT SYSTEM                           │
│        10 strategies • 20 datasets • Nightly validation        │
└─────────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology | Why |
|-------|------------|-----|
| Quant Engine | Python | pandas, numpy, backtesting libraries, ML ecosystem |
| API Layer | TypeScript | Webhooks, Moltbot integration, dashboard backend |
| Database | PostgreSQL | Trade history, signals, performance metrics |
| Cache | Redis | Real-time data caching |
| Dashboard | Vercel | Fast deployment, cheap, easy |
| Quant Hosting | Hetzner | Cost-effective compute for backtesting |
| Communication | Moltbot | Existing personal AI, multi-channel |

---

## Capital Structure

```
TOTAL STARTING CAPITAL: $2,000

├── Base Reserve: $1,000 (UNTOUCHABLE)
│   • Hard-coded floor that cannot be spent
│   • Grows as 50% of profits are added
│
└── Trading Capital: $1,000 (at risk)
    │
    ├── F100 Core: $1,000 (primary)
    │   • Fortune 100 stocks
    │   • Low risk, proven strategies
    │
    ├── Discovery: $500 (funded from F100 profits)
    │   • Mid-cap momentum plays
    │   • High risk, separate budget
    │   • Starts at $0, funded when F100 profits reach $500
    │
    └── Crypto: $500 (funded from F100 profits)
        • BTC, ETH, SOL only
        • Medium risk, separate budget
        • Starts at $0, funded when F100 profits reach $1000
```

**Profit allocation:**
- 50% reinvested into trading capital
- 50% added to base reserve (raises the untouchable floor)

---

## Strategy Module Interface

Every strategy implements this contract:

```python
from typing import Protocol
from dataclasses import dataclass
from pandas import DataFrame

@dataclass
class Signal:
    ticker: str
    action: str  # "buy", "sell", "hold"
    size: float
    confidence: float  # 0-100
    rationale_tags: list[str]
    stop_loss: float
    take_profit: float
    explanation: str

@dataclass
class BacktestResult:
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    profit_factor: float
    trades: list[dict]

class Strategy(Protocol):
    name: str
    version: str
    description: str

    def analyze(self, context: MarketContext) -> list[Signal]:
        """Analyze market and return trade signals."""
        ...

    def explain(self, signal: Signal) -> str:
        """Human-readable explanation for Moltbot to present."""
        ...

    def backtest(self, historical: DataFrame) -> BacktestResult:
        """Run strategy against historical data."""
        ...
```

**MarketContext contains:**
- Current positions and cash
- Today's pre-market data (futures, overnight moves)
- News sentiment scores for watchlist stocks
- Technical indicators (pre-computed)
- Social sentiment from X/Reddit

---

## Data Pipeline

### Sources

| Stream | Source | Cost | Data |
|--------|--------|------|------|
| Market Data | Alpaca | Free | OHLCV, real-time quotes |
| Futures/Macro | Yahoo Finance | Free | ES futures, VIX, 10Y yield |
| News Sentiment | Polygon.io | ~$30/mo | Headlines, sentiment scores |
| Social Sentiment | X API + Reddit | ~$20/mo | Mention volume, polarity |
| Options Flow | Unusual Whales | ~$30/mo | Smart money signals (Discovery) |
| On-Chain | Glassnode | ~$30/mo | Crypto metrics |

**Total data budget: ~$80-110/month**

### Schedule

```
4:00 AM ET  - Overnight news digest
6:00 AM ET  - Futures snapshot, pre-market movers
9:00 AM ET  - Final pre-market sentiment refresh
9:30 AM ET  - Market open, real-time mode
4:00 PM ET  - EOD summary, position reconciliation
6:00 PM ET  - Crypto overnight setup check
```

### Computed Indicators

- RSI (14-period)
- MACD (12, 26, 9)
- Bollinger Bands (20, 2)
- VWAP
- ATR (14-period)
- 20/50/200 day moving averages
- Volume vs 20-day average

---

## F100 Core Watchlist

| Ticker | Company | Sector | Why Included |
|--------|---------|--------|--------------|
| AAPL | Apple | Tech | Ultimate liquidity, clean trends |
| NVDA | NVIDIA | Semiconductors | Volatility sweet spot, momentum |
| META | Meta | Tech | High beta, sentiment-driven |
| MSFT | Microsoft | Tech | Liquid, steadier than peers |
| AMZN | Amazon | Consumer/Cloud | Good range, news catalysts |
| GOOGL | Alphabet | Tech | Liquid, moderate volatility |
| TSLA | Tesla | Auto/Tech | High volatility, social sentiment |
| JPM | JPMorgan | Finance | Sector diversity, macro sensitive |
| XOM | Exxon | Energy | Non-tech diversity, oil correlation |
| UNH | UnitedHealth | Healthcare | Defensive diversity, steady mover |

**Selection criteria:**
- High liquidity (>10M daily volume)
- Volatility sweet spot (moves enough to profit, not erratic)
- Fortune 100 membership
- Sector diversification (6 tech, 1 finance, 1 energy, 1 healthcare)

---

## Risk Management

### Hard Limits (Code-Enforced)

```python
class RiskManager:
    # Position limits
    MAX_POSITION_SIZE = 1000        # Never more than $1000 per stock
    MAX_CONCURRENT_POSITIONS = 5    # Max 5 open positions

    # Daily limits
    MAX_DAILY_LOSS = 200            # Stop trading if down $200 in a day

    # Portfolio limits
    MAX_PORTFOLIO_RISK = 0.50       # Never risk more than 50% of trading capital
    RESERVE_FLOOR = 1000            # Cannot touch base reserve

    def can_trade(self, account: Account) -> bool:
        available = account.equity - self.RESERVE_FLOOR
        return available > 0 and not self.daily_loss_exceeded()
```

### Position Sizing

| Confidence | Base Size | Conditions |
|------------|-----------|------------|
| 90%+ | $1,000 | All signals aligned |
| 80-89% | $800 | Strong conviction |
| 70-79% | $600 | Standard trade |
| <70% | Skip | Below threshold |

**Scale down when:**
- Drawdown >10%
- Losing streak >3 trades
- VIX >25

**Scale up when:**
- Winning streak >3
- Confidence >85%
- VIX <15

### Circuit Breakers

| Trigger | Action |
|---------|--------|
| 3 consecutive losses | Pause 24 hours, require manual override |
| Daily loss limit hit | No new positions until next day |
| Account at reserve floor | Full stop, manual review required |
| Strategy drawdown >20% | Pause strategy, flag for tournament review |

---

## Discovery Agent

High-risk scanner for opportunities outside the F100 watchlist.

### What It Searches For

- Momentum breakouts in mid-cap stocks ($1B-$50B market cap)
- Unusual options activity (smart money signals)
- Social sentiment spikes before mainstream
- SEC filings (insider buys, 13F changes)
- Earnings whisper plays

### Risk Controls (Stricter Than F100)

```python
class DiscoveryRiskManager(RiskManager):
    MAX_POSITION_SIZE = 250         # Smaller bets
    MIN_CONFIDENCE = 80             # Higher bar
    MIN_MARKET_CAP = 1_000_000_000  # $1B minimum
    MIN_SHARE_PRICE = 5.00          # No penny stocks
    BUDGET_CAP = 500                # Separate budget
    PAUSE_ON_DRAWDOWN = 0.50        # Pause if 50% of budget lost
```

### Signal Format

```
DISCOVERY ALERT — High Risk

PLTR (Palantir) — BUY — 82% confidence
Category: Momentum breakout + unusual call activity

WHY THIS SURFACED:
• Broke 52-week high on 2.3x volume
• $2.1M in call options flow (Jan expiry, $25 strike)
• Reddit mention velocity +340% (24h)
• No negative news catalysts

RISK DISCLOSURE:
• Not in core watchlist — less historical data
• Higher volatility expected (ATR: 4.2%)
• Discovery budget allocation: $250 of $500

Approve risky play? (Y/N)
```

---

## Crypto Strategy

### Asset Coverage (Start Small)

| Asset | Why |
|-------|-----|
| BTC | Market leader, must-have |
| ETH | Different use case, DeFi exposure |
| SOL | High volatility, momentum plays |

### Key Differences From Stocks

- 24/7 market (different timing)
- Higher volatility (smaller positions)
- Different sentiment sources (Crypto Twitter, on-chain)
- Different broker (Coinbase Pro API)

### Risk Controls

```python
class CryptoRiskManager(RiskManager):
    MAX_POSITION_SIZE = 500         # Half of stock positions
    MAX_PORTFOLIO_RISK = 0.25       # Max 25% of trading capital
    STOP_LOSS_PERCENT = 0.05        # Wider stops (5%) for volatility

    # Crypto-specific
    FEAR_GREED_NO_BUY_LOW = 20      # Don't buy in extreme fear
    FEAR_GREED_NO_BUY_HIGH = 80     # Don't buy in extreme greed
```

### Signal Timing

- 6:00 AM ET — Morning briefing (with stocks)
- 6:00 PM ET — Evening check for overnight setup
- Intraday alerts on >5% moves

---

## Tournament System

Validates strategies before they touch real money.

### Structure

```
tournament/
├── strategies/           # 10 competing strategies
│   ├── momentum_breakout.py
│   ├── mean_reversion.py
│   ├── sentiment_momentum.py
│   ├── gap_fade.py
│   ├── vwap_reversion.py
│   ├── earnings_drift.py
│   ├── sector_rotation.py
│   ├── volatility_contraction.py
│   ├── news_catalyst.py
│   └── multi_factor.py
├── datasets/             # 20 market scenarios
│   ├── bull_2017.parquet
│   ├── bull_2021.parquet
│   ├── bear_2022.parquet
│   ├── bear_2008.parquet
│   ├── sideways_2015.parquet
│   ├── sideways_2019.parquet
│   ├── covid_crash_2020.parquet
│   ├── covid_recovery_2020.parquet
│   ├── flash_crash_2010.parquet
│   ├── volatility_spike_2018.parquet
│   └── ... (10 more scenarios)
└── results/
    └── tournament_YYYY_MM_DD.json
```

### Anti-Overfitting Measures

1. **Walk-forward validation** — Train on first 60%, test on last 40%
2. **Random entry points** — Don't always start at dataset beginning
3. **Out-of-sample holdout** — Some datasets never seen during development
4. **Parameter stability** — Small param changes shouldn't destroy performance
5. **Cross-regime validation** — Must perform in both bull AND bear markets

### Scoring Criteria

| Metric | Weight | Why |
|--------|--------|-----|
| Sharpe Ratio | 30% | Reward consistency, not just gains |
| Max Drawdown | 25% | Capital preservation |
| Win Rate | 20% | Confidence in signals |
| Profit Factor | 15% | Ratio of gains to losses |
| Regime Stability | 10% | Works across market conditions |

### Tournament Schedule

- **Nightly:** Run on any strategy changes
- **Weekly:** Full tournament with all strategies and datasets
- **On-demand:** Before promoting a strategy to live

---

## Daily Workflow

### Pre-Market (6:00 - 9:30 AM ET)

Moltbot delivers the morning briefing with full rationale:

```
Good morning. Here's today's analysis:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MARKET CONTEXT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• S&P futures: +0.3% (mildly bullish)
• VIX: 18 (normal range)
• 10Y yield: 4.2% (stable)
• Notable: NVDA earnings after close tomorrow

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RECOMMENDATION #1: AAPL — BUY — 78% Confidence
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TECHNICAL (weight: 40%)
• Price broke above 20-day resistance at $182.50
• RSI: 58 (healthy momentum, not overbought)
• Volume: 1.4x average (confirms breakout)
• MACD: bullish crossover 2 days ago, continuing

SENTIMENT (weight: 35%)
• News: 4 positive articles, 0 negative (24h)
  - "Apple supplier raises guidance"
  - "iPhone demand strong in China"
• X/Twitter: +12% mention volume, 0.72 polarity

MACRO (weight: 25%)
• Sector (XLK): +0.8% pre-market, outperforming
• Futures context supports risk-on
• VIX favorable for momentum plays

RISK ASSESSMENT
• Entry: $183.20 (current ask)
• Stop-loss: $177.70 (-3%)
• Take-profit: $192.36 (+5%)
• Risk/reward: 1:1.67
• Position size: $800

STRATEGY: momentum_sentiment_v2

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RECOMMENDATION #2: META — BUY — 72% Confidence
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Full rationale...]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Proposed: Buy $800 AAPL, $600 META
Total exposure: $1,400
Stop-loss risk: $84 (6% of positions)

Approve / Modify / Skip all?
```

### Response Options (Mode 1 - Manual)

| Response | Action |
|----------|--------|
| "Approve" | Execute all recommendations |
| "Just AAPL" | Execute only AAPL trade |
| "AAPL at $750" | Modify position size |
| "Skip" | No trades today |
| "Why META?" | More detail (already shown by default) |

### During Market Hours

- System monitors positions against stop-loss/take-profit
- Alerts on triggered exits or significant moves
- Can query "How's AAPL doing?" anytime

### Post-Market (4:00 PM ET)

```
End of day summary:

CLOSED POSITIONS
• NVDA: Sold at $485.20 (+4.2%) — Take-profit triggered
  Profit: $42.00

OPEN POSITIONS
• AAPL: $184.10 (+0.5%) — Holding
• META: $312.40 (+1.2%) — Holding

TODAY'S P&L: +$62.40
PORTFOLIO VALUE: $2,062.40
BASE RESERVE: $1,000.00 (protected)
```

---

## Moltbot Integration

The quant system integrates with Moltbot via webhooks.

### Architecture

```
Quant Engine (Hetzner)
       │
       │ POST /signals
       ▼
TypeScript API (Vercel)
       │
       │ Webhook
       ▼
    Moltbot ─────► Your preferred channel
       │           (WhatsApp/Telegram/iMessage/etc)
       │
       │ Your reply
       ▼
TypeScript API
       │
       │ POST /execute
       ▼
Quant Engine ───► Alpaca/Coinbase
```

### Moltbot Responsibilities

- Route messages to your preferred channel
- Parse natural language responses ("skip AAPL", "approve all")
- Maintain conversation context
- Remember your preferences

### Quant System Responsibilities

- Generate signals and full rationale
- Execute trades via broker APIs
- Enforce risk limits
- Track positions and P&L

---

## Performance Dashboard

Unified view across all agents, deployed on Vercel.

### Sections

**Portfolio Overview**
- Total value, base reserve status
- Today/MTD/YTD performance
- Breakdown by agent (F100, Discovery, Crypto)

**Agent Performance**
- Return, win rate, Sharpe, max drawdown per agent
- Timeframe filters (30D, 90D, YTD, All)
- Agent comparison charts

**Trade Journal**
- Every trade with full rationale
- Filterable by agent, ticker, date, outcome
- Searchable

**Strategy Analytics**
- Active strategy performance
- Confidence calibration (are 80% trades winning 80%?)
- Signal type accuracy breakdown
- Tournament results history

**Risk Monitor**
- Current exposure by agent
- Distance to circuit breakers
- Drawdown visualization

---

## Quant Guide

Lives at `docs/quant-guide.md` — the canonical source of trading rules.

```markdown
# Quant Guide v1.0

## Core Principles
- Never risk base capital ($1000 floor)
- Maximum position size: $1000 per stock
- Maximum concurrent positions: 5
- Minimum confidence threshold: 70%

## Watchlist
[Table of 10 F100 stocks]

## Entry Criteria
- At least 2 of 3 signal types must align
- No entry within 2 days of earnings
- No entry when VIX > 30

## Exit Rules
- Stop-loss: 3% below entry
- Take-profit: 5% above entry
- Time stop: Exit if flat after 3 days

## Active Strategy
- Current: [tournament winner]
- Metrics: [from tournament]

## Change Log
- [Dated entries for all changes]
```

Claude reads this before every analysis. Changes are version-controlled.

---

## Evolution Path

### Phase 1: Foundation (Weeks 1-4)
- Set up infrastructure (Hetzner, Vercel, databases)
- Build data pipeline
- Implement 3 core strategies
- Run tournament with historical data
- Paper trade on Alpaca

### Phase 2: Live Trading (Weeks 5-8)
- Go live with F100 Core (Mode 1 - manual approval)
- Refine based on real performance
- Build remaining 7 tournament strategies
- Implement full dashboard

### Phase 3: Expansion (Weeks 9-12)
- Fund Discovery agent from F100 profits
- Fund Crypto agent
- Move to Mode 2 (exception-based)
- Add ensemble voting (Approach B)

### Phase 4: Optimization (Ongoing)
- Continuous tournament validation
- Strategy evolution
- Consider options via Schwab
- Scale capital as system proves itself

---

## Appendix: The 10 Tournament Strategies

1. **momentum_breakout** — Buy on price/volume breakouts above resistance
2. **mean_reversion** — Fade extended moves, buy oversold, sell overbought
3. **sentiment_momentum** — Trade in direction of news/social sentiment
4. **gap_fade** — Fade overnight gaps that are likely to fill
5. **vwap_reversion** — Trade back toward VWAP after extended deviations
6. **earnings_drift** — Ride post-earnings momentum (after initial reaction)
7. **sector_rotation** — Rotate into strongest sectors, out of weakest
8. **volatility_contraction** — Enter on volatility squeeze, ride expansion
9. **news_catalyst** — Trade specific news events (FDA, earnings, M&A)
10. **multi_factor** — Combine technical + sentiment + macro signals

---

## Appendix: The 20 Tournament Datasets

**Bull Markets:**
1. 2017 steady climb
2. 2019 recovery
3. 2020 post-COVID rally
4. 2021 meme stock era

**Bear Markets:**
5. 2008 financial crisis
6. 2022 inflation/rate hikes
7. 2018 Q4 selloff
8. 2020 COVID crash

**Sideways/Choppy:**
9. 2015 range-bound
10. 2011 debt ceiling
11. 2018 H1
12. 2023 H1

**High Volatility Events:**
13. Flash crash 2010
14. VIX spike Feb 2018
15. COVID initial shock March 2020
16. SVB collapse March 2023

**Sector-Specific:**
17. Tech bubble burst 2000
18. Energy crisis 2014
19. Crypto correlation 2022
20. AI rally 2023

---

*Document version: 1.0*
*Last updated: 2026-01-28*
