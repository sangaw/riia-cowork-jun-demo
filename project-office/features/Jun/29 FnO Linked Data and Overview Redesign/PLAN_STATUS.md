# Feature 29 — FnO Linked Data & Overview Redesign: Plan Status

**Last updated:** 2026-06-10
**Overall status:** `[x] Complete — all phases merged; specs updated (e983a0d)`
**Requirements:** `project-office/features/Jun/29 FnO Linked Data and Overview Redesign/REQUIREMENTS.md`

---

## Phase Summary

| Phase | Title | Status | Commits |
|---|---|---|---|
| Phase 0 | Duration cleanup — lock to 1y | `[x] Merged` | b822859 (merge b8a712e) |
| Phase 1 | `user_hedge_plans` backend | `[x] Merged` | e839dda (merge), f731e1f (QA — 9 tests) |
| Phase 2 | Portfolio Hedge wires to saved plan | `[x] Merged` | d96dd4c (merge), ce23a9f (code-review fix) |
| Phase 3 | Overview redesign | `[x] Merged` | 64099e3 (merge), 8e0c7ee (path fix) |
| Phase 4 | Spec updates | `[x] Complete` | e983a0d (2026-06-07) |

---

## Phase 0 — Duration cleanup

**Status:** `[x] Merged — commit b822859 (2026-06-03)`
**Effort estimate:** 30 min
**Files:** `portfolio-hedge.js`, `portfolio_hedge.py`, `fno.html`

### Tasks

| # | Task | Status | Notes |
|---|---|---|---|
| 0.1 | Remove `_state.duration` + `phSetDuration` from `portfolio-hedge.js` | `[x]` | Hardcode `duration='1y'` in `_fetchHedge()` |
| 0.2 | Remove any duration pill/button HTML from `fno.html` | `[x]` | None visible post F28 redesign — confirm |
| 0.3 | `portfolio_hedge.py` — remove `1m`/`3m` from pattern, default `1y` | `[x]` | Keep param for compat; drop it from UI only |

### Acceptance Gate
No duration controls visible. All hedge API calls use `?duration=1y`. `phSetDuration` export removed.

---

## Phase 1 — `user_hedge_plans` backend

**Status:** `[x] Merged — e839dda; QA f731e1f (9 tests); alembic upgrade head applied`
**Effort estimate:** 2 hours
**Files:** models · repo · schemas · endpoint · migration · main.py

### Tasks

| # | Task | Status | Notes |
|---|---|---|---|
| 1.1 | ORM model `UserHedgePlanModel` | `[x]` | `plan_id`, `key_id` FK, `coverage` int, `duration` str, `hedged_ids` JSON, `scenario_tab` str, `updated_at` datetime |
| 1.2 | `UserHedgePlanRepo` — `find_by_key_id()` + `upsert()` | `[x]` | upsert = find + update or create |
| 1.3 | Pydantic schemas `HedgePlanOut`, `HedgePlanSave` | `[x]` | `HedgePlanSave` accepts coverage + hedged_ids + scenario_tab; no duration field from client |
| 1.4 | Experience-tier router `hedge_plan.py` — GET + PUT | `[x]` | GET → 404 if no plan; PUT → upsert, always writes duration='1y' |
| 1.5 | Alembic migration `YYYYMMDD_add_user_hedge_plans` | `[x]` | FK to `user_portfolio_keys.key_id`; unique constraint on `key_id` |
| 1.6 | Register router in `main.py` | `[x]` | Under experience routers block |
| 1.7 | Unit test `test_hedge_plan.py` | `[x]` | GET 404 when none; PUT creates; PUT again overwrites; duration always 1y |

### Acceptance Gate
`PUT` then `GET` round-trips cleanly. `duration` is always `"1y"` in response. Migration runs on fresh DB.

---

## Phase 2 — Portfolio Hedge wires to saved plan

**Status:** `[x] Merged — d96dd4c (2026-06-03); code-review fix ce23a9f`
**Effort estimate:** 1.5 hours
**Files:** `portfolio-hedge.js`

### Tasks

| # | Task | Status | Notes |
|---|---|---|---|
| 2.1 | On `loadPortfolioHedge()` — call `GET hedge-plan` after portfolio load | `[x]` | If 200: seed `hedgeChecked`, `coverage`, `_scenarioTab`; if 404: use defaults (all checked, 50, 'pp') |
| 2.2 | `_savePlan()` — fire-and-forget `PUT hedge-plan` | `[x]` | Sends `{coverage, hedged_ids: [..._state.hedgeChecked], scenario_tab: _scenarioTab}` |
| 2.3 | Debounce `_savePlan` 500ms | `[x]` | Attach to `phToggleHedge()`, `phSetCoverage()`, `phSetScenarioTab()` |
| 2.4 | Optional: "Saved" flash indicator | `[x]` | Small text near card header — `opacity` fade after 1.5s |

