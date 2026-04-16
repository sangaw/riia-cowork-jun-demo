# RITA — JavaScript Frontend Specifications

This document is a high-density, low-token reference for AI agents working on the `dashboard/js/` ES-module codebase.

**IMPORTANT FOR AI AGENTS**: Read this before writing or modifying any JS in this repository. Do not re-read all JS files to understand the architecture — use this spec instead.

---

## 1. Tech Stack & Constraints

- **Pure Vanilla JS (ES Modules)** — no React, Vue, Svelte, Webpack, or bundlers.
- **Chart.js** for all charts. No D3, Recharts, or other charting libs.
- **No TypeScript** — plain `.js` files only.
- Each dashboard page (`rita.html`, `fno.html`, `ops.html`) has its own module subtree: `js/rita/`, `js/fno/`, `js/ops/`.
- All `onclick=""` handlers in HTML **must** be exposed on `window.*` — ES modules do not auto-expose functions globally.

---

## 2. Module Structure — `dashboard/js/rita/`

| File | Responsibility | Key exports |
|---|---|---|
| `api.js` | HTTP client wrapping `fetch` | `api(path, method?, body?)` |
| `utils.js` | DOM helpers | `setEl(id, html)`, `badge(status)`, `fmt(v, dec)`, `fmtPct(v)` |
| `charts.js` | Chart.js registry + defaults | `mkChart(id, config)`, `destroyChart(id)`, `C` (color palette), `chartOpts()` |
| `chart-modal.js` | Zoom-on-click modal for charts | `openChartModal(id, title)`, `closeChartModal()` |
| `nav.js` | Section navigation, loader registry | `show(section)`, `_sectionLoaders` map, `getCurrentSection()` |
| `main.js` | Entry point — wires everything | Registers `_sectionLoaders`, binds `window.*` |
| `health.js` | Home KPI strip + model status | `loadHealth()`, `loadMetrics()`, `loadPerfSummary()`, `loadDrift()`, `loadProgress()` |
| `market-signals.js` | Market Signals section + timeframe tabs | `loadMarketSignals()`, `switchMsTab(tf)`, `loadGoalHint()` |
| `trades.js` | Trade Journal section | `loadTrades()`, `downloadTradeJournal()`, `allocBadge(v)` |
| `observability.js` | Ops monitoring panel | `loadObservability()` |
| `scenarios.js` | Backtest scenario runner | `loadScenarios()`, `runScenarioBacktest()`, `renderScenarioResults()` |
| `export.js` | Pipeline step buttons (Goal, Market, Strategy) | `runGoal()`, `runMarket()`, `runStrategy()`, `runFullPipeline()` |
| `pipeline.js` | Pure renderers for pipeline step results | `renderGoalResult()`, `renderMarketResult()`, `renderStepResult()` |
| `performance.js` | Performance analytics charts | `loadPerformance()` |
| `risk.js` | Live risk view | `loadRisk()` |
| `training.js` | Training progress tracker | `loadTrainProgress()` |
| `diagnostics.js` | Model diagnostics panel | `loadDiagnostics()` |
| `explainability.js` | SHAP / model explain panel | `loadExplain()` |
| `audit.js` | Audit log table | `loadAudit()` |
| `mcp.js` | MCP calls panel | `loadMcp()` |
| `chat.js` | RITA chat assistant | `sendChatMsg()`, `useChip()`, `clearChat()` |

---

## 3. Section Loader Pattern

Every `<section id="sec-X">` in `rita.html` has a corresponding loader registered in `main.js`:

```js
// nav.js exports this map
_sectionLoaders['market-signals'] = loadMarketSignals;
_sectionLoaders.trades            = loadTrades;
// ... etc
```

**Rules:**
- The section `id` in HTML is `sec-X`. The loader key is `X` (without the `sec-` prefix).
- `show(section)` in `nav.js` calls `_sectionLoaders[section]()` on first navigation.
- **Adding a new section**: (1) add `<section id="sec-NAME">` in HTML, (2) write a loader function, (3) register it in `main.js`'s `_sectionLoaders` map, (4) expose it on `window.*` if needed for a refresh button.

---

## 4. API Communication Pattern

