# RITA - HTML Frontend Specifications

This document outlines the architecture, design constraints, and purposes of the HTML files within the `dashboard/` directory. These files form the Experience Layer of the RITA platform.

## Design & Technical Constraints

1. **Pure Vanilla Web Stack**: 
   - Strict adherence to Vanilla HTML, Vanilla JavaScript (ES Modules), and pure CSS.
   - **DO NOT USE** React, Vue, Svelte, or any other JavaScript framework.
   - **DO NOT USE** Tailwind CSS, Bootstrap, or any other CSS framework.
2. **Styling and Theming**:
   - All styling is centralized via CSS variables documented in the `<style>` tags or `css/responsive.css`. Follow existing palettes (`--surface`, `--border`, `--text`, `--build`, `--run`, `--warn`).
   - Use dynamic interactions (hover states, transitions) heavily. Keep the UI feeling modern and responsive.
3. **Data Fetching**:
   - The UI communicates strictly with the Experience Layer API (`/api/experience/...`), fetching pre-composed payloads.
4. **Charting**:
   - `Chart.js` is utilized for all graphics, graphs, and performance charts. Avoid introducing D3 or Recharts.

---

## File Specifications

### 1. `index.html` (Welcome Portal)
- **Purpose**: The entry point of the frontend application. It acts as a router/landing page that directs the user to different personas or apps within RITA.
- **Key Sections**:
  - Hero banner with system readiness status.
  - Four primary navigation tiles:
    1. **Research (Data Scientist Lab)** -> routes to `ds.html`
    2. **Portfolio Builder (RITA core)** -> routes to `rita.html`
    3. **Portfolio Review (FnO Tracker)** -> routes to `fno.html`
    4. **Operations (Ops Portal)** -> routes to `ops.html`

### 2. `rita.html` (Portfolio Builder / RITA Core)
- **Purpose**: The core user interface for retail investors or quantitative traders to build, backtest, and evaluate their portfolios using the Double DQN model.
- **Sections (Phases)**:
  - **Phase 01 (Plan)**: Financial Goal setting, Market Analysis (fetching latest MACD/RSI indicators), and Strategy formulation.
  - **Phase 02 (Backtest)**: Scenarios to configure backtesting date boundaries.
  - **Phase 03 (Analyse)**: Performance (comparing returns against benchmarks), Trade Journal, and Model Explainability (SHAP values).
  - **Phase 04 (Monitor)**: Live Risk Views, Training Progress, and Observability.
- **Interacts with**: `/api/experience/dashboard` endpoint and underlying `workflow` triggers.

### 3. `fno.html` (FnO Portfolio Manager)
- **Purpose**: A specialized tracker for Futures and Options positions. Focuses heavily on Greeks, margin utilization, and hedging tools.
- **Sections**:
  - **Positions**: Active and closed trades with Unrealized/Realized P&L.
  - **Margin Tracker**: Estimates SPAN and exposure margins for active baskets.
  - **Risk & Greeks**: Aggregates Delta, Theta, and Vega across the portfolio. Stress scenarios (P&L at different underlying levels).
  - **Risk-Reward & Hedge History**: Tools for scenario planning and tracking anchor positions and reactive hedges.

### 4. `ops.html` (Operations Portal)
- **Purpose**: Used by the platform engineers and DevOps to ensure the health of the RIIA system.
- **Sections**:
  - **Monitoring**: Real-time stats on API latency, error rates, and endpoints.
  - **CI / CD Pipeline**: Tracks the state of linting, unit testing, and Playwright execution matrices.
  - **Deployments**: Details on the FastAPI and Streamlit environments, environment variables, and ports.
  - **Observability & Chat Analytics**: Model drift monitoring and query volume logs for the chat-based RITA assistant.

### 5. `ds.html` (Data Scientist Lab)
- **Purpose**: The advanced view for model developers to tweak the reinforcement learning model, re-train hyperparameters, and iterate on features.
- **Sidebar sections:**

