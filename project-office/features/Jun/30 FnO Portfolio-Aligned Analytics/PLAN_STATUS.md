# Feature 30 — FnO Portfolio-Aligned Analytics: Plan Status

**Last updated:** 2026-06-10
**Overall status:** `[x] Complete — all 6 phases merged; specs updated (e983a0d)`
**Requirements:** `project-office/features/Jun/30 FnO Portfolio-Aligned Analytics/REQUIREMENTS.md`
**Eng context:** `project-office/features/Jun/30 FnO Portfolio-Aligned Analytics/eng-context.md`

---

## Phase Summary

| Phase | Title | Status | Commits |
|---|---|---|---|
| Phase 1 | Backend analytics endpoint | `[x] Merged` | a3ba34a |
| Phase 2 | State + initApp refactor | `[x] Merged` | 7bfb90c (merge), cb5eeba (QA) |
| Phase 3 | Overview redesign + analytics rendering wiring | `[x] Merged` | 559c65e (merge), 92bd2cf (hotfix) |
| Phase 4 | Manoeuvre tab re-wire | `[x] Merged` | included in Phase 3 (559c65e) |
| Phase 5 | Stress/Scenarios page updates | `[x] Merged` | included in Phase 3 (559c65e) |
| Phase 6 | Spec updates | `[x] Complete` | e983a0d (2026-06-07) |

---

## Phase 1 — Backend analytics endpoint

**Status:** `[x] Merged — a3ba34a (2026-06-04); 15/15 QA tests`
**Effort estimate:** 3 days
**Files:**
- `src/rita/api/experience/portfolio_analytics.py` (new)
- `src/rita/main.py` (register router)

### Tasks

| # | Task | Status | Notes |
|---|---|---|---|
| 1.1 | Mock data constants — MOCK_PORTFOLIO dict with all 5 instruments, pre-computed greeks/stress/scenarios | `[x]` | No DB calls; return immediately when `mode=mock` |
| 1.2 | Real data path — load `user_portfolio` via `UserPortfolioRepo`, `user_hedge_plans` via `UserHedgePlanRepo` | `[x]` | 404 if no portfolio; see eng-context C1 |
| 1.3 | Geography-overview data fetch — reuse `geography_overview()` logic for `ann_vol_pct`, `return_1y_pct`, `risk_score`, `region` per instrument | `[x]` | Import from `experience/rita.py` or extract to shared util |
| 1.4 | Market data — pull latest from `MarketDataCacheRepository` for all portfolio instruments | `[x]` | Same as portfolio_summary currently does |
| 1.5 | Greek computation — reuse `_compute_bs_price()` from `portfolio_hedge.py`; derive delta/theta/vega per holding based on hedge plan selections | `[x]` | See eng-context C2 |
| 1.6 | Scenario computation — ±2σ/±1σ/flat moves per holding; sum weighted P&L | `[x]` | See eng-context C3 |
| 1.7 | Payoff grid — 20-point price grid (±30%); unhedged vs hedged portfolio value curves | `[x]` | See eng-context C4 |
| 1.8 | Stress scenarios — 5 hardcoded events applied to portfolio; hedged vs unhedged P&L | `[x]` | See eng-context C5 |
| 1.9 | Hedge quality score (HQS) — 0–100 per instrument (is_hedged 40pts + cost_vs_risk 30pts + coverage_match 30pts) | `[x]` | See eng-context C6 |
| 1.10 | net_greeks + net_delta aggregation across all holdings | `[x]` | Simple weighted sum |
| 1.11 | Register router in `main.py` | `[x]` | Under experience routers block |
| 1.12 | QA: 12 unit tests | `[x]` | mock returns no DB calls; real 401/404/200; greeks sign (put = negative theta); stress has 5 entries |

### Acceptance Gate
`?mode=mock` returns full payload. `?mode=real` returns 401 without JWT, 404 with no portfolio, full payload otherwise. All state fields consumed by `app-init.js` are present in the response.

---

## Phase 2 — State + initApp refactor

**Status:** `[x] Merged — 7bfb90c (2026-06-04); Real/Mock toggle; contract tests cb5eeba`
**Effort estimate:** 1 day
**Files:**
- `dashboard/js/fno/state.js`
- `dashboard/js/fno/app-init.js`
- `dashboard/js/fno/nav.js`
- `dashboard/fno.html`

### Tasks

| # | Task | Status | Notes |
|---|---|---|---|
| 2.1 | `state.js` — add `portfolioMode: 'real'`, `portfolioMeta: {}` | `[x]` | Read from `sessionStorage('fno_portfolio_mode')` on init |
| 2.2 | `app-init.js` — replace `initApp()`: single fetch to `portfolio-analytics?mode=${state.portfolioMode}` | `[x]` | See eng-context C7 |
| 2.3 | `app-init.js` — remove `fetchPositions()`, `loadEquityHedge()` call, `rita:asml-state-updated` event listener | `[x]` | equity_hedge.js still importable but no longer called from init |
| 2.4 | Auto-fallback: if `mode=real` returns 404 → switch to mock, set `state.portfolioMode='mock'`, show banner | `[x]` | Banner: "No portfolio saved — showing demo data. Build yours →" (links to RITA Portfolio Builder) |
| 2.5 | `nav.js` / `fno.html` — Real/Mock toggle pill in sidebar | `[x]` | Matches Paper/Live pill style; on click: update state, persist sessionStorage, call `initApp()` |
| 2.6 | QA: browser test — load page, check no flicker, toggle mock↔real, verify re-render | `[x]` | |

