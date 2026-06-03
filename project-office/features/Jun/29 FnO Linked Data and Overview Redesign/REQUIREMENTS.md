# Feature 29 — FnO Linked Data & Overview Redesign

**Created:** 2026-06-03
**Owner:** Engineer (full-stack) · PM (UX decisions)
**Status:** `[ ] Not started`
**Guardrail refs:** org · engineer-role · rita-project
**Affected specs:** Spec_HTML_Code.md · Spec_JS_Code.md · Spec_RITA_App.md · Spec_Python_Code.md · Spec_DB.md
**Affected skills:** add-fno-feature · add-db-model · add-endpoint

---

## Context & Motivation

RITA is a **research platform** — not a trading system. All computed values (strike prices, premiums, P&L projections) are **indicative and illustrative** for visualisation and concept demonstration. No real transactions are placed.

After Feature 28, the Portfolio Hedge page works in isolation — a user's coverage choices, instrument selections, and strategy tab are lost on every page reload. The Overview page still shows a thin two-column portfolio table (name + alloc%) with no connection to the hedge the user configured. Pages share no state.

This feature wires the FnO module together through a **saved hedge plan** and redesigns the **Overview page** to show portfolio composition and current hedge posture at a glance.

---

## Design Decisions (locked before build)

| # | Decision | Resolution |
|---|---|---|
| D1 | Duration granularity | **1 year only.** 1m and 3m options are removed. The research platform showcases the concept; intra-year tenors add complexity without insight gain. |
| D2 | Hedge plan is intent-only | The plan records the user's selections for visualisation. No order placement, no broker connection. |
| D3 | All values indicative | Black-Scholes premiums, VaR, and P&L projections are labelled illustrative throughout the UI. |
| D4 | Hedge plan scope | One active plan per user (upsert by `key_id`). No history or versioning in v1. |
| D5 | Overview replaces positions table | The FnO Overview is repurposed as a portfolio + hedge summary. The active positions / options table is not the focus of this module. It may be moved to a dedicated "Positions" page later. |

---

## Objective

Connect all FnO pages through a shared data layer and redesign the Overview to reflect that story:

1. **Duration cleanup** — remove 1m/3m from the UI; lock all hedge calculations to 1 year.
2. **`user_hedge_plans` table** — persist coverage level, hedged instruments, and scenario strategy per user.
3. **Portfolio Hedge wires to saved plan** — loads selections on open; saves on change (debounced).
4. **Overview redesign** — portfolio-at-a-glance + hedge-status-at-a-glance as the landing experience.

---

## Linking Story (post-feature)

```
Portfolio Builder (rita.html)
  └── saves user_portfolios (holdings + total_value_eur)
           │
           ▼
FnO Overview ──────────── reads user_portfolios + user_hedge_plans
                           shows: holdings table, allocation chart, hedge status card

FnO Portfolio Hedge ─────  reads user_portfolios (source)
                            reads user_hedge_plans (pre-selects coverage + instruments)
                            writes user_hedge_plans (on any user change, debounced)

FnO Risk & Greeks (future)  reads user_hedge_plans → hedged vs unhedged Greeks
FnO Scenarios (future)      reads user_hedge_plans → pre-fills strategy + coverage
```

---

## Data Model — New Table

### `user_hedge_plans`

| Column | Type | Notes |
|---|---|---|
| `plan_id` | String (UUID) | Primary key |
| `key_id` | String (FK → user_portfolio_keys.key_id) | One active plan per user |
| `coverage` | Integer (0–100) | Coverage slider position |
| `duration` | String | Always `'1y'` in v1 (locked) |
| `hedged_ids` | JSON (`list[str]`) | Instrument IDs the user checked for hedging |
| `scenario_tab` | String | `'pp'` \| `'ps'` \| `'collar'` |
| `updated_at` | DateTime | Auto-updated on upsert |

No separate `created_at` needed — `updated_at` is sufficient for a single-row-per-user plan.

---

## API Contracts

### `GET /api/v1/experience/fno/hedge-plan`  (JWT required)
Returns the current saved plan, or 404 if none exists.

**Response:**
```json
{
  "plan_id": "uuid",
  "coverage": 65,
  "duration": "1y",
  "hedged_ids": ["RELIANCE", "BANKNIFTY", "NVIDIA"],
  "scenario_tab": "pp",
  "updated_at": "2026-06-03T14:22:00"
}
```

