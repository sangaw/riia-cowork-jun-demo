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
| `api.js` | Thin re-export wrapper → `shared/api.js` | `api(path, method?, body?)` |
| `utils.js` | Thin re-export wrapper → `shared/utils.js` | `setEl(id, html)`, `badge(status)`, `fmt(v, d?)`, `fmtPct(v)`, `fmtMs(v)`, `appendResult(containerId, html)` |
| `charts.js` | Thin re-export wrapper → `shared/charts.js` | `mkChart(id, config)`, `destroyChart(id)`, `C` (color palette), `chartOpts()` |
| `chart-modal.js` | Zoom-on-click modal for charts | `openChartModal(id, title)`, `closeChartModal()` |
| `nav.js` | Section navigation, loader registry | `show(section)`, `_sectionLoaders` map, `getCurrentSection()`. `_currentSection` defaults to `'market-signals'` (landing page). |
| `main.js` | Entry point — wires everything | Registers `_sectionLoaders`, binds `window.*`. `selectGeoInstrument(id)` — instrument selector: sets `localStorage('ritaInstrument')`, toggles `.geo-kpi-active` on geo panel tiles, posts to `/api/v1/instrument/select`, refreshes health KPIs + active section. `loadInstrumentTabs` and `#inst-tabs-container` removed (2026-05-21) — geo panel tiles are now the selector. |
| `health.js` | Home KPI strip + model status | `loadHealth()`, `loadMetrics()`, `loadPerfSummary()`, `loadDrift()`, `loadProgress()` |
| `market-signals.js` | Market Signals section + timeframe tabs + geography panels | `loadMarketSignals()`, `switchMsTab(tf)`, `loadGoalHint()`, `loadGeoPanels()`. `loadGeoPanels()` fetches `GET /api/v1/experience/rita/geography-overview`, renders `.geo-kpi` tiles into `#geo-panels`. Each tile has `onclick="selectGeoInstrument(id)"` and `data-id`. Active instrument (from `localStorage`) gets `.geo-kpi-active` class on every render. Region names via `_GEO_REGION_NAMES` (`India`, `US`→`United States`, `EU`→`Europe`); flag emoji stripped. Instrument display names via `_GEO_INST_NAMES` (e.g. `Dow Jones Industrial Average`→`Dow Jones`). ATHER excluded (`i.id !== 'ATHER'`). Name occupies 2 lines (`min-height:2.6em`); price and trend always on lines 3–4. Called non-blocking from `loadMarketSignals()`. `ms-last-updated` label: `D MMM YYYY HH:MM` en-GB; null → `—`. |
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
| `commentary.js` | Typewriter narrative for overview and strategy pages | `loadOverviewCommentary()`, `showOverviewCommentary(text)`, `showStrategyCommentary(text)` |
| **`agent-panel.js`** | **LangGraph 6-agent simulation** | `loadAgentPanel()`, `agentPanelStep()`, `approveAgentProposal()`, `rejectAgentProposal()`, `resetAgentPanel()` |
| **`ai-compliance.js`** | **AI Compliance panel (reads agent history)** | `loadAiCompliance()`, `switchAcTab(tabId, viewId)` |
| `technical-analysis.js` | Technical Analysis section — commentary + PV/ATR/RSI charts | `loadTechnicalAnalysis()` |
| `learnings.js` | Learnings / Concepts section — accordion cards + live market-trend charts, plus the **Investment Workflow & Agents** tabbed block (Feature 31): narrative on how professional investment firms invest, 8-step workflow table, RIIA two-pillar (Data Science + Agentic AI) copy, and 8 agent tabs (`aw-a1`…`aw-a8`) each linking a chart. Follows the DS Lab CRISP-DM tab pattern. Reuses existing endpoints only (no new path): `performance-summary`, `market-signals`, `experience/rita/backtest-daily`, `shap`, `experience/rita/training-history`. | `loadLearnings()`, `toggleLearnCard(id)`, `switchAgentTab(agentKey, el)` |
| `strategy-comparison.js` | Strategy Comparison card (Card 5 in Learnings) — 5-strategy OHLCV dashboard; 7 Chart.js panels; instrument pills; year toggle; commentary | `loadStrategyComparison()`, `scSelectInstrument(id)`, `scSelectYear(year)` |
| `my-portfolio.js` | Portfolio allocation builder (Phase 05 nav) — `kpi kpi-sm` tiles (one per instrument, editable % input), 100% enforcer + progress bar, save to `POST /api/v1/user-portfolio/`, pre-fill from saved portfolio. Post-save: allocation chips + Chart.js 2025 line chart via `portfolio-performance` endpoint (base 100). **Auth:** calls `ensureDevToken()` before save — on localhost auto-mints a JWT via `/auth/token`; on production redirects to Google OAuth. | `loadMyPortfolio()`, `savePortfolio()` |
| `portfolio-builder.js` | Portfolio Builder page (Feature 28) — three region buckets ranked by 1Y return with select-all and sticky Selected basket (chip grid, 4-row scroll, 15% default on add, 100% Allocate gate); Chart.js scatter map (return vs risk); sortable instrument table; guided basket (Short Term auto-selected on load, goal presets, ranked draft, toggle on/off). Data from `geography-overview` (return_1y_pct, risk_score, sector, horizons[]). Module cache-busted via `?v=` in main.js import. **Shares + cash (post-F28):** when Portfolio value (€) input is set, each basket chip shows whole-share count (`floor(allocEur / close)`) and cash remainder in green/grey; `pbSetAlloc` updates the chip live without re-render. `pbBuildPortfolio()` enriches each holding with `shares` (int) and `cash_eur` (float) before POSTing. Helpers: `_priceForId(id)` reads `close` from geoCache; `_sharesAndCash(totalEur, allocPct, price)` returns `{allocEur, shares, actual, cash}`. Basket summary panel shows total cash balance row. **Auth:** calls `ensureDevToken()` on localhost, falls back to Google OAuth on production. | `loadPortfolioBuilder()`, `pbToggleInstrument(id)`, `pbSelectAllRegion(key)`, `pbClearAllRegion(key)`, `pbSortTable(col)`, `pbApplyGoalPreset(key)`, `pbToggleDraftItem(id)`, `pbBuildFromDraft()`, `pbClearBasket()`, `pbBuildPortfolio()`, `pbSetAlloc(id, pct)` |
| `agent-performance.js` | Agent Performance page (Feature 32) — per-agent KPI cards (`#agent-perf-cards`) + 7-row table (`#agent-perf-table`) for the 7 investment-workflow agents. Reads `GET /api/v1/experience/rita/agent-performance`. Imports `api` (api.js) and `setEl, badge, fmtPct` (utils.js). Helpers: `fmtRate(rate)` (0–1 fraction → `fmtPct(rate*100)`, `—` when null), `fmtTrend(trend)` (signed percent, `—` when null). try/catch sets both containers to `—` on error. Distinct from the Ops Agent Builds page. | `loadAgentPerformance()` |

