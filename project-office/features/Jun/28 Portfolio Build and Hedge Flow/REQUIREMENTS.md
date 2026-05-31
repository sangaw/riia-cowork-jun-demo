# Feature 28 — Portfolio Build & Hedge Flow

**Created:** 2026-05-31
**Owner:** Engineer (frontend-led) · Architect (backend gap)
**Status:** `[ ] Not started`
**Guardrail refs:** org · engineer-role · rita-project
**Affected specs:** Spec_HTML_Code.md · Spec_JS_Code.md · Spec_RITA_App.md · Spec_Python_Code.md (Phase backend only)
**Affected skills:** add-fno-feature
**Design source:** Claude Design bundle `portfolio-build-and-hedge` — `Portfolio Final Flow.html` (two-page flow). Bundle extracted to `/tmp/design-extract/` during the design-review session; intent captured in `chats/chat1.md`.

---

## Objective

Redesign the FnO portfolio experience into a guided **two-page flow** that adapts the Claude Design "Portfolio Final Flow" wireframe to the live FnO dashboard style (editorial serif + `#BE185D` accent):

- **Page 1 — Portfolio Builder:** choose instruments faster than the current one-at-a-time stepper grid. Region buckets ranked by performance with group select-all and a sticky **final basket**; a **return-vs-risk map** and **sortable table** as two faster lenses on the same universe; and a **guided basket** (goal preset → ranked draft → tweak).
- **Page 2 — Hedging:** the saved basket as a full-width **sortable hedge table**, a single **coverage dial** that sets every strike/cost at once (with no-F&O names falling back to an index proxy), and a **payoff / scenario simulator** below.

After this feature, a retail self-directed user can assemble a 5–10 name basket by region/performance and see a tangible hedge payoff — without clicking each instrument individually.

---

## Background

The current FnO portfolio surface is two thin screens:

- `dashboard/js/fno/my-portfolio.js` — read-only KPI tiles + 2025 performance chart.
- `dashboard/js/rita/my-portfolio.js` — allocation builder (per-instrument `%` steppers, total-must-equal-100, Save Portfolio, perf chart).
- `dashboard/js/fno/portfolio-hedge.js` — Feature 27 hedge recommendation cards (one card per holding).

The design assistant reviewed our existing UI (screenshots in the bundle) and the user landed on the two combined pages above. The pain point being solved (per `chat1.md`): *"too many items to select, one at a time clicking."* This feature is the implementation handoff of that finalized design.

This is the natural follow-on to **Feature 26 (User Portfolio Store)** and **Feature 27 (Portfolio Hedge)** — it reuses their persistence and hedge-recommendation backends and layers the new selection/visualization/coverage UX on top.

---

## What Exists vs. What's New (gap review)

Legend: ✅ exists & reusable · 🟡 exists but needs extension · 🔴 new build

### Backend / data

| Capability design needs | Status | Detail |
|---|---|---|
| Saved portfolio (holdings, name, updated_at) | ✅ | `GET /api/v1/experience/user-portfolio` (JWT) → `instrument_id`, `allocation_pct`, `name`, `updated_at`. Reuse for the **final basket** and the hedge page's source holdings. |
| Save / build allocation | ✅ | Feature 26 store + `rita/my-portfolio.js` builder logic (total=100 validation, save). Reuse for "Continue → Allocate". |
| Portfolio performance series | ✅ | `GET /api/v1/experience/rita/portfolio-performance?holdings=&year=` → `dates[]`, `values[]` (base 100). Reuse for any basket sparkline / draft preview. |
| Instruments grouped by region | 🟡 | `GET /api/v1/experience/rita/geography-overview` already groups `is_available` instruments into India / US / Europe / Other from the instruments table — but returns **daily** return + signal, **no 1Y return, no risk score, no sector**. The region-bucket skeleton is here; the ranking/risk fields are not. |
| Per-instrument **1Y return %** | 🔴 | Needed to rank buckets and plot the map. Not currently exposed; price history exists in the cache but no 1Y-return aggregation endpoint. |
| Per-instrument **risk score (1–5)** | 🔴 | Needed for the map Y/X and table. No volatility/risk metric is computed today. |
| Per-instrument **sector** | 🔴 | Shown as a chip in buckets/table. Not in current responses (instruments table may have it — to confirm). |
| Hedge recommendations per holding | 🟡 | `GET /api/experience/fno/portfolio-hedge` (JWT, Feature 27) → `instrument_id`, `allocation_pct`, `risk_level` (derived from alloc%), `hedge_type` (`index_put`/`index_put_spread`/`equity_note`/`na`), `eligible` (F&O), `cost_estimate_pct`, `recommendation`. Reuse as the hedge-table base. |
| Hedge **strike** + **% protected** per holding | 🔴 | Table columns in the design; not returned today. |
| **Coverage level** (one dial → all strikes/costs) | 🔴 | No `coverage` parameter; current recs are fixed. Needs a `coverage_pct` query param and aggregate roll-ups (max-drawdown-protected, monthly cost). |
| **Payoff / scenario** data (hedged vs unhedged curve, scenario P&L) | 🔴 | Entirely new. Could be derived client-side from coverage + weights for a first cut. |

### Frontend

| Design block | Status | Detail |
|---|---|---|
| Region buckets w/ select-all + sticky final basket | 🔴 | New layout; reuses geography-overview data + builder save. |
| Return-vs-risk scatter map (lasso a cluster) | 🔴 | New component. Lasso can be a simplified click/drag-select. |
| Sortable instrument table (sort, bulk-add) | 🔴 | New; data partly from geography-overview once return/risk added. |
| Guided basket (goal presets → ranked draft → projected return) | 🔴 | New; goal presets + projected-return are new concepts. |
| Hedge table (sortable, F&O proxy highlight) | 🟡 | Evolves Feature 27 card list into a table with extra columns. |
| Coverage dial band (slider + readouts + CTA) | 🔴 | New control. |
| Payoff simulator (SVG curve + scenario table) | 🔴 | New component. |

