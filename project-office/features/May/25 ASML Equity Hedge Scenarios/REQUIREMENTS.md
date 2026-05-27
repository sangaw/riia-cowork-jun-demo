# Feature 25 — ASML Equity Hedge Scenarios

**Created:** 2026-05-27
**Owner:** Engineer
**Status:** `[ ] Not started`
**Guardrail refs:** org · engineer-role · rita-project
**Affected specs:** Spec_JS_Code.md · Spec_HTML_Code.md · Spec_Python_Code.md
**Affected skills:** skill-add-fno-feature.md · skill-add-api-endpoint.md

---

## Objective

Add an **"Equity Hedge"** page to the FnO Portfolio Manager (`fno.html`) that lets a user build an ASML equity portfolio over a selected date range, view its performance, and then explore two hedging strategies at period end — a **covered call** (mild bearish) and a **protective put** (strong bearish) — with a three-way payoff comparison chart.

---

## Background

The FnO Portfolio Manager currently covers only NIFTY and BANKNIFTY derivatives. The `portfolio_engine.py` backend already loads ASML OHLCV data and can run the DDQN backtest over any date range. This feature surfaces that capability in a new dedicated page, adds Black-Scholes option pricing for the hedge scenarios, and renders the results using the existing CSS component library (cards, KPI rows, tables, Chart.js charts) so it feels native to the app.

Volatility is computed from 30-day historical data at period end. A future enhancement (Feature 25b) will add a user-adjustable volatility slider so users can run what-if scenarios — this design must accommodate that without structural changes.

---

## Scope

### In Scope
- New nav item **"Equity Hedge"** (colour `p04`, purple) in `fno.html` sidebar
- New page section `id="page-equity-hedge"` in `fno.html` using only existing CSS classes
- New JS module `dashboard/js/fno/equity_hedge.js`
- Wire into `nav.js` (import + load hook on nav click)
- New backend function `equity_hedge_scenarios()` in `src/rita/core/portfolio_engine.py`
- New API endpoint `POST /api/v1/portfolio/equity-hedge-scenarios` in `src/rita/api/v1/portfolio.py`
- Black-Scholes call and put pricing (server-side, using scipy.stats already in deps)
- Historical 30-day volatility computed from ASML CSV at `end_date`
- Payoff curves: Unhedged · Covered Call · Protective Put across a €100-wide price grid

### Out of Scope
- User-adjustable volatility slider (Feature 25b — future)
- Multi-instrument portfolios (use only ASML)
- Live option chain data / real broker prices
- Touch ds.html or any non-FnO code
- i18n translations (add `data-i18n` attributes as stubs; translations in a separate pass)

---

## Design

### Workflow — 3 Panels on one page

```
[Page header: "Equity Hedge Scenarios"    phase-tag p04]

Panel 1 — Portfolio Builder (card)
  Instrument: ASML | Shares: [10] | From: [2025-01-01] | To: [2025-01-31]
  [Build & Analyse] button → POST /api/v1/portfolio/equity-hedge-scenarios

KPI row c4 (loads after API call)
  Start Price (€) | End Price (€) | Period Return (%) | 30d Volatility (%)

Panel 2 — two-col layout
  Left:  Portfolio Value chart (line, date x-axis, EUR value y-axis, n_shares × price)
  Right: Hedge Overview card
         - Mild Bearish: strategy label, strike, premium received, breakeven
         - Strong Bearish: strategy label, strike, premium paid, breakeven

Panel 3 — two-col layout  (scenario detail cards)
  Left:  Covered Call card  — kpi strip: Strike | Premium Rcvd | Max Value | Breakeven
         One-line plain-English description below the KPIs
  Right: Protective Put card — kpi strip: Strike | Premium Paid | Floor Value | Breakeven
         One-line plain-English description below the KPIs

Panel 4 — Payoff Comparison chart (full width, tall)
  X axis: ASML price at option expiry (€ range)
  Y axis: P&L vs end_date position (€)
  Line 1: Unhedged     (blue,  var(--p02))
  Line 2: Covered Call (green, var(--p01))   — capped above strike
  Line 3: Protective Put (red, var(--neg))   — floored at strike
  Vertical annotation line at current price (end_date close)
```

### API Contract

**Request**
```
POST /api/v1/portfolio/equity-hedge-scenarios
{
  "instrument":  "ASML",
  "n_shares":    10,
  "start_date":  "2025-01-01",
  "end_date":    "2025-01-31"
}
```

**Response**
```json
{
  "portfolio": {
    "start_price":    680.0,
    "end_price":      695.0,
    "total_value_eur": 6950.0,
    "return_pct":     2.21,
    "vol_30d_pct":    28.4,
    "daily": [
      { "date": "2025-01-02", "price": 681.5, "value": 6815.0 },
      ...
    ]
  },
  "hedge_scenarios": {
    "mild_bearish": {
      "strategy":           "covered_call",
      "strike":             730.0,
      "strike_label":       "€730 (+5.0% OTM)",
      "premium_per_share":  18.50,
      "total_premium_eur":  185.0,
      "max_value_eur":      7300.0,
      "breakeven_price":    676.5,
      "description":        "Sell 10 ASML calls at €730. Collect €185 premium; upside capped above €730."
    },
    "strong_bearish": {
      "strategy":           "protective_put",
      "strike":             695.0,
      "strike_label":       "€695 (ATM)",
      "premium_per_share":  22.30,
      "total_premium_eur":  223.0,
      "floor_value_eur":    6727.0,
      "breakeven_price":    717.3,
      "description":        "Buy 10 ASML puts at €695. Pay €223; losses capped below €695."
    },
    "payoff_curves": {
      "price_range":    [550, 560, ..., 870],
      "unhedged":       [...],
      "covered_call":   [...],
      "protective_put": [...]
    }
  }
}
```