---

## 3. Module Structure — `dashboard/js/fno/`

| File | Responsibility | Key exports |
|---|---|---|
| `api.js` | Thin re-export wrapper → `shared/api.js`; exports apiBase, api, apiFetch, RITA_API_KEY | `apiBase()`, `api(path, method?, body?)`, `apiFetch(url, options?)`, `RITA_API_KEY` |
| `app-init.js` | Single-fetch init via `/api/v1/experience/fno/portfolio-analytics?mode=`. F30 Phase 2: `initApp(mode='mock')` replaces separate fetch chain; `fetchPositions()` is a backward-compat shim that calls `initApp(state.analyticsMode)`. **F30 Phase 3:** adds `_normScenarioLevels(raw)` — normalises `{target,sl}` shape to `{bull:{target,sl},bear:{target:sl,sl:target}}`; applied to `data.scenario_levels` before state assignment. `_renderAll()` now calls `renderOverviewFromState()` (my-portfolio.js) and `renderPortfolioHedgeRadar()` (hedge.js) instead of `renderHedgeRadar()`. **`_buildPortfolioGeoInstruments(portData, geoData)`:** builds `state.portfolioGeoInstruments` from parallel portfolio + geography fetches; each entry now carries `shares` (integer, from saved portfolio), `cash_eur` (leftover cash per holding), and `close` (current market price from geo) in addition to `id`, `name`, `region`, `allocation_pct`. | `fetchPositions()`, `initApp(mode?)`, `checkStatus()` |
| `state.js` | Shared FnO state | `state` object (active group, instrument, etc.) |
| `nav.js` | Section navigation | `show(section)`, `_sectionLoaders` map |
| `main.js` | Entry point | Registers loaders, binds `window.*` |
| `dashboard.js` | FnO overview KPI cards + geo-region instrument overview. **Overview redesign (F31):** `renderDashboard()` calls `renderDashKpis()`, `renderGeoOverview()`, `renderMarketSnapshot()`, `renderDailyProgress()`. `renderGeoOverview()` groups `state.marketData` + `state.positions` by region (India/US/EU/Other), renders RITA-style compact geo-kpi cards with price + signal, onclick→`setUnderlying(id)`. `renderDashKpis()` now emits 7-KPI merged row: Portfolio Value (from `state.portfolioMeta.total_value_eur`) · Total P&L · Active Positions · Unrealized P&L · Realized P&L · Net P&L · Net Delta. Removed: `renderInstrumentCapsule()`, `renderSegmentChart()`, `renderMovers()`. DOM IDs: `fno-geo-overview`, `dash-kpis`. | `renderDashboard()`, `renderGeoOverview()`, `renderDashKpis()`, `renderMarketSnapshot()`, `renderDailyProgress()` |
| `positions.js` | Open positions table | `loadPositions()` |
| `greeks.js` | Greeks calculator | `loadGreeks()`, `calculateGreeks()` |
| `margin.js` | Margin tracker | `loadMargin()` |
| `payoff.js` | Payoff diagram | `loadPayoff()` |
| `stress.js` | Stress test section. **F31:** `renderStressScenarios()` now calls `renderStdDevTable()` instead of `renderAnalyticsStress()`. `renderStdDevTable()` reads `state.positions` + `state.marketData`, renders per-instrument ±1σ/±2σ/±3σ price ranges with 68.3%/95.5%/99.7% probabilities into `id="stress-events-row"`. Historical events section removed. | `computeFilteredStress()`, `renderStressScenarios()`, `renderStdDevTable()` |
| `rr.js` | Risk-Reward chart. **F31:** `renderScenarios()` is now fully dynamic — gets instrument list from `Object.keys(state.scenarioLevels)` (portfolio-driven, not hardcoded). Injects per-instrument sections into `id="scen-instrument-sections"` container. Summary card delta sub-label uses all portfolio instruments. Removed hardcoded NIFTY/BANKNIFTY section IDs. `renderBullBearKpis(und)` now uses `und` directly for spot label instead of conditional NIFTY/BANKNIFTY check. | `loadRR()`, `renderScenarios()`, `renderBullBearKpis(und)`, `renderView(und, mode)`, `renderBullBearTable(und, mode)`, `renderRRHistory()`, `computeScen()`, `getProgressDir()`, `getBullBear()`, `saveToday()`, `syncPriceHistory()`, `loadHistory()` |
| `hedge.js` | Hedge Radar section + HQS historical timeline. **F30 Phase 3:** adds `renderPortfolioHedgeRadar()` — reads `state.hedgeQuality.positions[]`, renders KPI counts (total/hedged/unhedged), alert banner (red/yellow/green), instrument-level HQS table (`hqs-tbody`). Guards: `!positions?.length` → shows "No hedge quality data" in `hqs-kpis` and returns. | `loadHedge()`, `renderHedgeHistory()`, `renderHedgeRadar()`, `renderPortfolioHedgeRadar()` |
| `manoeuvre.js` | Manoeuvre section | `loadManoeuvre()` |
| `equity_hedge.js` | ASML Equity Hedge Scenarios page. **`_computeNShares(instrument)`:** prefers `inst.shares` (integer stored by portfolio builder) from `state.portfolioGeoInstruments`; falls back to `floor(alloc%/100 × total_value_eur / price)` using `state.marketData[inst].close` or `inst.close` — ensures hedge scenarios always use whole-share counts. | `loadEquityHedge(forceRefresh)`, `renderEquityHedge(data)` |
| `my-portfolio.js` | **F29 Phase 3** — Portfolio Overview redesign. 3-source parallel fetch via `Promise.allSettled`: `GET /api/v1/experience/user-portfolio` (JWT), `GET /api/experience/rita/geography-overview`, `GET /api/v1/experience/fno/hedge-plan` (JWT). Renders: 5-card KPI strip (Portfolio Value, Holdings, Wtd 1Y Return [indicative], Avg Risk [indicative], Hedge Coverage [indicative]); region-allocation doughnut chart (`mkChart`, grouped India/US/EU/Other from instMap); Hedge Status card (plan details or "No hedge configured" + CTA); 6-column holdings table (Instrument · Alloc% · Position€ · 1Y Return [ind.] · Risk [ind.] · Hedged?). instMap built via explicit nested loop propagating `reg.region` from parent GeoRegion to each instrument. Per-source fallback: portfolio null → empty state; geo null → `instMap={}`; hedge null → "No hedge configured". DOM IDs: `fno-mp-name`, `fno-mp-updated`, `fno-mp-empty`, `fno-mp-error`, `fno-mp-kpi-value`, `fno-mp-kpi-holdings`, `fno-mp-kpi-return`, `fno-mp-kpi-risk`, `fno-mp-kpi-hedged`, `fno-mp-alloc-chart`, `fno-mp-hedge-card`, `fno-mp-holdings-body`, `fno-mp-total`. Window binding: `window.fnoMpGoHedge` (navigates to portfolio-hedge section, registered in main.js). **F30 Phase 3:** adds `renderOverviewFromState()` and `fnoSelectInstrument(id)`. **F31 Overview redesign:** `renderOverviewFromState()` is now a no-op stub — geo overview moved to `dashboard.js:renderGeoOverview()`, KPI row moved to `dashboard.js:renderDashKpis()`. `fnoSelectInstrument(id)` now delegates directly to `window.setUnderlying(id)`. Removed: instrument selector pills (`fno-overview-inst-selector`), merged KPI strip DOM IDs, positions grid (`fno-overview-positions-body`), `_selectedInstrument` module variable. | `loadFnoMyPortfolio()`, `renderOverviewFromState()`, `fnoSelectInstrument(id)` |
| `risk_chart.js` | Instrument + Portfolio performance charts for the FnO Risk page. One-time fetch from `GET /api/v1/portfolio/overview?instruments=` (portfolio IDs from `state.portfolioGeoInstruments`). Renders two Chart.js line charts: (1) `risk-inst-chart` — per-instrument absolute price lines (normalised_returns × start_prices); (2) `risk-port-chart` — weighted portfolio composite in EUR (anchored to `state.portfolioMeta.total_value_eur`). `highlightRiskChart()` — updates line opacity/width on instrument filter change without a re-fetch, reads `state.riskSelectedInstrument` (null = all lines equal weight; set = selected line bold, others faded). Imported by `app-init.js` at init. | `fetchAndRenderRiskCharts()`, `highlightRiskChart()` |
| `portfolio-builder.js` | _(see RITA section — file lives in `dashboard/js/rita/`, not fno)_ | — |
| `portfolio-hedge.js` | 4-tab hedge wizard (Feature 28 Phase 3, updated F29 Phase 0 + Phase 2) — Discover (holdings summary, duration locked to 1y) → Selection (Put Buy vs Sell Call per instrument, BS-priced, auto-recommend) → Allocation (σ-anchored scenario matrix −2σ/−1σ/Flat/+1σ, coverage slider) → Hedge (read-only confirmed strategy summary + payoff chart). State: `_state.{tab, coverage, holdings, instruments, apiHedge, selections, hedgeChecked, reached}`. `duration` removed from state (F29 Phase 0). **F29 Phase 2:** calls `GET /api/v1/experience/fno/hedge-plan` on load to restore `hedged_ids`, `coverage`, and `scenario_tab`; calls `PUT` (debounced 400ms) on every user change (checkbox toggle, coverage slider, scenario tab switch). GET 404 silently uses defaults. Blocking bug fixed: `hedgeChecked` is no longer overwritten by `_fetchHedge` loop — only `loadHedgePlan()` and the first-time-user fallback (`if hedgeChecked.size === 0`) populate it. API: `GET /api/v1/experience/fno/portfolio-hedge?coverage=N` (JWT) — `duration` query param removed, `tMonths = 12` hardcoded. **Holdings table (post-F28):** each row now renders `shares` and `cash_eur` from `_state.holdings` inline under the ticker (green "N shares" + grey "€X cash") when the portfolio builder stored those values. `_renderDiscoverTotals()` adds a "total cash" label (green) in the portfolio-total sticky row by summing `cash_eur` across all holdings. | `loadPortfolioHedge()`, `phGoNext()`, `phGoBack()`, `phGoToTab(tab)`, `phPickStrategy(id, strategy)`, `phSetCoverage(val)` — `phSetDuration(d)` removed (F29 Phase 0); internal: `loadHedgePlan(token)`, `saveHedgePlan()`, `_debouncedSave()` (F29 Phase 2) |
| `utils.js` | fno-specific formatters: fmt (en-IN locale), fmtPnl (INR prefix), pnlClass | `fmt(v, d?)`, `fmtPnl(v)`, `pnlClass(v)` |

