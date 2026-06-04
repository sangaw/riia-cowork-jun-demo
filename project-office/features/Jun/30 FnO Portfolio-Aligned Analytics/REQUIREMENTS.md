# Feature 30 — FnO Portfolio-Aligned Analytics

**Created:** 2026-06-04
**Owner:** Engineer (full-stack) · Architect (analytics design)
**Status:** `[ ] Not started`
**Guardrail refs:** org · engineer-role · rita-project
**Affected specs:** Spec_Python_Code.md · Spec_JS_Code.md · Spec_HTML_Code.md · Spec_RITA_App.md · Spec_DB.md
**Affected skills:** add-fno-feature · add-endpoint · add-data-feature

---

## Context & Motivation

RITA is a **research platform** — not a trading system. All computed values (premiums, greeks, P&L projections) are **indicative and illustrative** for visualisation and concept demonstration only.

After Features 26–29 the FnO module has two parallel data worlds that do not talk to each other:

**World A — User equity portfolio** (`user_portfolio` table)
- 5 equity holdings (e.g. NIFTY 30%, BANKNIFTY 20%, ASML 20%, NVIDIA 20%, TRU 10%)
- Shown correctly on: My Portfolio (Overview), Portfolio Hedge

**World B — F&O paper trading positions** (`paper_positions` table)
- 2 dummy NIFTY/BANKNIFTY options positions used for study
- Shown (incorrectly) on: FnO Dashboard, Positions tab
- Loaded from a backend endpoint that does NOT return greeks, scenarios, stress, or hedge quality

The consequence is that **Risk/Greeks, Scenarios (RR), Payoff, Stress, and Hedge Radar pages all render empty** — the `initApp()` call in `app-init.js` tries to read `d.greeks`, `d.scenario_levels`, etc. from `/api/v1/portfolio/summary`, but that endpoint never returns those fields. Additionally the Dashboard position count flickers from 2 → 4 as ASML equity hedge positions are injected asynchronously after the initial render.

This feature unifies all FnO analysis pages under the user's equity portfolio as the single source of truth and introduces a **Real / Mock data toggle** to support both authenticated users and demo/first-time scenarios.

---

## Design Decisions

| # | Decision | Resolution |
|---|---|---|
| D1 | Source of truth for all FnO analysis | **User equity portfolio** (`user_portfolio` table). F&O paper positions are retired as the analysis source. |
| D2 | Mock / demo data | A **hardcoded 5-instrument demo portfolio** is returned when `mode=mock`. No DB calls made in mock path. |
| D3 | Mode toggle scope | Toggle lives in the FnO sidebar. Selection persists in `sessionStorage('fno_portfolio_mode')`. Default = `'real'`. Falls back to `'mock'` automatically if the user has no saved portfolio. |
| D4 | Greeks source | Greeks are **derived from the saved hedge plan** (Portfolio Hedge selections). If no hedge plan exists, delta = 1.0 per holding, theta/vega/gamma = 0. |
| D5 | Scenarios are σ-based | Scenario moves are ±2σ / ±1σ / flat computed from each holding's `ann_vol_pct` (from portfolio-hedge Black-Scholes). Portfolio P&L = weighted sum of per-holding P&L. |
| D6 | Stress scenarios | **5 hardcoded crisis events** (2008 crash, COVID-2020, 2022 rate hike, Tech rally, India slowdown). Applied as flat % moves to the full portfolio; hedged vs unhedged comparison computed per event. |
| D7 | Payoff chart | Portfolio value across a price grid (±30% from current) — one curve for unhedged, one for hedged (if plan exists). Computed on the backend for consistency. |
| D8 | Hedge quality score (HQS) | 0–100 per instrument: hedged (40 pts) + cost efficiency vs risk level (30 pts) + coverage match (30 pts). |
| D9 | Existing pages not replaced | My Portfolio (Overview), Portfolio Hedge, and Hedge History sections keep their own fetch flows. Only the `initApp()` data initialisation path is replaced. |
| D10 | Extensibility seam | The `mode` query param is the extensibility seam. Future modes (shared portfolio, advisor view, stress-test demo) add one `elif` branch on the backend and one pill button on the frontend — no other changes needed. |
| D11 | All values indicative | Every computed metric carries an "(indicative)" or "illustrative" label in the UI. No changes to existing disclaimer policy. |

