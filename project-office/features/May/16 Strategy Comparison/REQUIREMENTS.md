# Feature 16 (May) — Strategy Comparison

**Location:** RITA App → Learnings → Strategies (Card 5)
**Invoke via:** `/enhance`
**Status:** PLANNED

---

## Summary

A new "Strategies" card in the RITA Learnings section that runs 5 rule-based trading strategies against any instrument's OHLCV data and renders a 7-panel performance dashboard. The instrument picker shows all available instruments with the globally active one highlighted. Switching instrument or year re-renders all panels. Commentary auto-fires via the existing commentary endpoint (extended with a new `strategy-comparison` page).

---

## User Story

As a RITA user, after selecting an instrument on the Overview, I navigate to **Learnings → Strategies** and see how 5 standard trading strategies performed on that instrument over a selected year. I can compare returns, Sharpe ratio, drawdown, trade frequency, accuracy, and final portfolio value side-by-side, then read a plain-English summary that identifies the winner and key risk observations.

---

## Scope

### In scope
- New "Strategies" collapsible card (Card 5) in `sec-learnings`, below Market Trends
- Instrument pill selector: all available instruments, active one highlighted on load
- Year toggle: 2024 / 2025 (default 2025)
- 7-panel Chart.js layout matching the Strategy Checks PNG
- Commentary via `POST /api/v1/commentary` extended with `page="strategy-comparison"`
- Summary metrics table below charts

### Out of scope
- Custom strategy parameter tuning (thresholds fixed per spec below)
- Multi-instrument portfolio combinations
- FnO instruments

---

## 5 Strategies — Fixed Parameters

| # | Strategy | Entry Signal | Exit Signal |
|---|---|---|---|
| 1 | Buy and Hold | Day 1 of year | Last day of year |
| 2 | Value Investing | RSI-14 < 30 (oversold) | RSI-14 > 70 (overbought) |
| 3 | Momentum Investing | Price crosses **above** SMA-20 | Price crosses **below** SMA-20 |
| 4 | Swing Trading | 5-day local low | 5-day local high |
| 5 | Support-Resistance 52-Week H/L | Price ≤ rolling-252-day low × 1.05 | Price ≥ rolling-252-day high × 0.95 |

Initial capital: **$10,000** (constant across all strategies and instruments).

---

## Metrics per Strategy

| Metric | Formula |
|---|---|
| Total Return % | `(final − 10000) / 10000 × 100` |
| Sharpe Ratio | `mean(daily_pct_change) / std(daily_pct_change) × √252` |
| Max Drawdown % | `max((peak − trough) / peak × 100)` |
| Number of Trades | Count of closed positions |
| Win Rate % | `winning_trades / total_trades × 100` |
| Final Portfolio Value | Portfolio value on last trading day |

---

## API Contract

### NEW — Experience endpoint

**`GET /api/v1/experience/rita/strategy-comparison`**

Query params:

| Param | Type | Required | Default |
|---|---|---|---|
| `instrument` | str | Yes | — |
| `year` | int | No | 2025 |

Response:
```json
{
  "instrument": "ASML",
  "year": 2025,
  "initial_capital": 10000,
  "strategies": [
    {
      "name": "Buy and Hold",
      "equity_curve": [10000.0, 10231.5, "..."],
      "dates": ["2025-01-02", "2025-01-03", "..."],
      "returns_pct": 34.8,
      "sharpe": 0.99,
      "max_drawdown_pct": 26.3,
      "n_trades": 1,
      "win_rate_pct": 100.0,
      "final_value": 13484.0
    }
  ],
  "winner": "Buy and Hold",
  "risk_adjusted_winner": "Value Investing",
  "latency_ms": 185.4
}
```

Error cases:

| Case | HTTP | Detail |
|---|---|---|
| Instrument missing | 422 | FastAPI validation |
| No data for instrument+year | 200 | `strategies: []`, `message` field set |
| CSV read failure | 200 | structlog warning, empty strategies |

### EXTEND — Commentary endpoint

`POST /api/v1/commentary` — add `("rita","strategy-comparison")` to dispatch table in `commentary.py`.

Request: `{ "app": "rita", "page": "strategy-comparison", "instrument": "ASML", "year": 2025 }`

Handler behaviour:
- `instrument` required → HTTP 400 if missing
- Calls `StrategyComparisonService.compute_strategies()` directly (no internal HTTP call)
- Commentary covers: winner by return, risk-adjusted winner, MDD-breaching strategies, 2–3 sentence narrative
- Follows same `_build_narrative(data)` swap pattern as other handlers

---

## Architecture (ADR-001 three-tier)

### Service — `src/rita/services/strategy_comparison_service.py`

- Class `StrategyComparisonService`
- Method `compute_strategies(instrument: str, year: int) -> dict`
- Reads OHLCV from `data/raw/` — see Data Loading section
- Includes 50-day prior warmup window for RSI/SMA initialisation
- Implements all 5 strategies with exact parameter values above
- Returns structured dict matching response schema

### Experience router — `src/rita/api/experience/rita.py` (new file)

- `GET /api/v1/experience/rita/strategy-comparison`
- Instantiates `StrategyComparisonService`, calls `compute_strategies()`
- structlog timing; HTTP 200 always (fallback empty strategies list on data error)
- Register in `main.py` alongside other experience routers

### Commentary handler — extend `src/rita/api/v1/workflow/commentary.py`

- Add `("rita","strategy-comparison"): _handle_strategy_comparison` to `_DISPATCH`
- `_handle_strategy_comparison(req, db)` imports and calls `StrategyComparisonService` directly
- `instrument` required → HTTP 400 if absent
- `year` optional, default 2025

### Schemas — `src/rita/schemas/strategy_comparison.py`

