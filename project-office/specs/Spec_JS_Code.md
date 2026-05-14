# RITA — JavaScript Frontend Specification

High-density reference for AI agents working on the `dashboard/js/` ES-module codebase.

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
| `nav.js` | Section navigation, loader registry | `show(section)`, `_sectionLoaders` map, `getCurrentSection()`. `_currentSection` defaults to `'market-signals'` (landing page). |
| `main.js` | Entry point — wires everything | Registers `_sectionLoaders`, binds `window.*` |
| `health.js` | Home KPI strip + model status | `loadHealth()`, `loadMetrics()`, `loadPerfSummary()`, `loadDrift()`, `loadProgress()` |
| `market-signals.js` | Market Signals section + timeframe tabs + geography panels | `loadMarketSignals()`, `switchMsTab(tf)`, `loadGoalHint()`, `loadGeoPanels()`. `loadGeoPanels()` calls `GET /api/v1/experience/rita/geography-overview` and renders three side-by-side panels (US/EU/India) into `#geo-panels`. `ms-last-updated` label shows date **and** time (`D MMM YYYY HH:MM` en-GB); null/invalid → `—`. |
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
| **`agent-panel.js`** | **LangGraph 6-agent simulation** | `loadAgentPanel()`, `agentPanelStep()`, `approveAgentProposal()`, `rejectAgentProposal()`, `resetAgentPanel()` |
| **`ai-compliance.js`** | **AI Compliance panel (reads agent history)** | `loadAiCompliance()`, `switchAcTab(tabId, viewId)` |
| `technical-analysis.js` | Technical Analysis section — commentary + PV/ATR/RSI charts | `loadTechnicalAnalysis()` |

---

## 3. Module Structure — `dashboard/js/fno/`

| File | Responsibility | Key exports |
|---|---|---|
| `api.js` | FnO HTTP client | `api(path, method?, body?)` |
| `state.js` | Shared FnO state | `state` object (active group, instrument, etc.) |
| `nav.js` | Section navigation | `show(section)`, `_sectionLoaders` map |
| `main.js` | Entry point | Registers loaders, binds `window.*` |
| `dashboard.js` | FnO overview KPI cards | `loadFnoDashboard()` |
| `positions.js` | Open positions table | `loadPositions()` |
| `greeks.js` | Greeks calculator | `loadGreeks()`, `calculateGreeks()` |
| `margin.js` | Margin tracker | `loadMargin()` |
| `payoff.js` | Payoff diagram | `loadPayoff()` |
| `stress.js` | Stress test section | `loadStress()` |
| `rr.js` | Risk-Reward chart | `loadRR()` |
| `hedge.js` | Hedge Radar section | `loadHedge()` |
| `manoeuvre.js` | Manoeuvre section | `loadManoeuvre()` |
| `utils.js` | DOM helpers | `setEl`, `badge`, `fmt`, `fmtPct` |

---

## 4. Module Structure — `dashboard/js/ops/`

| File | Responsibility | Key exports |
|---|---|---|
| `api.js` | Ops HTTP client | `api(path, method?, body?)` |
| `utils.js` | DOM helpers | `setEl`, `badge`, etc. |
| `sidebar.js` | Sidebar navigation | `showSection()` |
| `nav.js` | Section navigation | `show(section)`, `_sectionLoaders` |
| `main.js` | Entry point | Registers loaders, binds `window.*` |
| `overview.js` | Ops overview dashboard | `loadOverview()` |
| `cicd.js` | CI/CD pipeline view | `loadCicd()` |
| `monitoring.js` | Prometheus metrics view | `loadMonitoring()` |
| `observability.js` | Structured metrics summary | `loadObservability()` |
| `test-results.js` | Test results grid | `loadTestResults()` |
| `daily-ops.js` | Daily operations panel | `loadDailyOps()` |
| `deploy.js` | Deployment management | `loadDeploy()` |
| `chat.js` | Ops chat | `sendOpsChat()` |
| **`users.js`** | **User management table** | `loadUsers()`, `createUser()`, `deleteUser()` |
| `agent-builds.js` | Agent Builds pipeline runs + performance metrics panels — API calls to `/api/experience/ops/agent-builds` and `/api/experience/ops/token-forecast` | `loadAgentBuilds()`, `renderTokenEstimateWidget()`, `submitTokenEstimate()`, `toggleEstimateWidget()` |