### Acceptance Gate
Single API call on page load. No position count flicker. Toggle works. First-time user (no portfolio) sees mock data with banner.

---

## Phase 3 — Positions tab re-skin

**Status:** `[x] Merged — 559c65e (2026-06-04); hotfix 92bd2cf (null guard + instrument selector)`
**Effort estimate:** 0.5 days
**Files:**
- `dashboard/js/fno/positions.js`
- `dashboard/fno.html`

### Tasks

| # | Task | Status | Notes |
|---|---|---|---|
| 3.1 | KPI strip — replace with: Total Value€ · Weighted 1Y Return · Weighted Ann Vol · Hedge Coverage% | `[x]` | Read from `state.portfolioMeta` + `state.positions` |
| 3.2 | Holdings table — new columns: Instrument · Region · Alloc% · Position€ · 1Y Return (ind.) · Ann Vol · Hedged? | `[x]` | Drop strike, side, FUT/CE/PE badges, qty, avg, ltp |
| 3.3 | Remove expiry pills from Positions section | `[x]` | Pills may stay in sidebar if other sections still use them |
| 3.4 | Hedged? column — pull from `state.hedge_quality.positions` lookup by instrument | `[x]` | Show strategy label (put_buy/call_sell) or "—" |

### Acceptance Gate
No expiry pills. No F&O-specific columns. Holdings table shows equity data. KPI strip shows portfolio-level metrics.

---

## Phase 4 — Manoeuvre tab re-wire

**Status:** `[x] Merged — delivered within Phase 3 (559c65e)`
**Effort estimate:** 1 day
**Files:**
- `dashboard/js/fno/manoeuvre.js`
- `dashboard/fno.html`

### Tasks

| # | Task | Status | Notes |
|---|---|---|---|
| 4.1 | Portfolio Alerts section — per-instrument flag cards using `state.hedge_quality.positions` | `[x]` | Flags: unhedged + ann_vol > 40%, HQS < 40, alloc > 35% |
| 4.2 | Suggested Actions section — actionable cards derived from alerts | `[x]` | Deep-link to Portfolio Hedge section with instrument pre-selected |
| 4.3 | Move existing month/expiry/snapshot sections below, labelled "Options Activity" | `[x]` | No functional change to existing code — layout only |

### Acceptance Gate
Portfolio Alerts and Suggested Actions render from state (no new API call). At least one suggestion card when NVIDIA is unhedged at 20% allocation with 55% vol. Options Activity still works.

---

## Phase 5 — Stress/Scenarios updates

**Status:** `[x] Merged — delivered within Phase 3 (559c65e)`
**Effort estimate:** 0.5 days
**Files:**
- `dashboard/js/fno/stress.js`
- `dashboard/js/fno/rr.js`

### Tasks

| # | Task | Status | Notes |
|---|---|---|---|
| 5.1 | `stress.js` — replace `computeFilteredStress()`: read from `state.stressData` array; show hedged vs unhedged columns | `[x]` | See eng-context C5 for shape |
| 5.2 | `rr.js` `renderScenarios()` — add σ-based portfolio scenario cards from `state.scenarioLevels`; keep per-instrument bull/bear section below | `[x]` | |
| 5.3 | Add "(indicative)" to all scenario/stress P&L figures | `[x]` | |

### Acceptance Gate
Stress page shows 5 crisis events with both columns. Scenario page shows σ-move portfolio P&L. Flat scenario is always the middle card.

---

## Phase 6 — Spec updates

**Status:** `[x] Complete — e983a0d (2026-06-07)`
**Effort estimate:** 30 min

| Spec | Update |
|---|---|
| `Spec_Python_Code.md` | Add `portfolio_analytics.py` to Experience Layer table |
| `Spec_JS_Code.md` | Update `app-init.js`, `state.js`, `positions.js`, `manoeuvre.js` notes |
| `Spec_HTML_Code.md` | Document Real/Mock toggle; updated Positions section layout |
| `Spec_RITA_App.md` | Add `GET /api/v1/experience/fno/portfolio-analytics` to API inventory |

---

## Session Log

| Date | Session | Work Done |
|---|---|---|
| 2026-06-04 | Analysis + Phase 1 | Diagnosed 3 bugs (pos count flicker, empty analysis pages, manoeuvre paper-data mismatch). Designed F30 architecture. Created feature folder. Ran /enhance: Phase 1 backend endpoint built and merged (a3ba34a). 2 new files (schemas/portfolio_analytics.py, api/experience/portfolio_analytics.py), auth.py extended, main.py wired. 15/15 QA tests pass. Confluence Engineering v45. |
| 2026-06-04 | Phases 2–5 | Phase 2 state + initApp refactor with Real/Mock toggle merged (7bfb90c; contract tests cb5eeba). Phase 3 overview redesign + analytics rendering wiring merged (559c65e; hotfix 92bd2cf). Phases 4 + 5 delivered within the Phase 3 merge. EOD commit 229aedb. |
| 2026-06-07 | Phase 6 | Spec updates committed (e983a0d) alongside F29 Phase 4 — status verified after being falsely marked complete earlier. |
| 2026-06-10 | Closure | Documentation sweep — PLAN_STATUS marked Complete; all phase statuses and task checkboxes finalised. |