```js
// api.js — all fetch calls go through here
import { api } from './api.js';

const data = await api('/api/v1/market-signals?timeframe=daily&periods=252');
const result = await api('/api/v1/goal', 'POST', { target_return_pct: 15 });
```

- `api()` throws on non-2xx responses. Always wrap in `try/catch`.
- Base URL is resolved from `window.RITA_API_BASE` (set in the HTML `<script>` block).
- **Never** hardcode `http://localhost:8000` — always use `api()`.

---

## 5. Chart Pattern

```js
import { mkChart, C } from './charts.js';

// Always use mkChart — it destroys the previous chart instance first.
// Never assume a chart canvas is clean; always call mkChart to recreate.
mkChart('chart-my-id', { type: 'line', data: {...}, options: {...} });
```

**Color palette `C`:**

| Key | Hex | Use |
|---|---|---|
| `C.run` | `#0056B8` | Primary line (portfolio) |
| `C.build` | `#1A6B3C` | Positive / bullish |
| `C.warn` | `#92480A` | Warning / neutral |
| `C.danger` | `#9B1C1C` | Negative / bearish |
| `C.mon` | `#6B2FA0` | Model / monitoring |
| `C.t3` | `#8C877A` | Muted label text |
| `C.mono` | `IBM Plex Mono, monospace` | Font for tick labels |

**`chartOpts(label, tickCb, labels)`** — shared responsive options for simple single-axis charts.

---

## 6. API Endpoints → JS Consumers

### `GET /api/v1/market-signals?timeframe=&periods=`
**Consumer:** `market-signals.js` → `loadMarketSignals()`, `loadGoalHint()`  
**Response fields (per row):**
```
date, Close, Volume,
rsi_14, macd, macd_signal, macd_hist,
bb_upper, bb_lower, bb_pct_b,
atr_14,
ema_5, ema_13, ema_26, ema_50,
trend_score
```
**DOM targets:** `ms-rsi-val/sig`, `ms-macd-val/sig`, `ms-bb-val/sig`, `ms-ema5/13/26-val/sig`, `ms-atr-val/sig`, `ms-trend-val/sig`, `ms-data-range`, `ms-alerts`  
**Charts:** `chart-ms-pv`, `chart-ms-rsi`, `chart-ms-macd`, `chart-ms-bb`, `chart-ms-ema`, `chart-ms-atr`, `chart-ms-trend`

### `POST /api/v1/market`
**Consumer:** `export.js` → `runMarket()` → `pipeline.js` → `renderMarketResult()`  
**Response fields (inside `result`):**
```
date, close, trend, trend_score, sentiment_proxy,
rsi_14, rsi_signal,
macd, macd_signal_line, macd_signal,   ← NOTE: "macd_signal_line" not "macd_signal" for the numeric value
bb_pct_b, bb_position,
atr_14, atr_percentile,
ema_5, ema_13, ema_26
```
**Rendered into:** `#market-result` via `renderMarketResult()`

### `POST /api/v1/goal`
**Consumer:** `export.js` → `runGoal()` → `pipeline.js` → `renderGoalResult()`  
**Response fields (inside `result`):**
```
target_return_pct, time_horizon_days, risk_tolerance,
years, annualized_target_pct, required_monthly_return_pct,
feasibility, feasibility_note, suggested_realistic_target_pct,
last_12m_return_pct,
yearly_returns: [{year, return_pct}, ...]
```
**Chart:** `chart-goal-returns` (bar chart of annual returns)

### `GET /api/v1/risk-timeline?phase=all`
**Consumer:** `trades.js` → `loadTrades()`  
**Response fields (per row):**
```
date, phase, allocation, portfolio_value_norm, current_drawdown_pct, regime
```
**Phase values:** `"Train"` | `"Validation"` | `"Backtest"` — must match `TJ_PHASE` keys exactly

### `GET /api/v1/training-history`
**Consumer:** `trades.js` → `loadTrades()` (for Train/Validation KPI cards)  
**Response fields (per run, newest-first):**
```
round, run_id, timestamp, model_version, algorithm, status,
timesteps, backtest_sharpe, backtest_mdd_pct, backtest_return_pct
```

### `GET /api/v1/performance-summary`
**Consumer:** `health.js` → `loadPerfSummary()`, `scenarios.js` → `loadScenarios()`  
**Key fields:** `portfolio_total_return_pct`, `benchmark_total_return_pct`, `portfolio_cagr_pct`, `sharpe_ratio`, `max_drawdown_pct`, `win_rate_pct`, `total_trades`, `total_days`