---

## 5. Module Structure — `dashboard/js/ds/`

**IMPORTANT: ds.html uses inline `<script>` blocks — NOT ES modules.** There is no `dashboard/js/ds/` directory. All JS logic lives inside `<script>` tags at the bottom of `riia-jun-release/dashboard/ds.html`.

Script loading: Chart.js + annotation plugin loaded via CDN. Navigation via inline `show(section, el)` function. No `_sectionLoaders` registry — section switching is direct DOM show/hide.

### Current ds.html Section Inventory

| Section key (`data-s`) | Page title | Notes |
|---|---|---|
| `understand` | Understand Data | Landing page (active by default) |
| `dashboard` | Dashboard | Build overview KPIs |
| `pipeline` | — | Build pipeline steps |
| `performance` | Performance | Backtest results — DDQN vs Buy & Hold |
| `risk` | Risk View | VaR, drawdown, trade risk, regime confidence |
| `trades` | Trade Journal | Entry/exit signals overlaid on price |
| `explain` | Explainability | SHAP feature importance charts |
| `scenarios` | Portfolio Scenarios | Scenario runner |
| `training` | Training Metrics | Round-by-round model improvement |
| `changelog` | Model Changelog | Model improvement log |
| `observability` | Observability | Pipeline timing, drift detection, system health |
| `mcp` | MCP Calls | Live log of Claude Desktop → RITA MCP invocations |
| `export` | Export & DevOps | Download results, API health, deployment info |

### Planned additions (Phases 03 / 04 — rita-app-improve feature)

| Section key | Page title | Source | Status |
|---|---|---|---|
| `experiment-results` | Experiment Results | RITA Trade Journal content moved here (renamed) — distinct from existing `trades` section | Not yet in ds.html |
| `trade-diagnostics` | Trade Diagnostics | RITA Trade Diagnostics content moved here — new section | Not yet in ds.html |
| `model-train-progress` | Training Progress | RITA Monitor copy — distinct from existing `training` section | Not yet in ds.html |
| `model-observability` | Observability | RITA Monitor copy — distinct from existing `observability` section | Not yet in ds.html |
| `model-mcp` | MCP Calls | RITA Monitor copy — distinct from existing `mcp` section | Not yet in ds.html |
| `model-audit` | Audit | RITA Monitor copy — new section | Not yet in ds.html |

> ⚠ Existing ds.html sections (`trades`, `observability`, `mcp`, `training`) have DIFFERENT content from RITA's equivalents. All additions use distinct section keys with `model-` prefix or different names to avoid collision. Do not modify existing ds.html sections when implementing Phases 03/04.

---

## 5a. Module Structure — `dashboard/js/invest-game/`

Standalone page (`invest-game.html`) — not mounted inside the Ops/RITA/FnO shells.

| File | Responsibility | Key exports |
|---|---|---|
| `api.js` | HTTP fetch wrapper; `MOCK_MODE = false` flag; `selectDays()`, `runDay()`, `getResult()` | All three functions |
| `main.js` | Full game loop: pill clicks, date validation, warm-up rows, active day unlock, Buy/Sell → `runDay()`, result card, New Game reset | `init()` (called via `<script type="module">`) |

**Game state:** managed in `gameState` object inside `main.js` — not persisted to localStorage.

---

## 6. Section Loader Pattern

Every `<section id="sec-X">` in HTML has a corresponding loader registered in `main.js`:

```js
_sectionLoaders['market-signals'] = loadMarketSignals;
_sectionLoaders['agent-panel']    = loadAgentPanel;
_sectionLoaders['ai-compliance']  = loadAiCompliance;
// ...
```

**Rules:**
- Section id in HTML is `sec-X`. Loader key is `X` (without `sec-`).
- `show(section)` in `nav.js` calls `_sectionLoaders[section]()` on first navigation.
- **Adding a new section**: (1) `<section id="sec-NAME">` in HTML, (2) loader function, (3) register in `_sectionLoaders`, (4) `window.*` binding if needed.
- **Landing section**: `_sectionLoaders['market-signals']` fires on `window.load` (called directly in the load handler in `main.js`). `_currentSection` starts as `'market-signals'`. The `sec-market-signals` section carries the `active` CSS class in HTML.

