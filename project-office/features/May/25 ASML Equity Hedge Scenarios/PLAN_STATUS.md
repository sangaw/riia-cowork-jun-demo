# Feature 25 — ASML Equity Hedge Scenarios: Plan Status

**Last updated:** 2026-05-27
**Overall status:** `[x] Complete`
**Requirements:** `project-office/features/May/25 ASML Equity Hedge Scenarios/REQUIREMENTS.md`

---

## Phase Summary

| Phase | Title | Status | Blocker |
|---|---|---|---|
| Phase 1 | Backend — Core Engine + API Endpoint | `[x] Complete` | — |
| Phase 2 | Frontend — FnO Page + JS Module | `[x] Complete` | — |

---

## Phase 1 — Backend: Core Engine + API Endpoint

**Status:** `[x] Complete`
**Agent:** Engineer (general-purpose + worktree)
**Effort estimate:** 1–1.5 hours

### Tasks

| # | Task | Status | Notes |
|---|---|---|---|
| 1.1 | Add `equity_hedge_scenarios()` to `portfolio_engine.py` — OHLCV load, vol computation, Black-Scholes pricing, payoff grid | `[x]` | Use scipy.stats.norm (already in deps); r=0.03, T=30/252 |
| 1.2 | Add Pydantic `EquityHedgeScenariosRequest` model to `portfolio.py` | `[x]` | Fields: instrument, n_shares, start_date, end_date |
| 1.3 | Add `POST /api/v1/portfolio/equity-hedge-scenarios` endpoint | `[x]` | Calls `equity_hedge_scenarios()`, returns structured JSON |
| 1.4 | Validate with curl — check all response fields non-null and payoff arrays equal length | `[x]` | |

### Acceptance Gate

`POST /equity-hedge-scenarios` with ASML 10 shares Jan 2025 returns HTTP 200 with all fields in the contract (see REQUIREMENTS.md).

---

## Phase 2 — Frontend: FnO Page + JS Module

**Status:** `[x] Complete`
**Agent:** Engineer (general-purpose + worktree)
**Effort estimate:** 1.5–2 hours

### Tasks

| # | Task | Status | Notes |
|---|---|---|---|
| 2.1 | Add `equityHedgeData: null` to `state.js` | `[x]` | Prevents re-fetch on repeated nav clicks |
| 2.2 | Add nav item `data-page="equity-hedge"` with `p04` colour class in `fno.html` sidebar | `[x]` | Below Risk-Reward, above Hedge Radar |
| 2.3 | Add `<div class="section" id="page-equity-hedge">` to `fno.html` — all 4 panels using existing CSS | `[x]` | Panel 1: form card; Panel 2: KPI row c4; Panel 3: two-col; Panel 4: payoff chart |
| 2.4 | Create `dashboard/js/fno/equity_hedge.js` with `loadEquityHedge()` and `renderEquityHedge()` | `[x]` | EUR formatting: toLocaleString('de-DE'); date format YYYY-MM-DD |
| 2.5 | Wire into `nav.js`: import `loadEquityHedge`, add click handler for `equity-hedge` page | `[x]` | Pattern same as `history` page → `loadHedgeHistory()` |
| 2.6 | Smoke-test all existing pages — no regressions | `[x]` | |

### Acceptance Gate

All acceptance criteria in Phase 2 checked; no existing FnO pages broken.

---

## Session Log

| Date | Session | Work Done |
|---|---|---|
| 2026-05-27 | Initial | Requirements written; PLAN_STATUS created; ready for /enhance |
| 2026-05-27 | Continuation Run 1 | Phase 1 + Phase 2 delivered: portfolio_engine.py, portfolio.py, equity_hedge.js, fno.html, nav.js, state.js, pyproject.toml, spec files; fix commit 488a42b (i18n nav label, hedge return + net return KPIs) |
| 2026-05-27 | Continuation Run 2 | QA tests created and run; PLAN_STATUS updated to complete; fix commit 488a42b noted |

---

## Open Questions

| # | Question | Owner | Status |
|---|---|---|---|
| Q1 | Risk-free rate for EUR Black-Scholes: use 3% hardcoded (ECB rate approx). Confirm or override? | PM | Resolved — use 3% |
| Q2 | Covered call OTM target: 5% above spot. Adjust? | PM | Resolved — use 5% |
| Q3 | Payoff grid range: spot ±25%, 33 steps. Adjust? | PM | Resolved — use ±25% |