### Backend — `equity_hedge_scenarios()` in `portfolio_engine.py`

Steps:
1. Load ASML OHLCV + indicators via `_load_with_indicators("ASML")`
2. Filter to `[start_date, end_date]`; fail if < 5 rows
3. `start_price` = `df_f["Close"].iloc[0]`, `end_price` = `df_f["Close"].iloc[-1]`
4. Compute `vol_30d`: annualised std of daily log-returns for the last 30 trading days at `end_date` (or all rows if < 30)
5. Black-Scholes parameters: `S = end_price`, `T = 30/252`, `r = 0.03` (EUR risk-free, hardcoded)
6. **Covered call** strike = `S × 1.05` (5% OTM); BS call price → `premium_per_share`
7. **Protective put** strike = `S` (ATM); BS put price → `premium_per_share`
8. Build `daily` list: `{date, price, value: price × n_shares}`
9. Build payoff grid: 33 points from `max(100, S × 0.75)` to `S × 1.25`, step rounded to €10
   - `unhedged[i]       = (price_i - end_price) × n_shares`
   - `covered_call[i]   = (min(price_i, call_strike) - end_price) × n_shares + total_call_prem`
   - `protective_put[i] = (max(price_i, put_strike) - end_price) × n_shares - total_put_prem`

### Frontend — `equity_hedge.js`

- `async function loadEquityHedge()` — called on nav click; reads form values, POSTs to API, calls `renderEquityHedge(data)`
- `function renderEquityHedge(data)` — renders KPI strip, portfolio chart, hedge detail cards, payoff chart
- Portfolio line chart: `Chart` type `line`, dataset = `data.portfolio.daily` mapped to `{x: date, y: value}`
- Payoff chart: `Chart` type `line`, 3 datasets from `data.hedge_scenarios.payoff_curves`; tick callback uses `€` prefix, not `₹`
- All monetary values formatted as `€X,XXX.XX` using `toLocaleString('de-DE', {minimumFractionDigits: 2})`
- Date display: `YYYY-MM-DD` (ISO) consistent with rest of app
- State: add `equityHedgeData: null` to `state.js`; set on load; skip re-fetch if already set
- On error: render error message inside `.card` using existing pattern from `hist-loading`

### vol_30d design note (for Feature 25b)

The API response already returns `vol_30d_pct`. When Feature 25b adds the vol slider, the endpoint will accept an optional `volatility_override_pct` field. If present, skip historical vol computation and use override. The frontend renders the slider and re-posts on change. No structural changes to the response shape.

---

## Phases

### Phase 1 — Backend

**Goal:** Implement `equity_hedge_scenarios()` core function and the API endpoint; validate with curl.

| Deliverable | Description |
|---|---|
| `src/rita/core/portfolio_engine.py` | Add `equity_hedge_scenarios()` function |
| `src/rita/api/v1/portfolio.py` | Add `POST /api/v1/portfolio/equity-hedge-scenarios` endpoint with Pydantic request model |

**Acceptance Criteria:**
- [ ] `curl -X POST .../equity-hedge-scenarios -d '{"instrument":"ASML","n_shares":10,"start_date":"2025-01-01","end_date":"2025-01-31"}'` returns HTTP 200
- [ ] Response includes `portfolio.daily` with ≥ 5 entries
- [ ] Response includes `hedge_scenarios.mild_bearish.premium_per_share > 0`
- [ ] Response includes `hedge_scenarios.payoff_curves` with `price_range`, `unhedged`, `covered_call`, `protective_put` arrays of equal length
- [ ] `vol_30d_pct` is present and > 0

---

### Phase 2 — Frontend

**Goal:** Add the "Equity Hedge" page to `fno.html` and wire the JS module.

| Deliverable | Description |
|---|---|
| `dashboard/fno.html` | New nav item + `page-equity-hedge` section using existing CSS classes |
| `dashboard/js/fno/equity_hedge.js` | New module: form, API call, KPIs, portfolio chart, hedge cards, payoff chart |
| `dashboard/js/fno/nav.js` | Import `loadEquityHedge`; trigger on `equity-hedge` nav click |
| `dashboard/js/fno/state.js` | Add `equityHedgeData: null` field |

**Acceptance Criteria:**
- [ ] "Equity Hedge" nav item appears in sidebar below Risk-Reward, using `p04` purple colour
- [ ] Clicking nav item shows the section; other sections hide correctly
- [ ] Defaults pre-filled: instrument=ASML, shares=10, start=2025-01-01, end=2025-01-31
- [ ] "Build & Analyse" button triggers POST and renders all 4 panels
- [ ] KPI row shows: Start Price, End Price, Return %, Volatility % — all populated
- [ ] Portfolio value line chart renders with correct EUR values on Y axis
- [ ] Covered Call card shows strike, premium received, max value, breakeven (all non-zero)
- [ ] Protective Put card shows strike, premium paid, floor value, breakeven (all non-zero)
- [ ] Payoff chart renders 3 lines; covered call line is flat/capped above strike; protective put line is flat/floored below strike
- [ ] No `₹` symbols appear — all monetary values use `€`
- [ ] No regressions on existing FnO pages (dashboard, positions, etc.)

---

## Dependencies

| Phase | Depends on |
|---|---|
| Phase 2 | Phase 1 complete and endpoint returning valid JSON |

---

## Definition of Done

- [ ] All phases complete with acceptance criteria checked
- [ ] No regressions in existing FnO pages (nav, positions, hedge radar, history)
- [ ] `vol_30d_pct` present in API response (enabling future Feature 25b vol slider)
- [ ] Session committed to git