---

## 6. Agent Panel Module (`agent-panel.js`)

### State
```js
let apState = {
  dayIndex: 0,              // 0–15 (ASML April 2026, 16 trading days)
  threadId: crypto.randomUUID(),  // unique per session
  loaded: false,
};
let _twToken = 0;           // cancellation token for typewriter animation
const TOTAL_DAYS = 16;
```

### Key Functions

| Function | Description |
|---|---|
| `loadAgentPanel()` | Initialises chart and shows intro narrator text. Guards against double-load. |
| `agentPanelStep()` | Posts to `/api/v1/agent-panel/run-day` → updates chart + widgets + audit table → saves to localStorage. Pauses for HITL if BUY. |
| `approveAgentProposal()` | Hides HITL panel, appends audit note "approved", re-enables Run Day button. |
| `rejectAgentProposal()` | Hides HITL panel, appends audit note "rejected", re-enables Run Day button. |
| `resetAgentPanel()` | Increments `_twToken`, resets all state and UI, clears `riia_agent_history` from localStorage. |

### HITL Flow
When `result.proposal.action === 'BUY'`:
1. Show `#ap-hitl-panel` with proposal summary
2. Disable Run Day button, set status badge to "Awaiting Decision"
3. User clicks Approve → `approveAgentProposal()` or Reject → `rejectAgentProposal()`
4. Next day button becomes available

### DOM Targets
| Element ID | Content |
|---|---|
| `ap-chart` | Chart.js canvas — dual-axis (ASML price + capital) |
| `ap-regime` | Current regime label |
| `ap-policy` | Dynamic policy string |
| `ap-probability` | Historical success % |
| `ap-proposal` | Action + size |
| `ap-compliance` | "PASSED" or "FLAGGED: ..." (colored red on flag) |
| `ap-audit-body` | tbody — one row per day, newest first |
| `ap-narrator-title` | Narrator box title |
| `ap-narrator-text` | Typewriter-animated text |
| `ap-hitl-panel` | HITL decision panel (hidden by default) |
| `ap-hitl-summary` | Proposal summary in HITL panel |
| `ap-run-btn` | Run Day / Processing… / ✓ Complete button |
| `agent-panel-status` | Status badge |

### localStorage
- `riia_agent_history` — array of `AgentState` objects, one per day run

---

## 7. AI Compliance Module (`ai-compliance.js`)

Reads `riia_agent_history` from localStorage (written by `agent-panel.js`). **No API calls.**

### Key Functions

| Function | Description |
|---|---|
| `loadAiCompliance()` | Reads history, renders governance tab, switches to governance tab view. |
| `switchAcTab(tabId, viewId)` | Deactivates all `.ac-tab` and `.ac-view`, activates specified tab+view. |

### Three Sub-Tabs
| Tab | View ID | Content |
|---|---|---|
| Governance | `ac-view-governance` | KPIs (pass rate, veto count, days run) + visual timeline of days |
| Guardrails | `ac-view-guardrails` | (static rules documentation) |
| Trace Inspector | `ac-view-trace` | Click a timeline node → shows full agent log for that day |

### KPI DOM Targets
| ID | Value |
|---|---|
| `ac-pass-rate` | `"XX.X%"` |
| `ac-veto-count` | number of FLAGGED days |
| `ac-days-run` | total days in history |
| `ac-timeline` | container for clickable day nodes (`.ac-node`, `.ac-node-pass`, `.ac-node-veto`) |

---

## 8. API Communication Pattern

```js
import { api } from './api.js';

const data   = await api('/api/v1/market-signals?timeframe=daily&periods=252');
const result = await api('/api/v1/goal', 'POST', { target_return_pct: 15 });
```

- `api()` throws on non-2xx responses. Always wrap in `try/catch`.
- Base URL from `window.RITA_API_BASE` (set in HTML `<script>` block).
- **Never** hardcode `http://localhost:8000`.