### Acceptance Gate
Reload → previous state restored. Slider/checkbox triggers silent debounced save. 404 on first load → clean default state.

---

## Phase 3 — Overview redesign

**Status:** `[x] Merged — 64099e3 (2026-06-03); /v1/ path fix 8e0c7ee; 10 QA tests`
**Effort estimate:** 3 hours
**Files:** `fno.html`, `dashboard/js/fno/my-portfolio.js`

### Tasks

| # | Task | Status | Notes |
|---|---|---|---|
| 3.1 | 5-KPI strip HTML | `[x]` | Portfolio Value · # Instruments · Wtd 1Y Return · Avg Risk · Hedge Coverage |
| 3.2 | Allocation chart — Chart.js doughnut by region | `[x]` | Reads portfolio.holdings × geography-overview region grouping |
| 3.3 | Hedge status card | `[x]` | Max DD protected, monthly cost, N/M hedged, CTA button; "No hedge configured" if plan=null |
| 3.4 | Enriched holdings table | `[x]` | Instrument · Alloc% · Position € · 1Y Return · Risk dots · Hedged? |
| 3.5 | "Hedged?" column — cross-reference `hedged_ids` from saved plan | `[x]` | Show strategy label from hedge-plan or "—" |
| 3.6 | CTA wiring — "Configure Hedge →" / "Edit Hedge →" → navigates to `portfolio-hedge` page | `[x]` | Use existing `_sectionLoaders` nav |
| 3.7 | `my-portfolio.js` — extend to fetch geography-overview + hedge-plan in parallel | `[x]` | `Promise.all([portfolio, geo, plan])` |
| 3.8 | KPI strip JS — compute Wtd 1Y Return + Avg Risk from geo data | `[x]` | Weighted by alloc_pct |
| 3.9 | Copy: label all computed values "(indicative)" in card subtitles | `[x]` | Hedge Status card subtitle + Holdings table header |

### Acceptance Gate
Overview loads without touching Portfolio Hedge page. Hedge status shows saved plan values. Holdings table shows hedged/unhedged per row. All illustrative values labelled.

---

## Phase 4 — Spec updates

**Status:** `[x] Complete — e983a0d (2026-06-07)`
**Effort estimate:** 45 min

### Tasks

| # | Task | Status |
|---|---|---|
| 4.1 | `Spec_DB.md` — `user_hedge_plans` schema | `[x]` |
| 4.2 | `Spec_Python_Code.md` — `hedge_plan.py` in Experience Layer table | `[x]` |
| 4.3 | `Spec_RITA_App.md` — GET + PUT endpoints in API inventory | `[x]` |
| 4.4 | `Spec_HTML_Code.md` — Overview redesign + Portfolio Hedge save behaviour | `[x]` |
| 4.5 | `Spec_JS_Code.md` — `_savePlan()` and plan-load documented | `[x]` |

---

## Open Questions

| # | Question | Owner | Status |
|---|---|---|---|
| Q1 | Should the active positions table be moved to a dedicated "Positions" sub-page, or just pushed below the portfolio section? | PM / user | Open |
| Q2 | Allocation chart — doughnut (by region) or stacked bar (by instrument)? | PM / user | Open |
| Q3 | Should the Hedge Status card show indicative Max DD + cost even before a plan is saved (computed from a default 50% coverage)? | PM / user | Open |

---

## Session Log

| Date | Session | Work Done |
|---|---|---|
| 2026-06-03 | Feature creation | REQUIREMENTS.md + PLAN_STATUS.md written. Design review and architecture discussion with user. Duration locked to 1y. Research-platform constraints captured. |
| 2026-06-03 | Phase 0 | /enhance run-20260603-1611: duration cleanup merged to master (b822859). _DURATION_MONTHS + phSetDuration removed. t_months=12.0 hardcoded. Both specs updated. |
| 2026-06-03 | Phase 1 | /enhance run-20260603-1640: user_hedge_plans ORM + migration + repo + schemas + GET/PUT endpoints built and code-reviewed (PASS). Branch worktree-agent-a122342e7c180a479, commit f1fcefa. QA + merge deferred — resume next session. |
| 2026-06-03 | Phases 1–3 | Phase 1 QA + merge (e839dda, f731e1f). Phase 2 saved-plan wiring merged (d96dd4c, fix ce23a9f). Phase 3 Overview redesign merged (64099e3, path fix 8e0c7ee) — 10 QA tests, Design Review 1 retry, Code Review PASS. |
| 2026-06-07 | Phase 4 | Spec updates committed (e983a0d): Spec_DB (user_hedge_plans), Spec_Python_Code (hedge_plan.py), Spec_RITA_App, Spec_JS_Code, Spec_HTML_Code. |
| 2026-06-10 | Closure | Documentation sweep — PLAN_STATUS marked Complete; all phase statuses and task checkboxes finalised. |