---

## Scope

### In Scope
- Two new FnO pages adapted to live FnO styling: **Portfolio Builder** and **Hedging**, navigable from the FnO sidebar (`nav.js` + `fno.html` sections + `dashboard/js/fno/*` modules).
- Reuse of existing endpoints (`user-portfolio`, `geography-overview`, `portfolio-hedge`, `portfolio-performance`).
- Frontend components for: region buckets + final basket, return-risk map, sortable table, guided basket, hedge table, coverage dial, payoff simulator.
- A clearly-bounded backend extension to supply the **new data fields** the design requires (1Y return, risk score, sector; hedge strike + % protected; coverage-level aggregation). Where a real metric is non-trivial (risk score, payoff curve), a documented derived/approximation is acceptable for v1, flagged as illustrative.
- Spec updates (HTML, JS, RITA app endpoint inventory; Python spec if endpoints change).

### Out of Scope
- Live option-chain pricing / real broker order placement ("Place hedge orders" / "Build portfolio" CTAs are wired to existing save/continue, not to execution).
- The wireframe's greyscale look, handwritten annotations, device frame, and the Tweaks panel (we adapt to live FnO style instead).
- The dropped "Hedge checkout" screen (explicitly cut by the user in `chat1.md`).
- Replacing the existing `rita/my-portfolio.js` builder — the new flow lives in the FnO dashboard; the RITA builder is left intact unless a later phase consolidates them.

---

## Phases

### Phase 0 — Design review & backend gap sign-off
**Goal:** Lock the exists-vs-new table above with the Architect; decide which 🔴 backend items are v1 (real) vs v1 (illustrative/derived).

| Deliverable | Description |
|---|---|
| `eng-context.md` | API contracts for any new/extended endpoints, files-to-touch, edge cases |
| Decision log | Per 🔴 row: real now / derived now / deferred |

**Acceptance Criteria:**
- [ ] Each 🔴 backend item has an agreed v1 disposition.
- [ ] Endpoint contracts drafted for extended `geography-overview` (or a new builder-universe endpoint) and `portfolio-hedge?coverage=`.

---

### Phase 1 — Page 1: Portfolio Builder (frontend, reused data)
**Goal:** Ship the Builder page structure against existing data, with map/table/guided using derived fields where backend is pending.

| Deliverable | Description |
|---|---|
| `dashboard/js/fno/portfolio-builder.js` | Region buckets, final basket, map, table, guided basket |
| `dashboard/fno.html` | New `page-portfolio-builder` section + nav item |
| `dashboard/js/fno/nav.js`, `main.js` | Register section loader |

**Acceptance Criteria:**
- [ ] Three region buckets render from `geography-overview`, ranked, with select-all and a sticky final basket synced to selection.
- [ ] Map + sortable table render side-by-side and stay in sync with the basket.
- [ ] Guided basket shows goal presets → ranked draft → "Build portfolio →" (→ existing save/continue).
- [ ] Styling matches live FnO dashboard (serif headings, `#BE185D` accent), not greyscale.

---

### Phase 2 — Backend data extension
**Goal:** Supply the new fields (1Y return, risk score, sector) and coverage aggregation so Page 1/2 use real data.

| Deliverable | Description |
|---|---|
| Extended builder-universe response | 1Y return %, risk score (1–5), sector per instrument |
| `portfolio-hedge?coverage=` | Coverage param → per-row strike + % protected + aggregate max-drawdown-protected & monthly cost |
| Schemas + spec updates | Pydantic + Spec_RITA_App / Spec_Python_Code |

**Acceptance Criteria:**
- [ ] Endpoints return the new fields; Page 1/2 read them instead of derived stand-ins.
- [ ] Tier placement follows ADR-001 (Experience tier; no system-tier calls from JS).
- [ ] Specs updated in the same commit.

---

### Phase 3 — Page 2: Hedging (table + coverage dial + payoff)
**Goal:** Ship the Hedging page with the coverage dial driving the table and the payoff simulator.

| Deliverable | Description |
|---|---|
| `dashboard/js/fno/portfolio-hedge.js` (evolve) | Card list → sortable table + coverage band + payoff simulator |
| `dashboard/fno.html` | Hedging section restructured (table on top, coverage band below, payoff below) |

**Acceptance Criteria:**
- [ ] Full-width hedge table with sortable columns; no-F&O rows visibly flagged as index-proxy.
- [ ] Coverage dial updates strikes/costs and the aggregate readouts (max-drawdown-protected, monthly cost).
- [ ] Payoff simulator shows hedged-vs-unhedged curve + scenario P&L table.

---

## Dependencies

| Phase | Depends on |
|---|---|
| Phase 1 | Phase 0 sign-off |
| Phase 2 | Phase 0 contracts |
| Phase 3 | Phase 2 (coverage + strike data) |

---

## Definition of Done

- [ ] All phases complete with acceptance criteria checked.
- [ ] Both pages reachable from the FnO sidebar and styled to the live dashboard.
- [ ] `Spec_HTML_Code.md`, `Spec_JS_Code.md`, `Spec_RITA_App.md` (and `Spec_Python_Code.md` if endpoints changed) updated.
- [ ] `add-fno-feature` skill `Last validated against spec` date refreshed if its structure changed.
- [ ] Session committed to git.
</content>
</invoke>
