# Feature 28 — Portfolio Build & Hedge Flow: Plan Status

**Last updated:** 2026-05-31
**Overall status:** `[ ] Not started`
**Requirements:** `project-office/features/Jun/28 Portfolio Build and Hedge Flow/REQUIREMENTS.md`
**Design source:** Claude Design bundle `portfolio-build-and-hedge` → `Portfolio Final Flow.html`

---

## Phase Summary

| Phase | Title | Status | Blocker |
|---|---|---|---|
| Phase 0 | Design review & backend gap sign-off | `[ ] Not started` | — |
| Phase 1 | Page 1 — Portfolio Builder (frontend, reused data) | `[ ] Not started` | Phase 0 |
| Phase 2 | Backend data extension | `[ ] Not started` | Phase 0 |
| Phase 3 | Page 2 — Hedging (table + coverage dial + payoff) | `[ ] Not started` | Phase 2 |

---

## Phase 0 — Design review & backend gap sign-off

**Status:** `[ ] Not started`
**Agent:** Architect + PM
**Effort estimate:** 2 hours

### Tasks

| # | Task | Status | Notes |
|---|---|---|---|
| 0.1 | Confirm exists-vs-new table in REQUIREMENTS.md | `[ ]` | Reviewed against geography-overview / portfolio-hedge / user-portfolio |
| 0.2 | Decide v1 disposition per 🔴 backend row (real / derived / deferred) | `[ ]` | 1Y return, risk score, sector, strike, %protected, coverage agg, payoff |
| 0.3 | Confirm whether instruments table already has `sector` / `country_code` | `[ ]` | country_code confirmed (geography uses it); sector TBD |
| 0.4 | Draft endpoint contracts in `eng-context.md` | `[ ]` | extended builder-universe + `portfolio-hedge?coverage=` |

### Acceptance Gate
Each 🔴 backend item has an agreed v1 disposition and a drafted contract before frontend wires real data.

---

## Phase 1 — Page 1 — Portfolio Builder

**Status:** `[ ] Not started` — blocked on Phase 0
**Agent:** Engineer (frontend)
**Effort estimate:** 6 hours

### Tasks

| # | Task | Status | Notes |
|---|---|---|---|
| 1.1 | `page-portfolio-builder` section + nav item in `fno.html` | `[ ]` | Adapt to live FnO style |
| 1.2 | Region buckets + select-all + sticky final basket | `[ ]` | Data from `geography-overview` |
| 1.3 | Return-vs-risk map (click/drag cluster select) | `[ ]` | Derived return/risk until Phase 2 |
| 1.4 | Sortable instrument table (sort, bulk-add) | `[ ]` | Sync with basket |
| 1.5 | Guided basket (presets → ranked draft → Build) | `[ ]` | Build → existing save/continue |
| 1.6 | Register loader in `nav.js` / `main.js` | `[ ]` | |

### Acceptance Gate
Builder page renders end-to-end against existing data, basket stays in sync, styling matches live FnO.

---

## Phase 2 — Backend data extension

**Status:** `[ ] Not started` — blocked on Phase 0
**Agent:** Engineer (backend) + Architect
**Effort estimate:** 6 hours

### Tasks

| # | Task | Status | Notes |
|---|---|---|---|
| 2.1 | Add 1Y return %, risk score (1–5), sector to builder-universe response | `[ ]` | Extend geography-overview or new endpoint; ADR-001 Experience tier |
| 2.2 | `portfolio-hedge?coverage=` → per-row strike + %protected | `[ ]` | + aggregate max-drawdown-protected & monthly cost |
| 2.3 | Pydantic schemas + tier/dir per ADR-001 | `[ ]` | No system-tier calls from JS |
| 2.4 | Update Spec_RITA_App.md + Spec_Python_Code.md | `[ ]` | Same commit as code |

### Acceptance Gate
New fields returned and consumed by Page 1/2; specs updated.

---

## Phase 3 — Page 2 — Hedging

**Status:** `[ ] Not started` — blocked on Phase 2
**Agent:** Engineer (frontend)
**Effort estimate:** 6 hours

### Tasks

| # | Task | Status | Notes |
|---|---|---|---|
| 3.1 | Evolve `portfolio-hedge.js` card list → sortable table | `[ ]` | Extra columns: strike, %protected, return |
| 3.2 | Coverage dial band (slider + readouts + CTA) | `[ ]` | Drives table + aggregates via `?coverage=` |
| 3.3 | Payoff simulator (SVG curve + scenario P&L table) | `[ ]` | Derived from coverage + weights for v1 |
| 3.4 | Restructure Hedging section in `fno.html` (stacked) | `[ ]` | Table top → coverage band → payoff |

### Acceptance Gate
Coverage dial updates the table and readouts; payoff simulator renders; no-F&O proxy rows flagged.

---

## Session Log

| Date | Session | Work Done |
|---|---|---|
| 2026-05-31 | Initial | Fetched & read Claude Design bundle (`Portfolio Final Flow.html` + chat1.md); reviewed existing FnO/RITA portfolio + hedge code and backend endpoints; wrote REQUIREMENTS.md (with exists-vs-new gap review) and PLAN_STATUS.md |

---

## Open Questions

| # | Question | Owner | Status |
|---|---|---|---|
| Q1 | Does the instruments table already store `sector`? | Engineer | Open |
| Q2 | v1 risk score — derived from price volatility, or a fixed mapping? | Architect | Resolved: annualized-vol bucketed (absolute thresholds) — see eng-context C1 |
| Q3 | Payoff curve — client-side derived from coverage/weights, or backend? | Architect | Resolved: **backend** (real calc) — see eng-context C3 |
| Q4 | Coverage levels — continuous slider or discrete steps? | PM / user | Resolved: **continuous slider with increments shown** |
| Q5 | Keep both RITA + FnO builders, or consolidate later? | PM / user | Resolved: **keep both for now**, consolidate later |
| D1 | Premium model — (a) heuristic vs (b) Black-Scholes on realized vol | Architect / user | Resolved: **(b) Black-Scholes on realized vol** |
| D2 | Payoff beta — per-holding β vs β=1 for v1 | Architect / user | Resolved: **β = 1 for v1** |
</content>