---

### 3a. Module Structure — `dashboard/js/scenarios/` (Shared FnO Scenario Modules)

Modules consumed both by the standalone `dashboard/equity-scenarios.html` page and by the FnO app as a native section (`#page-equity-scenarios` in `fno.html`, wired via `_sectionLoaders['equity-scenarios']` in `fno/main.js`). Self-contained ES modules with no imports from `fno/` or `shared/`.

| File | Responsibility | Key exports |
|---|---|---|
| `scenarios/equity-scenarios.js` | Equity SL/Target scenario tracker. Fetches `alerts.json`, `portfolio.json`, `tradebook.json` from `dashboard/data/scenarios/` via bare `fetch()` (not `api()` — static files, no auth; the JSONs are committed under `dashboard/data/scenarios/`). Renders an urgency-sorted expandable table — one line per instrument (`renderRow`) with a 9-dot SL→Target position indicator column (`calcFilled`/`buildDotHtml`) and Position column at the end; clicking a row class-toggles a detail row (`renderDetailRow`) with P&L metrics, trade chips, and recommendation text (`buildRecommendation`, `computeStatus`). Local helpers: `setEl()`, `INR()`, `PCT()`. | `init` (imported by `fno/main.js` and `equity-scenarios.html`) |

---

## 4. Module Structure — `dashboard/js/ops/`

