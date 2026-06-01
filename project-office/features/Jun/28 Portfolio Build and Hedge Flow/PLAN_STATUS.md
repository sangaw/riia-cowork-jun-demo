# Feature 28 — Portfolio Build & Hedge Flow: Plan Status

**Last updated:** 2026-06-01
**Overall status:** `[~] In progress — Phase 3 parked pending hedge design decision`
**Requirements:** `project-office/features/Jun/28 Portfolio Build and Hedge Flow/REQUIREMENTS.md`
**Design source:** Claude Design bundle `portfolio-build-and-hedge` → `Portfolio Final Flow.html`

---

## Phase Summary

| Phase | Title | Status | Blocker |
|---|---|---|---|
| Phase 0 | Design review & backend gap sign-off | `[x] Done` | — |
| Phase 1 | Page 1 — Portfolio Builder (frontend, reused data) | `[x] Done` | — |
| Phase 2 | Backend data extension | `[x] Done` | — |
| Phase 3 | Page 2 — Hedging (table + coverage dial + payoff) | `[~] Parked` | Hedge design decision pending |

---

## Phase 0 — Design review & backend gap sign-off

**Status:** `[x] Done`
**Agent:** Architect + PM
**Effort estimate:** 2 hours

### Tasks

| # | Task | Status | Notes |
|---|---|---|---|
| 0.1 | Confirm exists-vs-new table in REQUIREMENTS.md | `[x]` | Reviewed against geography-overview / portfolio-hedge / user-portfolio |
| 0.2 | Decide v1 disposition per 🔴 backend row (real / derived / deferred) | `[x]` | 1Y return → real; risk score → vol-bucketed; sector → static map; coverage/payoff → Phase 3 parked |
| 0.3 | Confirm whether instruments table already has `sector` / `country_code` | `[x]` | country_code confirmed; sector delivered as static fallback map in JS |
| 0.4 | Draft endpoint contracts in `eng-context.md` | `[x]` | extended geography-overview contracts drafted |

### Acceptance Gate
Each 🔴 backend item has an agreed v1 disposition and a drafted contract before frontend wires real data.

---

## Phase 1 — Page 1 — Portfolio Builder

**Status:** `[x] Done` — shipped in RITA dashboard (after My Portfolio in nav; moved from FnO during post-merge review)
**Commit:** `2c03966` (initial) · `3a99af2` (Phase 2 data wired) · `7e90c34` (UX polish)

### Tasks

| # | Task | Status | Notes |
|---|---|---|---|
| 1.1 | Portfolio Builder section + nav item in `rita.html` | `[x]` | Placed after My Portfolio in RITA sidebar |
| 1.2 | Region buckets + select-all + sticky basket + allocation inputs | `[x]` | 5 top-5 auto at 20%; new instruments default 15%; Allocate gated at 100% |
| 1.3 | Return-vs-risk scatter map | `[x]` | Chart.js scatter; click point to add/remove |
| 1.4 | Sortable instrument table | `[x]` | Sort by ticker / region / return / risk; Add button syncs basket |
| 1.5 | Guided basket (Short Term auto-selected; ranked draft; toggle on/off) | `[x]` | Short Term preset loads by default on section open |
| 1.6 | Register loader in `rita/nav.js` / `rita/main.js` | `[x]` | `portfolio-builder` section key wired |

---

## Phase 2 — Backend data extension

**Status:** `[x] Done` — commit `3a99af2` + `7e90c34`

### Tasks

| # | Task | Status | Notes |
|---|---|---|---|
| 2.1 | Add 1Y return %, 5Y/15Y CAGR, risk score (1–5), sector, horizons[] to geography-overview | `[x]` | `investment_horizons.py` config module; risk score = annualised-vol bucketed |
| 2.2 | `portfolio-hedge?coverage=` → per-row strike + %protected | `[~]` | Parked with Phase 3 |
| 2.3 | Pydantic schemas updated (`GeoInstrument` + new fields) | `[x]` | `geography.py` |
| 2.4 | Spec updates | `[x]` | This session |

---

## Phase 3 — Page 2 — Hedging

**Status:** `[~] Parked` — hedge design decision pending (user to revisit)
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
| 2026-05-31 | Initial | Fetched & read Claude Design bundle; reviewed existing FnO/RITA code; wrote REQUIREMENTS.md and PLAN_STATUS.md |
| 2026-05-31 | Phase 1+2 | Portfolio Builder shipped in RITA (region buckets, scatter map, sortable table, guided basket). Backend: 1Y return, risk score, sector. Commit `3a99af2`. |
| 2026-06-01 | Phase 1 polish | Short Term auto-selected on load; Total alloc moved to Selected widget; 4-row scroll cap; new instruments default 15%; Continue button removed; Allocate gated at 100%; investment_horizons.py config + 5Y/15Y CAGR + horizons[] field. Commit `7e90c34`. Spec updates this session. Phase 3 parked. |

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