---

## Problem Diagnosis (from session 2026-06-04)

### Bug 1 — Dashboard position count flickers 2 → 4
`initApp()` in `app-init.js` makes two position-loading calls:
1. `/api/v1/portfolio/summary` → `d.positions` is `undefined` → `state.positions = []`
2. `fetchPositions()` → `/api/v1/portfolio/positions?mode=paper` → sets `state.positions` to 2 paper positions
3. `loadEquityHedge(false)` fires **asynchronously** → `injectAsmlToState()` appends 2 synthetic ASML CE+PE positions → dispatches `rita:asml-state-updated` → re-renders dashboard to 4

### Bug 2 — Risk, Greeks, Scenarios, Stress, Payoff, Hedge Radar all render empty
`initApp()` reads `d.greeks`, `d.scenario_levels`, `d.stress`, `d.payoff`, `d.hedge_quality`, `d.net_delta`, `d.net_greeks`, `d.margin` from `/api/v1/portfolio/summary`. That endpoint does **not** return any of these fields. They default to `[]` / `{}` permanently.

### Bug 3 — Manoeuvre uses paper positions (not equity portfolio)
Manoeuvre fetches `/api/v1/portfolio/man-groups` and filters `state.positions` — both rooted in the F&O paper trading system. The equity portfolio has no representation here.

---

## New Endpoint Contract

### `GET /api/v1/experience/fno/portfolio-analytics?mode=real|mock`

No auth required for `mode=mock`. JWT required for `mode=real`.

**Response shape** (must match the fields `app-init.js` currently reads from state):

```json
{
  "mode": "real",
  "portfolio_meta": {
    "name": "My Portfolio",
    "total_value_eur": 50000,
    "updated_at": "2026-06-04T10:00:00"
  },
  "market": {
    "NIFTY":     { "close": 24200, "chgFromOpen": 0.8, "date": "2026-06-04" },
    "BANKNIFTY": { "close": 52100, "chgFromOpen": -0.3, "date": "2026-06-04" },
    "ASML":      { "close": 890.5, "chgFromOpen": 1.2, "date": "2026-06-04", "currency": "EUR" },
    "NVIDIA":    { "close": 132.4, "chgFromOpen": 2.1, "date": "2026-06-04", "currency": "USD" },
    "TRU":       { "close": 18.2,  "chgFromOpen": 0.4, "date": "2026-06-04", "currency": "EUR" }
  },
  "positions": [
    {
      "und": "NIFTY", "full": "NIFTY  30%", "exp": "EQUITY", "type": "EQ",
      "side": "Long", "qty": 1, "allocation_pct": 30, "position_eur": 15000,
      "avg": 0, "ltp": 0, "chg": 0.8, "pnl": 0, "currency": "EUR",
      "ann_vol_pct": 18.4, "region": "India"
    }
  ],
  "greeks": [
    {
      "und": "NIFTY", "exp": "EQUITY",
      "delta": 0.5,       "gamma": 0.002,
      "theta": -1.23,     "vega": 45.0,
      "allocation_pct": 30,
      "ann_vol_pct": 18.4, "sigma_eur": 2760,
      "hedge_type": "put_buy",
      "put_cost_eur": 450, "call_income_eur": 0,
      "net_theta_eur_day": -1.23
    }
  ],
  "net_greeks": {
    "delta": 3.2, "theta": -4.8, "vega": 180.0
  },
  "net_delta": { "NIFTY": 0.5, "BANKNIFTY": 0.5, "ASML": -0.2, "NVIDIA": 1.0, "TRU": 1.0 },
  "scenario_levels": {
    "NIFTY":     { "target": 25000, "sl": 22000 },
    "BANKNIFTY": { "target": 55000, "sl": 48000 }
  },
  "payoff": {
    "portfolio": { "labels": [35000, 36000, "..."], "data": [-8000, -6000, "..."] },
    "hedged":    { "labels": [35000, 36000, "..."], "data": [-4000, -3000, "..."] }
  },
  "stress": [
    { "label": "2008 Crisis",    "move_pct": -50, "portfolio_pnl_eur": -25000, "hedged_pnl_eur": -12000 },
    { "label": "COVID-2020",     "move_pct": -35, "portfolio_pnl_eur": -17500, "hedged_pnl_eur":  -8500 },
    { "label": "Rate Hike 2022", "move_pct": -20, "portfolio_pnl_eur": -10000, "hedged_pnl_eur":  -5500 },
    { "label": "Tech Rally",     "move_pct": +25, "portfolio_pnl_eur": +12500, "hedged_pnl_eur":  +8000 },
    { "label": "India Slowdown", "move_pct": -15, "portfolio_pnl_eur":  -7500, "hedged_pnl_eur":  -4000 }
  ],
  "hedge_quality": {
    "positions": [
      { "instrument": "NIFTY",     "hqs": 82, "hqs_tier": "green",  "hedged": true,  "strategy": "put_buy", "coverage_pct": 50 },
      { "instrument": "BANKNIFTY", "hqs": 74, "hqs_tier": "green",  "hedged": true,  "strategy": "put_buy", "coverage_pct": 50 },
      { "instrument": "ASML",      "hqs": 55, "hqs_tier": "yellow", "hedged": true,  "strategy": "call_sell", "coverage_pct": 50 },
      { "instrument": "NVIDIA",    "hqs": 0,  "hqs_tier": "red",    "hedged": false, "note": "No hedge configured" },
      { "instrument": "TRU",       "hqs": 0,  "hqs_tier": "red",    "hedged": false, "note": "No hedge configured" }
    ]
  },
  "closed_positions": [],
  "realized_pnl": 0,
  "margin": {}
}
```