| File | Responsibility | Key exports |
|---|---|---|
| `api.js` | Thin re-export wrapper → `shared/api.js` | `apiBase()`, `api(path, method?, body?)`, `apiFetch(url, options?)` |
| `utils.js` | DOM helpers + pipeline actions (merged from former utilities.js) | `setEl`, `badge(text, cls)` (local two-arg), `fmt`, `stepName`, `runGoal`, `runMarket`, `runStrategy`, `runFullPipeline`, `doReset`, `loadUtilities` |
| `sidebar.js` | Sidebar navigation | `showSection()` |
| `nav.js` | Section navigation | `show(section)`, `_sectionLoaders` |
| `main.js` | Entry point | Registers loaders, binds `window.*` |
| `overview.js` | Ops overview dashboard | `loadOverview()` |
| `monitoring.js` | API metrics, alerts, functional KPIs, step log — embeds `loadApiMetrics()` at end of load | `loadMonitoring()` |
| `observability.js` | Drift detection, data freshness, Sharpe trend, source availability, MCP call log | `loadObservability()` |
| `test-results.js` | Test results grid | `loadTestResults()` |
| `risk.js` | Portfolio Risk overview for Ops Risk page — KPI strip (net delta, theta, vega, unrealised P&L), open positions table, stress scenarios table, hedge quality score chips. Rendered above Manoeuvre section (risk-first layout). Added `1ee6105`. | `loadRisk()` |
| `daily-ops.js` | Daily operations panel | `loadDailyOps()`, `loadInstruments()`, `toggleInstrument()`, `saveInstruments()`, `triggerSnapshot()`, `searchInstrument()`, `onboardInstrument()` |
| `deploy.js` | Deployment management | `loadDeploy()` |
| `chat.js` | Ops chat | `sendOpsChat()` |
| **`users.js`** | **User management table** | `loadUsers()`, `createUser()`, `deleteUser()` |
| `agent-builds.js` | Agent Builds pipeline runs + performance metrics panels — API calls to `/api/experience/ops/agent-builds` and `/api/experience/ops/token-forecast` | `loadAgentBuilds()`, `renderTokenEstimateWidget()`, `submitTokenEstimate()`, `toggleEstimateWidget()`. Updated signatures: `mountTrendChart(m, runs)` and `renderTrendPanel(m, runs)` take runs array to derive TSR/CSAT/adherence; `renderKpiCards(metrics, runs)` takes runs for cache hit rate KPI. Run History table shows "Est / Actual" tokens column (colour-coded) replacing "Forecast Δ". Token chart shows dashed actual lines alongside solid estimate lines. |
| `api-metrics.js` | API call log metrics panel — reads from `/api/experience/ops/api-metrics`; DOM target now inside `sec-monitoring` | `loadApiMetrics()`, `filterApiMetrics()` |
| `alerts.js` | Active alerts panel — reads from `/ops/alerts/active-alerts.json`; DOM target now inside `sec-monitoring` | `loadAlerts()` |
| `source-availability.js` | Source availability chart — reads from `/ops/metrics/source-availability.json`; DOM target now inside `sec-observability` | `loadSourceAvailability()` |
| `functional-kpis.js` | KPI strip — reads from `/api/experience/ops/functional-kpis`; DOM target now inside `sec-monitoring` | `loadFunctionalKPIs()` |