**apiFetch() wrapper (added 2026-05-08 — Improve Observability):**
All three dashboards (`dashboard/js/rita/main.js`, `dashboard/js/fno/main.js`, `dashboard/js/ops/main.js`) and the Mobile PWA now use a shared `apiFetch(url, options)` wrapper. It attaches an `X-Request-ID` header (derived from `SESSION_TRACE_ID = crypto.randomUUID()`, with a `Math.random()` hex fallback for WebViews that lack `crypto.randomUUID`). Use `apiFetch()` for all new fetch calls; do not use bare `fetch()` directly. On non-JSON or error responses, `apiFetch()` logs to console with the trace_id and returns `null`.

---

## 9. API Endpoints → JS Consumers

### `GET /api/v1/market-signals?timeframe=&periods=&instrument=`
**Consumer:** `market-signals.js` → `loadMarketSignals()`, `loadGoalHint()`
**Response fields (per row):**
```
date, Close, Volume,
rsi_14, macd, macd_signal, macd_hist,
bb_upper, bb_lower, bb_pct_b,
atr_14, ema_5, ema_13, ema_26, ema_50, trend_score
```
**DOM targets:** `ms-rsi-val/sig`, `ms-macd-val/sig`, `ms-bb-val/sig`, `ms-ema5/13/26-val/sig`, `ms-atr-val/sig`, `ms-trend-val/sig`, `ms-data-range`, `ms-last-updated` (date + time, format: `Last updated: D MMM YYYY HH:MM`; `—` on null/error), `ms-alerts`
**Charts:** `chart-ms-pv`, `chart-ms-rsi`, `chart-ms-macd`, `chart-ms-bb`, `chart-ms-ema`, `chart-ms-atr`, `chart-ms-trend`

### `POST /api/v1/market`
**Consumer:** `export.js` → `runMarket()` → `pipeline.js` → `renderMarketResult()`
**Response fields (inside `result`):**
```
date, close, trend, trend_score, sentiment_proxy,
rsi_14, rsi_signal,
macd, macd_signal_line,    ← numeric signal line value
macd_signal,               ← string label: "bullish"|"bearish"
bb_pct_b, bb_position,
atr_14, atr_percentile,
ema_5, ema_13, ema_26
```

### `POST /api/v1/goal`
**Consumer:** `export.js` → `runGoal()` → `pipeline.js` → `renderGoalResult()`
**Response (inside `result`):**
```
target_return_pct, time_horizon_days, risk_tolerance,
annualised_target, required_monthly,
feasibility ("conservative"|"realistic"|"ambitious"|"unrealistic"),
nifty_yearly_returns: [float, ...],
last_12m_return
```

### `GET /api/v1/risk-timeline?phase=all&instrument=NIFTY`
**Consumer:** `trades.js` → `loadTrades()`
**Response fields (per row):**
```
date, portfolio_value, portfolio_value_norm, benchmark_value,
allocation, close_price, current_drawdown_pct, drawdown_budget_pct,
rolling_vol_20d, market_var_95, portfolio_var_95,
regime ("Bull"|"Neutral"|"Bear"), trend_score, phase, run_id
```

### `GET /api/v1/training-history?instrument=NIFTY`
**Consumer:** `trades.js` → `loadTrades()` (KPI cards); `ds.html` Training Metrics tabs
**Response fields (per run, newest-first):**
```
round, run_id, instrument, timestamp, model_version, algorithm, status, timesteps,
train_sharpe, train_mdd_pct, train_return_pct, train_trades,
val_sharpe, val_mdd_pct, val_return_pct, val_cagr_pct, val_trades,
backtest_sharpe, backtest_mdd_pct, backtest_return_pct, backtest_cagr_pct,
backtest_trades, backtest_constraints_met
```

### `GET /api/v1/performance-summary`
**Consumer:** `health.js` → `loadPerfSummary()`, `scenarios.js` → `loadScenarios()`
**Key fields:** `portfolio_total_return_pct`, `benchmark_total_return_pct`, `portfolio_cagr_pct`, `sharpe_ratio`, `max_drawdown_pct`, `win_rate_pct`, `total_days`
**Stale-check fields:** `_run_instrument_id`, `_active_instrument_id`

### `GET /api/v1/metrics/summary`
**Consumer:** `health.js` → `loadMetrics()`, `observability.js`
**Key fields:** `api_requests.total_requests`, `api_requests.avg_latency_ms`, `api_requests.error_rate_pct`, `pipeline.completed_steps`, `training.rounds`, `training.latest_backtest_sharpe`