---

## Mock Portfolio (mode=mock)

Returns a realistic demo portfolio with no DB calls. Suitable for first-time users and presentation/demo mode.

| Instrument | Region | Alloc% | 1Y Return | Ann Vol | Hedge |
|---|---|---|---|---|---|
| NIFTY | India | 30% | +14.2% | 18.4% | Put Buy |
| BANKNIFTY | India | 20% | +8.7% | 22.1% | Put Buy |
| ASML | EU | 20% | +34.8% | 28.6% | Sell Call |
| NVIDIA | US | 20% | +120.0% | 55.2% | None |
| TRU | EU | 10% | -3.1% | 31.0% | None |

Total mock portfolio value: €50,000 (illustrative).

---

## Architecture Diagram

```
Before Feature 30                     After Feature 30
─────────────────────────────────      ─────────────────────────────────────────
My Portfolio ──► user_portfolio  ✅    My Portfolio ──► user_portfolio  ✅ (unchanged)
Portfolio Hedge ► user_portfolio ✅    Portfolio Hedge ► user_portfolio  ✅ (unchanged)
Dashboard ───────► paper_positions ❌
Risk/Greeks ─────► (empty)        ❌   All FnO analysis pages
Scenarios/RR ────► (empty)        ❌       │
Payoff ──────────► (empty)        ❌       ▼
Stress ──────────► (empty)        ❌   /api/v1/experience/fno/
Hedge Radar ─────► (empty)        ❌   portfolio-analytics?mode=real|mock
Manoeuvre ───────► paper_positions ❌       │
                                        mode=real         mode=mock
                                           │                  │
                                      user_portfolio     MOCK_PORTFOLIO
                                      + hedge_plan       constant
                                      + geo data         (no DB calls)
```

---

## Scope

### In Scope
- New `GET /api/v1/experience/fno/portfolio-analytics?mode=real|mock` endpoint
- `mode=real`: computes from `user_portfolio` + `user_hedge_plans` + geography-overview + market data cache
- `mode=mock`: returns hardcoded demo data (no DB calls)
- `app-init.js` refactored to call portfolio-analytics (replaces summary + fetchPositions chain)
- `state.js` extended: `portfolioMode`, `portfolioMeta`
- Real / Mock toggle in FnO sidebar
- Positions tab re-skinned for equity holdings (columns: Instrument · Region · Alloc% · Position€ · 1Y Return · Ann Vol · Hedged?)
- Manoeuvre tab re-wired: portfolio-level rebalancing/hedge suggestions (instrument risk flagging, unhedged instruments, cost-efficiency alerts)
- ASML async injection (`equity_hedge.js` `injectAsmlToState()`) removed from the init path
- Spec updates (Spec_Python_Code, Spec_JS_Code, Spec_HTML_Code, Spec_RITA_App)