**Feature 16 Run A note:** No new JS module added. The data refresh endpoint (`POST /api/v1/instrument/refresh-all`) is invoked via the `/refresh-all-instruments-data` slash command and the standalone script `project-office/scripts/run_data_refresh.py`. A UI trigger panel may be added to `daily-ops.js` in a future run.

**Shared modules (`dashboard/js/shared/`):**

| File | Responsibility | Key exports |
|---|---|---|
| `shared/api.js` | Canonical HTTP client (shared by all apps). Reads JWT from `sessionStorage.getItem('auth_token')`. On 401 clears `auth_token`; **on localhost** returns silently (no redirect); **on production** redirects to `/auth/google/login`. **All dashboards must use `auth_token` as the sessionStorage key — never `rita_token` or any other key.** | `apiBase()`, `api(path, method?, body?)`, `apiFetch(url, options?)` |
| `shared/dev-auth.js` | Local-dev auth bypass. No-op on non-localhost. `ensureDevToken()` calls `POST /auth/token {username:'rita-dev', password:'rita-dev'}`, stores the returned JWT in `sessionStorage('auth_token')`. `isLocalDev()` returns true when hostname is `localhost`/`127.0.0.1`/`0.0.0.0`. Used by RITA `main.js` (on page load), `portfolio-builder.js`, and `my-portfolio.js` (before save). FnO `main.js` already called this before this change. Never runs on production. | `ensureDevToken()`, `isLocalDev()` |
| `shared/utils.js` | Canonical DOM helpers + formatters (shared by all apps) | `setEl(id, html)`, `badge(status)`, `fmt(v, d?)`, `fmtPct(v)`, `fmtMs(v)`, `appendResult(containerId, html)`, `randomUUID()` (safe fallback — `crypto.randomUUID` requires HTTPS; uses `Math.random` hex fallback on HTTP) |
| `shared/charts.js` | Chart.js registry (moved from rita/; shared by all apps) | `mkChart(id, config)`, `destroyChart(id)`, `chartOpts(label, tickCb, labels)`, `C` (color palette) |
| `shared/nav-base.js` | Lazy-loader registry factory | `createNavRegistry()` → `{ register, load, reset, loaders }` |
| `shared/api-cache.js` | Session-scoped API response cache factory. Cleared on page reload. | `createCache(apiFn)` — returns `cachedApi(path, ttlMs)` |
| `shared/i18n.js` | Client-side i18n module | `t(key)`, `setLanguage(lang)`, `getLanguage()`, `applyTranslations()`, `initI18n()` |