### `PUT /api/v1/experience/fno/hedge-plan`  (JWT required)
Upserts the plan. Creates on first save; overwrites on subsequent.

**Request body:**
```json
{
  "coverage": 65,
  "hedged_ids": ["RELIANCE", "BANKNIFTY", "NVIDIA"],
  "scenario_tab": "pp"
}
```

`duration` is always written as `"1y"` by the backend — not a client field.

**Response:** same shape as GET.

---

## Overview Page — Target Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  KPI strip (5 cards)                                            │
│  [Portfolio Value €] [# Instruments] [Wtd 1Y Return]           │
│  [Avg Risk Score]    [Hedge Coverage %]                         │
├────────────────────────────┬────────────────────────────────────┤
│  Allocation by Region      │  Hedge Status                      │
│  Stacked bar or donut      │  Max DD protected: −X%             │
│  India / US / EU / Other   │  vs −Y% unhedged                   │
│                            │  Monthly cost: Z%  (illustrative)  │
│                            │  N of M instruments hedged         │
│                            │  [Configure Hedge →]               │
│                            │  (or [Edit Hedge →] if plan saved) │
├────────────────────────────┴────────────────────────────────────┤
│  Holdings table                                                  │
│  Instrument | Alloc% | Position € | 1Y Ret | Risk | Hedged?    │
│  RELIANCE      25%     €12,500     +18.3%   ●●●○○   put spread │
│  BANKNIFTY     20%     €10,000      +6.1%   ●●●●○   proxy      │
│  NVIDIA        15%      €7,500     +42.0%   ●●●●●   —          │
└─────────────────────────────────────────────────────────────────┘
```

**Hedged?** column reads from the saved hedge plan's `hedged_ids`.  
**Hedge Status card** shows "No hedge configured" with CTA if no plan exists.  
All values carry an "Indicative" label in the subheading.

---

## Scope

### In Scope
- Duration locked to 1y — UI cleanup + backend default enforcement.
- `user_hedge_plans` ORM model + Alembic migration + repo + two endpoints (GET/PUT).
- Portfolio Hedge: load saved plan on init; debounced save on coverage/checkbox/tab change.
- FnO Overview redesign: 5-KPI strip, allocation chart, hedge status card, enriched holdings table.
- All computed values labelled indicative/illustrative in UI copy.
- Spec updates (Spec_DB, Spec_Python, Spec_HTML, Spec_JS, Spec_RITA_App).

### Out of Scope
- Multi-plan history or versioning.
- Risk & Greeks or Scenarios pages reading the hedge plan (flagged for a later feature).
- Any broker integration or order placement.
- Changing the Portfolio Builder in rita.html.

---

## Phases

### Phase 0 — Duration cleanup
**Goal:** Remove 1m/3m from the entire FnO surface. Lock to 1y everywhere.

| Deliverable | Detail |
|---|---|
| `portfolio-hedge.js` | Remove `_state.duration` controls; hardcode `duration='1y'` in `_fetchHedge()` |
| `fno.html` | Remove any remaining duration pill/button elements |
| `portfolio_hedge.py` | Change `duration` query param default to `'1y'`; keep it for backward compat but only `1y` is surfaced |

**Acceptance Criteria:**
- [ ] No duration picker visible in the Portfolio Hedge page.
- [ ] All API calls go to `?duration=1y`.
- [ ] `phSetDuration` export can be removed or left as dead code (no callers).

---

### Phase 1 — `user_hedge_plans` backend
**Goal:** Persist the user's hedge plan server-side.

| Deliverable | Detail |
|---|---|
| `src/rita/models/user_hedge_plan.py` | ORM model (plan_id, key_id, coverage, duration, hedged_ids JSON, scenario_tab, updated_at) |
| `src/rita/repositories/user_hedge_plan.py` | `UserHedgePlanRepo` — `find_by_key_id()`, `upsert()` |
| `src/rita/schemas/user_hedge_plan.py` | `HedgePlanOut`, `HedgePlanSave` Pydantic schemas |
| `src/rita/api/experience/hedge_plan.py` | `GET` + `PUT /api/v1/experience/fno/hedge-plan` (JWT, read-only GET, write on PUT) |
| Alembic migration | `YYYYMMDD_add_user_hedge_plans` |
| `src/rita/main.py` | Register `hedge_plan.router` |

**Acceptance Criteria:**
- [ ] `PUT` creates a plan if none exists; overwrites if one exists for that `key_id`.
- [ ] `GET` returns 404 if no plan saved.
- [ ] `duration` is always written as `"1y"` regardless of what client sends.
- [ ] Follows ADR-001 (Experience tier, read-only GET, one db.commit() in PUT).
- [ ] Migration runs cleanly on a fresh DB.

---

### Phase 2 — Portfolio Hedge wires to saved plan
**Goal:** Hedge selections survive page reloads.

| Deliverable | Detail |
|---|---|
| `portfolio-hedge.js` | On `loadPortfolioHedge()`: call `GET hedge-plan` → seed `_state.hedgeChecked`, `_state.coverage`, `_scenarioTab` |
| `portfolio-hedge.js` | `_savePlan()` — debounced 500ms `PUT hedge-plan`; called from `phToggleHedge()`, `phSetCoverage()`, `phSetScenarioTab()` |
| `fno.html` | Optional: small "Saved ✓" status indicator near the holdings table header |

**Acceptance Criteria:**
- [ ] Reload Portfolio Hedge → correct instruments pre-checked, slider at saved position, correct scenario tab active.
- [ ] Moving slider triggers a debounced save (no save spam).
- [ ] If `GET hedge-plan` returns 404, page loads with default state (all instruments checked, coverage 50, tab 'pp') — same as today.
- [ ] Save does not block the UI (fire-and-forget with silent error on fail).

---

### Phase 3 — Overview redesign
**Goal:** Overview becomes the portfolio + hedge summary landing page.

| Deliverable | Detail |
|---|---|
| `fno.html` — Overview section | Replace bottom "My Portfolio" table; add KPI strip, allocation chart, hedge status card, enriched holdings table |
| `dashboard/js/fno/my-portfolio.js` | Extend to fetch + render: geography-overview (for 1Y return, risk score), hedge-plan (for hedged_ids), portfolio (for position € per holding) |
| Allocation chart | Chart.js doughnut or stacked bar — grouped by region (India / US / EU / Other) weighted by alloc% |
| Hedge status card | Reads saved hedge plan; shows coverage %, Max DD protected, monthly cost (illustrative), N/M hedged count, CTA button |
| Holdings table | 6 columns: Instrument · Alloc% · Position € · 1Y Return · Risk (dots) · Hedged? (strategy label or —) |

**Acceptance Criteria:**
- [ ] KPI strip shows all 5 values; Portfolio Value shows '—' with hint if `total_value_eur` not set.
- [ ] Allocation chart renders from `portfolio.holdings` grouped by region (from geography-overview).
- [ ] Hedge status card shows "No hedge configured" + "Configure Hedge →" if no saved plan.
- [ ] Holdings table "Hedged?" column shows strategy label (e.g. "put spread") for instruments in `hedged_ids`, "—" for the rest.
- [ ] "Configure Hedge →" / "Edit Hedge →" button navigates to the Portfolio Hedge page.
- [ ] All computed values carry an "(indicative)" label in card subtitles.

---

### Phase 4 — Spec updates
**Goal:** Keep specs in sync.

| Deliverable |
|---|
| `Spec_DB.md` — `user_hedge_plans` table documented |
| `Spec_Python_Code.md` — hedge_plan.py endpoint added to Experience Layer table |
| `Spec_RITA_App.md` — GET/PUT hedge-plan added to API inventory |
| `Spec_HTML_Code.md` — Overview redesign and Portfolio Hedge save behaviour documented |
| `Spec_JS_Code.md` — `_savePlan()` and plan-load flow in portfolio-hedge.js documented |

---

## Dependencies

| Phase | Depends on |
|---|---|
| Phase 0 | Independent — can go first |
| Phase 1 | Phase 0 complete |
| Phase 2 | Phase 1 endpoints live |
| Phase 3 | Phase 1 (hedge-plan GET needed for hedge status card) |
| Phase 4 | Phases 1–3 complete |

---

## Definition of Done

- [ ] All phases complete with acceptance criteria checked.
- [ ] Duration picker gone; all API calls use `duration=1y`.
- [ ] Hedge plan persists across reloads — instruments, coverage, tab.
- [ ] FnO Overview shows portfolio value, allocation chart, hedge status, enriched holdings table.
- [ ] All UI copy labels illustrative/indicative values appropriately.
- [ ] Specs updated (Spec_DB, Spec_Python, Spec_RITA_App, Spec_HTML, Spec_JS).
- [ ] Session committed to git.