### Out of Scope
- My Portfolio (Overview) — already works, not touched
- Portfolio Hedge — already works, not touched
- Hedge History section — keeps its own fetch flow (`/api/v1/portfolio/hedge-history`)
- Margin tab — no changes; will work automatically with new greeks data in state
- Changes to the Portfolio Builder in `rita.html`
- New Alembic migrations (no new tables — analytics are computed, not stored)
- Any broker integration or order placement

---

## Phases

### Phase 1 — Backend analytics endpoint
**Goal:** Deliver `/api/v1/experience/fno/portfolio-analytics?mode=real|mock` with full payload.

**Files:**
- `src/rita/api/experience/portfolio_analytics.py` (new)
- `src/rita/main.py` (register router)

**Sub-tasks:**
1. Mock data constants module — 5-instrument demo portfolio, pre-computed greeks, scenarios, stress
2. Real data path — load `user_portfolio` (via `UserPortfolioRepo`), `user_hedge_plans` (via `UserHedgePlanRepo`), geo data (reuse `geography_overview()` logic)
3. Greek computation — reuse `_compute_bs_price()` and related functions from `portfolio_hedge.py` to derive delta/theta/vega per holding
4. Scenario computation — apply ±2σ/±1σ moves to each holding's `ann_vol_pct`; sum per-holding P&L weighted by allocation
5. Payoff grid — compute portfolio value at 20 price points (±30% range); hedged vs unhedged curves
6. Stress scenarios — 5 hardcoded crisis %s applied to portfolio; hedged P&L = unhedged P&L × (1 - hedge_coverage%)
7. Hedge quality score (HQS) — per instrument: is_hedged (40 pts) + cost_vs_risk_score (30 pts) + coverage_match (30 pts)
8. Market data — pull latest from `MarketDataCacheRepository` for all portfolio instruments
9. net_greeks and net_delta aggregation
10. Fallback: if `mode=real` but no portfolio saved → return 404 so frontend falls back to mock

**Acceptance criteria:**
- [ ] `?mode=mock` returns full payload with no DB calls (JWT not required)
- [ ] `?mode=real` returns 401 without JWT; 404 if no portfolio saved; full payload otherwise
- [ ] All state fields used by the existing frontend (`positions`, `greeks`, `net_greeks`, `net_delta`, `scenario_levels`, `payoff`, `stress`, `hedge_quality`, `market`) are present in the response
- [ ] `positions` array items include `type='EQ'` and `allocation_pct` fields
- [ ] `stress` array has exactly 5 entries with both `portfolio_pnl_eur` and `hedged_pnl_eur`

---

### Phase 2 — State + initApp refactor
**Goal:** Replace the broken summary + fetchPositions init chain with a single call to portfolio-analytics.

**Files:**
- `dashboard/js/fno/state.js`
- `dashboard/js/fno/app-init.js`
- `dashboard/js/fno/nav.js`
- `dashboard/fno.html`

**Sub-tasks:**
1. `state.js` — add `portfolioMode: 'real'` and `portfolioMeta: {}` fields
2. `app-init.js` — replace `initApp()` body: one `fetch` to `portfolio-analytics?mode=${state.portfolioMode}`; populate all state fields from response
3. `app-init.js` — remove `fetchPositions()`, `loadEquityHedge()` call, and `rita:asml-state-updated` event listener
4. `nav.js` / `fno.html` — add Real/Mock toggle pill to FnO sidebar (matching Paper/Live style); toggle handler updates `state.portfolioMode`, calls `initApp()`, persists to `sessionStorage`
5. If `mode=real` returns 404 (no portfolio) → auto-switch to `mock`, show banner "No portfolio saved — showing demo data. Build yours in Portfolio Builder →"

**Acceptance criteria:**
- [ ] Single API call on load; no position count flicker
- [ ] Real/Mock toggle visible in sidebar; persists across nav within FnO
- [ ] On first visit (no saved portfolio), mock data loads automatically with banner
- [ ] Switching toggle triggers full re-render of all sections

---

### Phase 3 — Positions tab re-skin
**Goal:** Show equity holdings instead of F&O options contracts.

**Files:**
- `dashboard/js/fno/positions.js`
- `dashboard/fno.html`