---

## 5. Module Structure — `dashboard/js/users/`

Standalone user traffic page — no ops sidebar, no shared api.js dependency.

| File | Responsibility |
|---|---|
| `users/main.js` | Standalone entry point — fetches `/api/v1/experience/users/traffic`, renders KPI tiles, Chart.js bar chart, daily breakdown table. JWT redirect guard on load. |

---

## 6. Module Structure — `dashboard/js/ds/`

**Feature 10 Phase 4 complete (2026-05-18).** All inline scripts extracted from `ds.html` into ES modules at `dashboard/js/ds/`. `ds.html` now loads via `<script type="module" src="js/ds/main.js">`.

Script loading: Chart.js + annotation plugin loaded via CDN (kept). Nav-collapse IIFE kept as plain `<script>`. Entry point: `ds/main.js`. Section switching: `ds/nav.js` `createShow(loaders)` factory. Cross-section state: `ds/state.js`.

### ds/ Module Table (24 files)

| File | Responsibility |
|---|---|
| `ds/api.js` | Thin re-export: `apiBase`, `api`, `apiFetch` from `../shared/api.js`; exports `DS_API_KEY = ''` |
| `ds/utils.js` | `mkTbl`, `fmtPctRaw`, `openChartModal`, `closeChartModal`, `DS_C` (extended color palette with ds-specific colors) |
| `ds/state.js` | `export const state = { activeInst: null }` — shared cross-section mutable state |
| `ds/nav.js` | `createShow(loaders)` factory → returns `show(sId, el)` function |
| `ds/main.js` | Entry point: imports all loaders + `createShow`; assigns all `window.*` at module scope; calls init on DOMContentLoaded |
| `ds/understand.js` | `data-s="understand"` — `loadUnderstand`, `runUnderstand`, `vizSelectInstrument`, `openVizModal`, `closeVizModal`, `runPortfolioOverview` |
| `ds/dashboard.js` | `data-s="dashboard"` — `loadDashboard` |
| `ds/pipeline.js` | `data-s="pipeline"` — `runBuild`, `runReuse`, `resetSession`, `checkStatus`, `loadInstruments`, `loadActiveInstrument` (writes `state.activeInst`) |
| `ds/performance.js` | `data-s="performance"` — `loadPerformance`, `switchPerfTab` (reads `state.activeInst`) |
| `ds/risk.js` | `data-s="risk"` — `loadRisk` |
| `ds/trades.js` | `data-s="trades"` — `loadTrades` (reads `state.activeInst`) |
| `ds/explain.js` | `data-s="explain"` — `loadExplain` |
| `ds/scenarios.js` | `data-s="scenarios"` — `loadScenariosPage`, `runPortfolioScenario` |
| `ds/training.js` | `data-s="training"` — `loadTraining`, `switchTrainTab` |
| `ds/changelog.js` | `data-s="changelog"` — `loadChangelog`, `saveChangelog` |
| `ds/observability.js` | `data-s="observability"` — `loadObservability` |
| `ds/mcp.js` | `data-s="mcp"` — `loadMCP` |
| `ds/export.js` | `data-s="export"` — `loadExport`, `pingAPI`, `dlJSON` |
| `ds/experiment-results.js` | `data-s="experiment-results"` — `loadExperimentResults`, `downloadExperimentResults` (reads `state.activeInst`) |
| `ds/trade-diagnostics.js` | `data-s="trade-diagnostics"` — `loadTradeDiagnostics` |
| `ds/model-train-progress.js` | `data-s="model-train-progress"` — `loadModelTrainProgress` |
| `ds/model-observability.js` | `data-s="model-observability"` — `loadModelObservability` |
| `ds/model-mcp.js` | `data-s="model-mcp"` — `loadModelMcp` |
| `ds/model-audit.js` | `data-s="model-audit"` — `loadModelAudit` |
| `ds/concepts.js` | `data-s="concepts"` — `loadConcepts`, `switchConceptTab(phase, el)`. CRISP-DM methodology page: 6 phases × 3 Chart.js charts = 18 charts total. Each phase: full-width description → key fact pills → 3-chart grid. Phase 4 SHAP field is `"Overall"` (capital O). TD Loss chart (cp4-c1) fall-back order: live `_live_progress` → persisted `GET /api/v1/training-metrics` → Sharpe-per-round from history. Duration field in step-log is `duration_secs` (not `duration_s`). Canvas IDs follow pattern `cp{1-6}-c{1-3}`. Auth bypass for localhost (early-return matching FnO pattern). Added `58767cb`. |