```python
class StrategyResult(BaseModel):
    name: str
    equity_curve: list[float]
    dates: list[str]
    returns_pct: float
    sharpe: float
    max_drawdown_pct: float
    n_trades: int
    win_rate_pct: float
    final_value: float

class StrategyComparisonResponse(BaseModel):
    instrument: str
    year: int
    initial_capital: float
    strategies: list[StrategyResult]
    winner: str
    risk_adjusted_winner: str
    latency_ms: float
```

### No new DB tables — v1

All computation is on-the-fly from CSV. Commentary audit uses the existing `commentary_logs` table (no change).

---

## Data Loading

Priority order per instrument:

1. `data/raw/{INSTRUMENT}/` — `*_daily.csv` (yfinance-fetched, preferred)
2. `data/raw/{INSTRUMENT}/` — `*_2001-2026.csv` (long-form historical)
3. `data/raw/NIFTY/nifty_yf.csv` — NIFTY-specific fallback
4. HTTP 422 if no file found

Column normalisation (both CSV formats use `Date,Close,High,Low,Open,Volume`):
- Date column: accept `date` or `Date` → parse as datetime
- Normalise to lowercase: `open, high, low, close, volume`

**Confirmed instruments with 2025 data in raw folder:**
NIFTY, BANKNIFTY, NVIDIA, ASML, AEX, ASRNL, ATO, DJI, IXIC, RELIANCE, SBIN

---

## Frontend

### New JS module — `dashboard/js/rita/strategy-comparison.js`

| Export | Description |
|---|---|
| `loadStrategyComparison()` | async — fetches from experience endpoint, renders all panels |
| `renderStrategyComparison(data)` | Renders 7 Chart.js panels + summary table |
| `selectStrategyInstrument(id)` | Called from pill onclick; re-fetches and re-renders |

### DOM additions to `rita.html`

Card 5 structure inside `sec-learnings`:

```html
<!-- Card 5: Strategies -->
<div class="card" style="margin-bottom:12px">
  <div class="card-hdr" onclick="toggleLearnCard('strategies')">
    <span class="card-title">Strategy Comparison</span>
    <span id="learn-chevron-strategies">▼</span>
  </div>
  <div id="learn-body-strategies" class="card-body">
    <!-- Commentary narrator box -->
    <div id="commentary-strategy-comparison-box" style="display:none">...</div>
    <!-- Instrument pills row -->
    <div id="strategy-instrument-pills">...</div>
    <!-- Year toggle -->
    <div id="strategy-year-toggle">...</div>
    <!-- Portfolio Growth (full width) -->
    <canvas id="chart-sc-growth" style="height:260px"></canvas>
    <!-- 3-column row: Returns | Sharpe | Drawdown -->
    <!-- 3-column row: Frequency | Accuracy | Final Value -->
    <!-- Summary metrics table -->
  </div>
</div>
```

### Instrument pill behaviour

- On card open (`loadStrategyComparison`): call `GET /api/v1/instrument/active` → highlight matching pill
- On pill click: call `selectStrategyInstrument(id)` → re-fetch → re-render all 7 charts + commentary
- Pill class pattern: `strategy-pill` + `strategy-pill-active` on selected

### Commentary narrator box

- IDs: `commentary-strategy-comparison-box`, `commentary-strategy-comparison-title`, `commentary-strategy-comparison-text`
- Fires in parallel with data fetch via `Promise.allSettled`
- On commentary failure: show `—`, never block chart render

### Integration with `learnings.js`

Add `loadStrategyComparison()` import and call from within `loadLearnings()` — fires when card 5 is in DOM.

---

## 7 Chart Panels (Chart.js)

| # | Chart | Type | Key feature |
|---|---|---|---|
| 1 | Portfolio Growth | Line (full width) | Initial capital dashed line |
| 2 | Total Returns % | Horizontal bar | Zero line |
| 3 | Sharpe Ratio | Horizontal bar | Red dashed line at 1.0 |
| 4 | Max Drawdown % | Horizontal bar | Red dashed line at 10% |
| 5 | Trading Frequency | Vertical bar | — |
| 6 | Trading Accuracy (Win Rate %) | Vertical bar | — |
| 7 | Final Portfolio Value | Vertical bar | Dashed line at $10,000 initial |

Colours (consistent with Strategy Checks PNG):
- Buy and Hold: `#1f77b4`
- Value Investing: `#ff7f0e`
- Momentum Investing: `#2ca02c`
- Swing Trading: `#d62728`
- Support-Resistance 52-Week H/L: `#9467bd`

---

## Error Handling

| Scenario | Behaviour |
|---|---|
| Instrument has no data for selected year | HTTP 200, `strategies: []`, UI shows "No data available" message |
| Insufficient warmup rows (< 30) | Skip that strategy; rest computed and returned |
| Commentary POST fails | Chart renders regardless (`Promise.allSettled`); narrator shows `—` |
| CSV column mismatch | structlog warning; HTTP 200 with empty strategies |

---

## Definition of Done

- [ ] `GET /api/v1/experience/rita/strategy-comparison?instrument=ASML&year=2025` returns metrics matching standalone script output (within ±0.5% tolerance)
- [ ] Commentary fires and renders for all 11 instruments
- [ ] Instrument pill highlights the globally active instrument on card open
- [ ] Switching instrument pill re-renders all 7 charts without page reload
- [ ] Year toggle (2024/2025) works and re-renders
- [ ] 8 unit tests: service compute, experience endpoint (happy + no-data), commentary handler (ok + missing instrument), schema validation
- [ ] `Spec_RITA_App.md` updated with new endpoint and Learnings card 5
- [ ] Deployed to production and verified at `https://riia.ravionics.nl`