**Sub-tasks:**
1. Replace KPI strip — 4 KPIs: Total Value€ · Weighted 1Y Return · Weighted Ann Vol · Hedge Coverage%
2. Replace holdings table columns — Instrument · Region · Alloc% · Position€ · 1Y Return (ind.) · Ann Vol · Hedged?
3. Remove expiry pills from the Positions section (equity has no expiry)
4. Remove Paper/Live toggle from Positions section (superseded by Real/Mock at initApp level)
5. Remove F&O-specific badges (FUT/CE/PE, strike, side Long/Short) from the table

**Acceptance criteria:**
- [ ] No expiry pills visible in Positions section
- [ ] Table shows equity fields, not F&O fields
- [ ] Hedged? column shows strategy from `hedge_quality.positions` for that instrument
- [ ] KPI strip shows all 4 values; "—" with hint when `total_value_eur` not set

---

### Phase 4 — Manoeuvre tab re-wire
**Goal:** Manoeuvre becomes portfolio adjustment suggestions rather than F&O options leg management.

**Files:**
- `dashboard/js/fno/manoeuvre.js`
- `dashboard/fno.html`

**Sub-tasks:**
1. New section: **Portfolio Alerts** — per-instrument flags: unhedged + high vol (>40% ann_vol_pct), hedged but HQS < 40, allocation > 35% (concentration risk)
2. New section: **Suggested Actions** — actionable cards: "Add Put Buy for NVIDIA (unhedged, high vol)", "Review ASML collar (HQS 55)", "Rebalance: NVIDIA allocation at 20% exceeds recommended 15% for its vol level"
3. Keep the existing Manoeuvre month/expiry/snapshot sections but clearly label them "Options Activity" and move below the new portfolio sections
4. Wire suggested actions to deep-link into Portfolio Hedge with pre-selected instrument

**Acceptance criteria:**
- [ ] Portfolio Alerts renders immediately from `state.hedge_quality.positions`
- [ ] Suggested Actions generates at least one card when a holding is unhedged and ann_vol_pct > 35%
- [ ] Options Activity section still works for legacy F&O data (no regression)
- [ ] No external API calls in the new sections (reads from state only)

---

### Phase 5 — Stress/Scenarios page updates
**Goal:** Stress and Scenario pages show portfolio-level P&L, not F&O delta × spot moves.

**Files:**
- `dashboard/js/fno/stress.js`
- `dashboard/js/fno/rr.js`
- `dashboard/fno.html`

**Sub-tasks:**
1. `stress.js` — replace `computeFilteredStress()`: read from `state.stressData` (new array from endpoint) instead of computing from greeksData × spot × move; show both unhedged and hedged P&L per event; add a comparison column
2. `rr.js` `renderScenarios()` — add portfolio-level scenario cards derived from `state.scenarioLevels` (σ-based moves); keep the existing per-instrument bull/bear section below
3. Add "(indicative)" subtext to all computed P&L figures

**Acceptance criteria:**
- [ ] Stress page shows all 5 crisis events with hedged vs unhedged columns
- [ ] Scenario page shows portfolio σ-move P&L for all portfolio instruments
- [ ] Flat scenario (0% move) always renders as the middle card

---

### Phase 6 — Spec updates
**Files:** Spec_Python_Code.md · Spec_JS_Code.md · Spec_HTML_Code.md · Spec_RITA_App.md

---

## Dependencies

| Phase | Depends on |
|---|---|
| Phase 1 | F29 Phase 4 complete (spec updates done) |
| Phase 2 | Phase 1 endpoint deployed locally |
| Phase 3 | Phase 2 (state has positions from new endpoint) |
| Phase 4 | Phase 2 (state has hedge_quality) |
| Phase 5 | Phase 2 (state has stress + scenario_levels) |
| Phase 6 | Phases 1–5 complete |

---

## Definition of Done

- [ ] All pages load without blank sections (no empty greeks/scenarios/stress/payoff/hedge-radar)
- [ ] Position count does not flicker on Dashboard
- [ ] Real/Mock toggle works; mock auto-activates when no portfolio saved
- [ ] Stress page shows 5 crisis events with hedged vs unhedged comparison
- [ ] Positions tab shows equity holdings (not F&O paper positions)
- [ ] Manoeuvre tab shows portfolio alerts and suggested actions
- [ ] All computed values labelled "(indicative)"
- [ ] Spec files updated
- [ ] Session committed to git