### ds.html Section Inventory (all 20 sections extracted)

| Section key (`data-s`) | Page title | Module | Status |
|---|---|---|---|
| `understand` | Understand Data | `ds/understand.js` | Extracted |
| `dashboard` | Dashboard | `ds/dashboard.js` | Extracted |
| `pipeline` | Pipeline | `ds/pipeline.js` | Extracted |
| `performance` | Performance | `ds/performance.js` | Extracted |
| `risk` | Risk View | `ds/risk.js` | Extracted |
| `trades` | Trade Journal | `ds/trades.js` | Extracted |
| `explain` | Explainability | `ds/explain.js` | Extracted |
| `scenarios` | Portfolio Scenarios | `ds/scenarios.js` | Extracted |
| `training` | Training Metrics | `ds/training.js` | Extracted |
| `changelog` | Model Changelog | `ds/changelog.js` | Extracted |
| `observability` | Observability | `ds/observability.js` | Extracted |
| `mcp` | MCP Calls | `ds/mcp.js` | Extracted |
| `export` | Export & DevOps | `ds/export.js` | Extracted |
| `experiment-results` | Experiment Results | `ds/experiment-results.js` | Extracted |
| `trade-diagnostics` | Trade Diagnostics | `ds/trade-diagnostics.js` | Extracted |
| `model-train-progress` | Training Progress | `ds/model-train-progress.js` | Extracted |
| `model-observability` | Model Observability | `ds/model-observability.js` | Extracted |
| `model-mcp` | Model MCP Calls | `ds/model-mcp.js` | Extracted |
| `model-audit` | Model Audit | `ds/model-audit.js` | Extracted |
| `concepts` | CRISP-DM Concepts | `ds/concepts.js` | Extracted — added `58767cb` |

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
  threadId: randomUUID(),  // unique per session — uses shared/utils.js safe fallback (HTTP-compatible)
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
**Consumer:** `market-signals.js` → `loadMarketSignals()`, `loadGoalHint()`; also `learnings.js` → `loadLearnings()` (Card 4 trend charts + Investment Workflow agent tabs a2/a3/a4/a5: reads `date`, `Close`, `rsi_14`, `macd`, `trend_score`, `ema_5/13/26/50`)
**Response fields (per row):**
```
date, Close, Volume,
rsi_14, macd, macd_signal, macd_hist,
bb_upper, bb_lower, bb_pct_b,
atr_14, ema_5, ema_13, ema_26, ema_50, trend_score
```
**DOM targets:** `ms-rsi-val/sig`, `ms-macd-val/sig`, `ms-bb-val/sig`, `ms-ema5/13/26-val/sig`, `ms-atr-val/sig`, `ms-trend-val/sig`, `ms-data-range`, `ms-last-updated` (date + time, format: `Last updated: D MMM YYYY HH:MM`; `—` on null/error), `ms-alerts`
**Charts:** `chart-ms-pv`, `chart-ms-rsi`, `chart-ms-macd`, `chart-ms-bb`, `chart-ms-ema`, `chart-ms-atr`, `chart-ms-trend`