### `GET /api/v1/drift`
**Consumer:** `health.js` → `loadDrift()`, `observability.js`
**Shape:** `{ summary: { overall: "ok"|"warn"|"err" }, checks: { [name]: { status, message } } }`

### `GET /health`
**Consumer:** `health.js` → `loadHealth()`
**Key fields:** `status`, `model_exists`, `model_age_days`, `csv_loaded`, `data_freshness.latest_date`, `data_freshness.days_since_latest`, `last_pipeline_run`, `output_dir`, `sharpe_trend_last5`

### `GET /api/v1/test-results`
**Consumer:** `ops/test-results.js` → `loadTestResults()`
**Key fields:**
```
data_available, total, passed, failed, pass_rate,
suite_summary: { e2e, unit, integration } each: { total, passed, failed, run_at, file_exists }
modules[], suites[]
```

### `POST /api/v1/agent-panel/run-day`
**Consumer:** `agent-panel.js` → `agentPanelStep()`
**Request:** `{ day_index: int, thread_id: string }`
**Response:** Full `AgentState` dict — `date, price_data, regime, policy, probability, proposal, compliance_status, logs, cash, holdings, portfolio_value, collaboration_insight`

### `GET /api/v1/portfolio/summary`
**Consumer:** `fno/dashboard.js`, Mobile PWA `fetchPortfolioSummary()`
**Key fields:** `total_pnl`, `lot_count`, `nifty_spot`, `banknifty_spot`, `asml_close`, `nvidia_close`, `market{NIFTY, BANKNIFTY, ASML, NVIDIA}` each: `{date, open, high, low, close, prevClose, chgFromOpen, chgFromPrev, shares, turnover}`

### `GET /api/v1/portfolio/positions?mode=paper`
**Consumer:** `fno/positions.js`, Mobile PWA `fetchPositions()`
**Response (per row):** `{instrument, full, und, exp, type, strike, side, qty, avg, ltp, chg, pnl, currency, lot_size, sl_price, target_price, entry_date, expiry_date}`

### `GET /api/v1/portfolio/price-history?periods=30`
**Consumer:** Mobile PWA `fetchPriceHistory()`, FnO `rr.js`
**Response (per row):** `{date, open, high, low, close}`

### `GET /api/v1/trade-events`
**Consumer:** Mobile PWA `fetchTradeEvents()`, `trades.js`
**Response (per event):** `{date, phase, event_type, trade_type, risk_action, allocation, delta_allocation, price, pnl, portfolio_var_95, delta_var, regime, sharpe_at_trade}`

### `GET /api/experience/ops/agent-builds`
**Consumer:** `ops/agent-builds.js` → `loadAgentBuilds()`
**Response:** `{ runs: AgentBuildRunOut[], metrics: AgentBuildMetrics }`
**Metrics shape (new fields):** `task_completion` (tsr, first_attempt_success_rate, partial_completion_rate, abandonment_rate), `quality` (avg_accuracy_score, avg_relevance_score, avg_csat, planning_accuracy_rate, grounding_pass_rate), `token_forecasting` (avg_forecast_error_pct, by_complexity, by_feature_type), `efficiency`, `reliability`, `hitl` (escalation_rate, avg_corrections_per_run, total_hitl_events), `agentic`
**Runs shape (new fields per run):** `hitl_events[]`, `token_forecast` (total_forecast, per_role, complexity, confidence, basis_runs), `human_score` (accuracy, relevance, planning_ok, csat, time_saved_hours)

### `GET /api/experience/ops/token-forecast`
**Consumer:** `ops/agent-builds.js` → `submitTokenEstimate()`
**Query params:** `feature_type` (rita|ops|fno|invest-game), `files_to_change` (small|medium|large), `new_endpoint_or_model` (none|one|both), `frontend_scope` (none|panel|page), `integration_type` (additive|extends|cross-cutting)
**Response (`TokenForecastResponse`):** `{ complexity, complexity_score, feature_type, per_role: {pm, architect, engineer, qa, techwriter}, total_forecast, confidence, basis_runs }`
**DOM targets:** `ab-estimate-result`, `ab-estimate-btn`
**Auth:** JWT required

---

## 10. Chart Pattern