### `GET /api/v1/metrics/summary`
**Consumer:** `health.js` → `loadMetrics()`, `observability.js` → `loadObservability()`  
**Key fields:** `api_requests.total_requests`, `api_requests.avg_latency_ms`, `api_requests.error_rate_pct`, `pipeline.completed_steps`, `training.rounds`, `training.latest_backtest_sharpe`

### `GET /api/v1/drift`
**Consumer:** `health.js` → `loadDrift()`, `observability.js` → `loadObservability()`  
**Shape:** `{ summary: { overall: "ok"|"warn"|"err" }, checks: { [name]: { status, message } } }`

### `GET /health`
**Consumer:** `health.js` → `loadHealth()`, `export.js` → `loadExport()`  
**Key fields:** `status`, `model_exists`, `model_age_days`, `csv_loaded`, `data_freshness.latest_date`, `data_freshness.days_since_latest`, `last_pipeline_run`, `output_dir`

---

## 7. Module-Level State

| Variable | File | Purpose |
|---|---|---|
| `_msTimeframe` | `market-signals.js` | Current tab: `'daily'`\|`'weekly'`\|`'monthly'` — persists across calls |
| `_tjRows` | `trades.js` | Cached trade rows for CSV download |
| `_charts` | `charts.js` | Registry of live Chart.js instances — keyed by canvas `id` |
| `TJ_PHASE` | `trades.js` | Phase color config: `{ Train, Validation, Backtest }` |

---

## 8. Known Gotchas & Defect History

1. **`phases` in `trades.js`** — must be declared as `const phases = Object.keys(TJ_PHASE)` before the `.map()` call. Using an undeclared `phases` throws `ReferenceError`, silently caught, leaving both the chart and table blank.

2. **`settings` vs `get_settings()`** — in Python `observability.py`, use `get_settings()` (function call), never the bare name `settings` (not defined at module level). A bare `settings` in the CSV fallback path causes a `NameError` caught silently → endpoint returns `[]` → all market-signals KPIs show `—`.

3. **`market-signals` field names differ from `POST /api/v1/market`:**
   - `/api/v1/market-signals` returns `macd_signal` (the signal line numeric value)
   - `POST /api/v1/market` returns `macd_signal_line` (same numeric value, different key) and `macd_signal` (the string label: `"bullish"|"bearish"`)
   - `pipeline.js` `renderMarketResult()` reads `r.macd_signal_line` for the number and `r.macd_signal` for the badge.

4. **Chart title "daily volume"** — `rita.html` `#ms-pv-subtitle` is now dynamic; `market-signals.js` updates it on every `loadMarketSignals()` call. Do not hardcode timeframe words in chart title HTML.

5. **`mkChart` destroys and recreates** — never call `Chart.getChart(id)` or patch an existing instance. Always call `mkChart(id, fullConfig)`.

6. **Section loaders fire once** — `nav.js` fires the loader on first visit. To force a reload, call the loader function directly (e.g., `window.loadTrades()`).

---

## 9. Window Binding Rules

ES modules are scoped — inline `onclick="foo()"` in HTML will fail unless the function is on `window`. **All functions called from HTML attributes must be listed in `main.js`:**

```js
window.functionName = functionName;   // required for every onclick handler
```

When adding a new interactive button, always check `main.js` for the `window.*` binding.

---

## 10. AI Agent Directives

1. **Never re-read all JS files to understand structure** — use this spec. Read a specific file only when you need to modify it.
2. **Check the DOM id** — before writing a `setEl('some-id', ...)` call, confirm the element exists in the HTML with that exact id.
3. **Check the API field name** — field names in API responses differ between endpoints (see Section 6 gotchas). Do not assume `market-signals` and `POST /market` use the same field names.
4. **New section checklist**: HTML section id → loader function → `_sectionLoaders` entry in `main.js` → `window.*` binding if needed.
5. **Do not introduce module-level side effects** — no `fetch()` or DOM queries at the top level of a module file; only inside exported functions.
6. **`allocBadge(v)` is the canonical allocation formatter** — do not inline allocation display logic elsewhere.
