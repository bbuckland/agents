# Code Critique Findings

**Date:** 2026-01-28
**Reviewed by:** 7 independent AI agents (4 completed, 3 hit rate limits)

---

## Summary

Phase 1 implementation has **122 passing tests** (up from 101) after fixing all critical issues identified by code review agents.

---

## Fixed Issues

| Issue | Fixed In | Commit |
|-------|----------|--------|
| RSI Score Inverted | Task 1 | `9da4bea` fix: correct RSI score calculation to reward strong momentum |
| Bad Data Defaults | Task 2 | `b0dc25c` fix: validate indicators exist before generating signals |
| No Order Validation | Task 3 | `1116775` fix: validate order inputs to prevent bad orders |
| No Error Handling | Task 4 | `392e0ee` fix: add error handling to broker client |
| Secrets Exposure | Task 5 | `407070f` fix: protect API keys with SecretStr |
| No Thread Safety | Task 6 | `b581253` fix: add thread safety to strategy registry |

**Tests Added:** 21 new tests covering:
- RSI confidence scoring (3 tests)
- Missing indicator handling (4 tests)
- Order validation (5 tests)
- Broker error handling (4 tests)
- Secret protection (3 tests)
- Thread safety (2 tests)

---

## Critical Issues (Must Fix) - ALL RESOLVED

### 1. Config Module - Secrets Exposure

**File:** `src/quant/config.py:19-20, 24-25`

```python
# WRONG - secrets will appear in logs/errors
alpaca_api_key: str
alpaca_secret_key: str
database_url: str  # Contains credentials

# SHOULD BE
from pydantic import SecretStr
alpaca_api_key: SecretStr
alpaca_secret_key: SecretStr
```

**Impact:** API keys and database credentials will be printed in error messages, stack traces, and logs.

---

### 2. Strategy Registry - No Thread Safety

**File:** `src/quant/strategy.py:64-106`

```python
# WRONG - race conditions under concurrent access
def register(self, strategy: Strategy) -> None:
    self._strategies[strategy.name] = strategy

# SHOULD HAVE
import threading
self._lock = threading.RLock()

def register(self, strategy: Strategy) -> None:
    with self._lock:
        self._strategies[strategy.name] = strategy
```

**Impact:** Will crash in production under concurrent load.

---

### 3. Broker Client - No Error Handling

**File:** `src/quant/broker.py:66, 79, 132, 153`

```python
# WRONG - unhandled API failures crash the process
def get_account(self) -> AccountInfo:
    account = self._client.get_account()  # Can throw!

# SHOULD HAVE
def get_account(self) -> AccountInfo:
    try:
        account = self._client.get_account()
    except Exception as e:
        logger.error(f"Failed to get account: {e}")
        raise BrokerError("Failed to fetch account") from e
```

**Impact:** Network failures, rate limits, or API errors will crash the entire system.

---

### 4. Broker Client - No Order Validation

**File:** `src/quant/broker.py:90-96`

```python
# WRONG - accepts negative quantities
def submit_market_order(
    self,
    ticker: str,
    side: OrderSide,
    notional: Decimal | None = None,
    quantity: Decimal | None = None,
) -> OrderResult:
    # No validation!

# SHOULD HAVE
if notional is not None and notional <= 0:
    raise ValueError("Notional must be positive")
if quantity is not None and quantity <= 0:
    raise ValueError("Quantity must be positive")
```

**Impact:** Could execute incorrect or reversed orders.

---

### 5. Momentum Strategy - RSI Score Inverted

**File:** `src/quant/strategies/momentum_breakout.py:109`

```python
# WRONG - penalizes strong momentum
rsi_score = (70 - rsi) / 70 * 25 if rsi < 70 else 0
# RSI 30 → 14.3 points (weak signal gets high score)
# RSI 65 → 1.8 points (strong signal gets low score)

# SHOULD BE (reward momentum in 40-70 range)
if 40 <= rsi < 70:
    rsi_score = ((rsi - 40) / 30) * 25  # Higher RSI = higher score
else:
    rsi_score = 0
```

**Impact:** Strategy actively avoids the best momentum signals.

---

### 6. Momentum Strategy - Bad Data Defaults

**File:** `src/quant/strategies/momentum_breakout.py:35-39`

```python
# WRONG - generates signals on missing data
price = float(indicators.get("price", 0.0))  # Missing = $0!
sma20 = float(indicators.get("sma20", 0.0))  # Missing = $0!

# With these defaults:
# breakout = price > sma20 → True if price > 0 and sma20 missing!

# SHOULD BE
required = ["price", "sma20", "volume_ratio", "rsi", "macd_histogram"]
if not all(k in indicators for k in required):
    return None  # Skip this ticker
```

**Impact:** Generates buy signals on tickers with missing or corrupt data.

---

## High Priority Issues (Should Fix)

### 7. Decimal to Float Conversion

**File:** `src/quant/broker.py:127, 129`

```python
# Loses precision on monetary values
request_params["notional"] = float(notional)
```

**Fix:** Pass as string or keep as Decimal if API supports it.

---

### 8. Hardcoded Stop Loss / Take Profit

**File:** `src/quant/strategies/momentum_breakout.py:57-60`

```python
stop_loss = entry_price * Decimal("0.97")   # Fixed 3%
take_profit = entry_price * Decimal("1.05") # Fixed 5%
```

**Fix:** Scale with ATR (volatility) and confidence score.

---

### 9. No Async Support in Strategy Protocol

**File:** `src/quant/strategy.py:27-58`

All methods are synchronous, blocking the event loop.

**Fix:** Add async variants or use thread pool for CPU-bound analysis.

---

### 10. Silent Strategy Overwrites

**File:** `src/quant/strategy.py:68-74`

```python
def register(self, strategy: Strategy) -> None:
    self._strategies[strategy.name] = strategy  # Silent overwrite!
```

**Fix:** Log warning or raise error on duplicate registration.

---

## Medium Priority Issues

| Issue | File | Fix |
|-------|------|-----|
| No URL validation | config.py:21,24,25 | Use Pydantic `HttpUrl`, `PostgresDsn` |
| Confidence truncation | momentum_breakout.py:118 | Use `round()` not `int()` |
| No lifecycle hooks | strategy.py | Add `initialize()`, `cleanup()` methods |
| Backtest is a stub | momentum_breakout.py:151-171 | Raise `NotImplementedError` |
| Close position unverified | broker.py:153-156 | Check returned quantity |

---

## Test Coverage Gaps

- ~~No tests for API failures / network errors~~ **FIXED** (TestBrokerErrorHandling)
- ~~No tests for negative/zero order quantities~~ **FIXED** (TestOrderValidation)
- ~~No tests for concurrent registry access~~ **FIXED** (TestRegistryThreadSafety)
- ~~No tests for secret field protection~~ **FIXED** (TestSecretProtection)
- ~~No tests for missing indicator data~~ **FIXED** (TestMissingDataHandling)
- No backtest integration tests

---

## Recommended Action Plan

### Before Paper Trading (Week 1)
1. Fix secrets exposure (SecretStr)
2. Add error handling to broker client
3. Add order validation (positive quantities)
4. Fix RSI score calculation
5. Validate indicators exist before use

### Before Live Trading (Week 2-3)
1. Add thread safety to registry
2. Scale SL/TP with volatility
3. Add retry logic for API calls
4. Implement proper backtest
5. Add comprehensive error tests

### After Validation (Week 4+)
1. Add async support
2. Add lifecycle hooks
3. Add URL validation
4. Add observer pattern for registry
5. Add version/namespace support

---

*This document should be updated as issues are resolved.*