```js
import { mkChart, C } from './charts.js';

// Always use mkChart — destroys previous instance first.
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

**`chartOpts(label, tickCb, labels)`** — shared responsive options for single-axis charts.

---

## 11. Module-Level State

| Variable | File | Purpose |
|---|---|---|
| `_msTimeframe` | `market-signals.js` | Current tab: `'daily'`\|`'weekly'`\|`'monthly'` |
| `_tjRows` | `trades.js` | Cached trade rows for CSV download |
| `_charts` | `charts.js` | Registry of live Chart.js instances keyed by canvas `id` |
| `TJ_PHASE` | `trades.js` | Phase color config: `{ Train, Validation, Backtest }` |
| `apState` | `agent-panel.js` | `{dayIndex, threadId, loaded}` — resets on `resetAgentPanel()` |
| `_twToken` | `agent-panel.js` | Cancellation token for typewriter animation |
| `_acHistory` | `ai-compliance.js` | Copy of `riia_agent_history` from localStorage |

---

## 12. Known Gotchas & Defect History

1. **`phases` in `trades.js`** — must be declared as `const phases = Object.keys(TJ_PHASE)` before `.map()`. Undeclared `phases` throws `ReferenceError` silently, leaving chart and table blank.

2. **`settings` vs `get_settings()`** — in Python `observability.py`, use `get_settings()` (function call), never bare `settings` (not defined at module level). Bare `settings` → `NameError` silently caught → endpoint returns `[]` → all market-signals KPIs show `—`.

3. **`market-signals` field names differ from `POST /api/v1/market`:**
   - `/api/v1/market-signals` returns `macd_signal` (numeric signal line value)
   - `POST /api/v1/market` returns `macd_signal_line` (numeric) and `macd_signal` (string label)
   - `pipeline.js:renderMarketResult()` reads `r.macd_signal_line` for the number and `r.macd_signal` for the badge.

4. **`mkChart` destroys and recreates** — never call `Chart.getChart(id)` or patch an existing instance (exception: `agent-panel.js:_updateApChart()` calls `Chart.getChart()` to incrementally add data to a running chart — this is intentional).

5. **Section loaders fire once** — `nav.js` fires the loader on first visit. To force reload, call the loader function directly (e.g., `window.loadTrades()`).

6. **Agent Panel localStorage** — `riia_agent_history` is read by `ai-compliance.js`. Always clear this key in `resetAgentPanel()` to avoid stale compliance data.

7. **`val_sharpe` backfill (2026-04-21)** — Historical `training_runs` records had `val_sharpe=NULL`. Fixed by SQL backfill. New runs write all fields correctly.

8. **Trade Journal layout** — `#trades-kpi-strip` uses `grid-template-columns: 1fr 1fr 2fr`. Both APIs called with `?instrument=` from `localStorage.getItem('ritaInstrument')`.

---

## 13. Window Binding Rules

ES modules are scoped — inline `onclick="foo()"` will fail unless `window.foo` is set. **All HTML onclick functions must be listed in `main.js`:**

```js
window.agentPanelStep     = agentPanelStep;
window.approveAgentProposal = approveAgentProposal;
window.rejectAgentProposal  = rejectAgentProposal;
window.resetAgentPanel    = resetAgentPanel;
window.loadAiCompliance   = loadAiCompliance;
window.switchAcTab        = switchAcTab;
```

---

## 14. AI Agent Directives

1. **Never re-read all JS files** — use this spec. Read a specific file only when you need to modify it.
2. **Check the DOM id** — before writing `setEl('some-id', ...)`, confirm the element exists in the HTML.
3. **Check the API field name** — field names differ between endpoints (see Section 9 gotchas).
4. **New section checklist**: HTML section id → loader function → `_sectionLoaders` entry → `window.*` binding.
5. **No module-level side effects** — no `fetch()` or DOM queries at the top level of a module; only inside exported functions. (Exception: `agent_panel.py` loads ASML data at module import — this is intentional for the backend, not the frontend.)
6. **`allocBadge(v)` is the canonical allocation formatter** — do not inline allocation display logic elsewhere.
7. **Agent Panel reset clears localStorage** — `resetAgentPanel()` must call `localStorage.removeItem('riia_agent_history')` to keep AI Compliance in sync.