### Investment Workflow & Agents (Feature 31) — `learnings.js` → `loadLearnings()` → `loadAgentWorkflow()`
Reuses existing endpoints only (no new path); all loaded via `Promise.allSettled`, one tab's failure renders `_noData(canvasId)` without breaking the page. `switchAgentTab(agentKey, el)` toggles `.concept-tab`/`.concept-panel` (panel id prefix `aw-`).
- `GET /api/v1/performance-summary` → tab a1 (`aw-a1-c1`): `performance.sharpe_ratio`/`sharpe`, `max_drawdown_pct`/`max_drawdown`, `win_rate_pct`/`win_rate`, `portfolio_total_return_pct`/`total_return_pct`.
- `GET /api/v1/market-signals?...` → tabs a2 (`aw-a2-c1` Close), a3 (`aw-a3-c1` `trend_score`), a4 (`aw-a4-c1` `rsi_14`, `aw-a4-c2` `macd`), a5 (`aw-a5-c1` `Close`+`ema_5/13/26/50`).
- `GET /api/v1/experience/rita/backtest-daily?instrument=NIFTY` → tab a6 (`aw-a6-c1`): `date`, `strategy_value`, `bh_value`.
- `GET /api/v1/shap` → tab a7 (`aw-a7-c1`): array of `{feature, Overall}` (capital-O `Overall`).
- `GET /api/v1/experience/rita/training-history?instrument=NIFTY` → tab a8 (`aw-a8-c1`): `round`, `backtest_return_pct`, `backtest_sharpe`.

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
yearly_returns: [{year: string, return_pct: float}, ...],
last_12m_return
```
**JS reads:** `r.annualised_target`, `r.required_monthly`, `r.last_12m_return`, `r.yearly_returns[].year/.return_pct`. `Suggested Target` is avg of `yearly_returns[].return_pct`.

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

### `GET /api/v1/experience/rita/agent-performance`
**Consumer:** `agent-performance.js` → `loadAgentPerformance()`
**Shape:** `{ agents: [ { agent_name, gap_status, invocation_count_30d, outcome_match_rate, trend_vs_prior_30d } ] }` — always 7 agents
**Key fields:** `agent_name`, `gap_status`, `invocation_count_30d`, `outcome_match_rate` (null until backfill → renders `—`), `trend_vs_prior_30d` (null when prior window empty → renders `—`)

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

9. **Strategy Comparison (`strategy-comparison.js`)** — reads `GET /api/v1/experience/rita/strategy-comparison?instrument=X&year=Y`. Response fields: `instrument`, `year`, `dates` (ISO strings), `strategies` (list of `{name, equity, color}`), `summary` (list of `{name, total_return_pct, sharpe, max_drawdown_pct, n_trades, win_rate_pct, final_value}`), `error` (nullable). Commentary via `POST /api/v1/commentary` with `{app:"rita", page:"strategy-comparison", instrument}`. Instrument pills from hardcoded `_INSTRUMENTS` list. `apiFetch` imported from `'../shared/api.js'` (not `./api.js` which only re-exports `api`).

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