| Nav label | Section id | Color | Description |
|---|---|---|---|
| Understand | `s-understand` | `c-ds` | Default landing. Instrument data viz (distributions, correlation, time series, clustering). Includes **Portfolio pill** for cross-instrument view. |
| Dashboard | `s-dashboard` | `c-text` | Last build KPIs (Return, CAGR, Sharpe, MDD, Win Rate) + constraint status + last run summary. |
| Build | `s-pipeline` | `c-ds` | Two pipeline panels: **Build Model Pipeline** (retrain from scratch) and **Re-use Model Pipeline** (load existing, run backtest). Each panel has instrument selector, timesteps, seeds, date range, inline 8-step progress bar. |
| Scenarios | `s-scenarios` | `c-ds` | **Portfolio backtest panel.** Instrument checkboxes (NIFTY/BANKNIFTY/ASML/NVIDIA) + EUR allocation per instrument + date range → `POST /api/v1/portfolio/backtest`. Results: 4-KPI row (Sharpe, MDD, Return, CAGR) + per-instrument table + cumulative return chart. |
| Performance | `s-performance` | `c-build` | Backtest performance analytics (comparison vs B&H, drawdown, rolling metrics). |
| Risk View | `s-risk` | `c-build` | Portfolio VaR, drawdown budget, trade risk impact, regime confidence. |
| Trade Journal | `s-trades` | `c-build` | Entry/exit signals on price chart, phase-by-phase analysis. |
| Explainability | `s-explain` | `c-build` | SHAP / model explain panel. |
| Training Progress | `s-training` | `c-run` | Live training curves (loss, ep_rew_mean vs timestep). |
| Model Changelog | `s-changelog` | `c-run` | Compare versions of trained `.zip` models. |
| Observability | `s-observability` | `c-mon` | API metrics, drift status, system health. |
| MCP Calls | `s-mcp` | `c-mon` | MCP call log panel. |
| Export & DevOps | `s-export` | `c-warn` | Pipeline step export buttons, DevOps info. |

- **Understand section — Portfolio pill** (added 2026-04-15):
  - A special `📊 Portfolio` pill appended to the instrument list with id `__portfolio__`.
  - Clicking it and pressing **Understand Data** calls `runPortfolioOverview()` → `GET /api/v1/portfolio/overview`.
  - Renders `#viz-portfolio-results`: instrument coverage cards, normalized price chart (`chart-vp-returns`), correlation matrix table (`vp-corr-table`).
  - KPI ids: `vp-count`, `vp-days`, `vp-from`, `vp-to`; grid id: `vp-inst-grid`.

- **Scenarios section — Portfolio backtest** (added 2026-04-15):
  - Fixed instrument set: NIFTY 50, BANKNIFTY, ASML, NVIDIA — checkboxes `sc-inst-{id}`, allocation inputs `sc-alloc-{id}`.
  - Total capital display: `#sc-total` (live-updated by `scUpdateTotal()`).
  - Date pickers: `sc-from`, `sc-to`. Run button: `btn-sc`, spinner `sc-spinner`, status badge `sc-status`.
  - Results injected into `#sc-result`: KPI row + per-instrument table + `chart-sc-portfolio` line chart.
  - API: `POST /api/v1/portfolio/backtest` — body `{ instruments[], allocations_eur{}, start_date, end_date }`.
  - Response fields: `sharpe_ratio`, `max_drawdown_pct`, `portfolio_total_return_pct`, `benchmark_total_return_pct`, `portfolio_cagr_pct`, `instruments_count`, `total_eur_allocated`, `instruments[]` (per-instrument: `id, name, currency, allocated_eur, return_pct, sharpe, weight_pct`), `daily[]` (`date, portfolio_value, benchmark_value`), optional `instrument_series{}` (per-instrument daily values for individual lines).

- **JS architecture**: All JS is inline in `<script>` at bottom of file (no ES module subtree — unlike rita/fno/ops). Uses same `mkChart(id, type, data, extra)` and `CHARTS` registry pattern but with different function signature than `js/rita/charts.js`.
- **Navigation**: `show(sectionId, el)` function — adds `active` class to `#s-{sectionId}` and calls registered loader. Add new sections to the `loaders` map inside `show()`.
- **Instrument list** for Build dropdowns: populated from `GET /api/v1/instruments` into `#b-instrument` and `#r-instrument` selects via `loadInstruments()`.
- **Active instrument pill** in topbar: updated by `loadActiveInstrument()` — elements `inst-pill`, `inst-pill-flag`, `inst-pill-name`, `inst-pill-exch`.
