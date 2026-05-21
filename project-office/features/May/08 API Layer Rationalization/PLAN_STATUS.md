# Feature 08 — API Layer Rationalization — Plan Status

**Status:** COMPLETE  
**Last updated:** 2026-05-17

---

## Current State

Requirements draft complete. Audit identified 14 issues across RITA, FnO, Ops, and Mobile surfaces.

| Category | Count | Priority |
|---|---|---|
| Tier violations (dashboard → system direct) | 8 | P1 |
| Missing routes | 2 | P1 |
| Path mismatches | 2 | P2 |
| Redundant API calls (no cache) | 6 data sources | P2 |
| API monitoring gap | 1 (no metrics endpoint) | P3 |

---

## Task Breakdown

### Run A — Compliance Fix (P1 issues) — merged at 479fa9f (2026-05-17)
- [x] R1: Create 3 experience endpoints (`backtest-daily`, `risk-timeline`, `training-history`)
- [x] R2: Update 8 JS files + mobile app to use new experience endpoints
- [x] R3: Resolve 4 missing/mismatch routes (`man-action` → `adjust-position-action`, dead `/metrics` fetch removed, `/users` path fixed)

### Run B — Monitoring + Optimization (P2+P3) — merged at a2d57a6 (2026-05-17)
- [x] R4: Session cache utility (`dashboard/js/shared/api-cache.js`) + applied to top 5 redundant endpoints
- [x] R5.1: `api_call_log` DB table + Alembic migration + middleware (DB-persisted)
- [x] R5.2: `GET /api/experience/ops/api-metrics` endpoint reads from DB
- [x] R5.3: Ops dashboard "API Metrics" panel (table: path, method, calls, p50, p95, errors)
- [x] R5.4: `aggregate_metrics.py` updated to include `api_metrics` block
- [x] R6: CLAUDE.md updated with API tier routing enforcement rules

---

## Decisions Logged (2026-05-17)

- **R3.1:** Renamed `man-action` → `adjust-position-action`. Option A confirmed: build the route. Uses existing `manoeuvres` table + `ManoeuvreService` — no new migration. Long-term intent: ML analysis of trader behaviour.
- **R3.2:** `/metrics` is dead code in `audit.js` — variable fetched but never used. Remove the fetch call; no backend work needed.

## Post-merge hotfixes (2026-05-17)

- `fix(rita)`: api-cache.js import path corrected in 8 rita JS files (../../ → ../) — SyntaxError killing RITA module tree. Commit: 2c94033
- `fix(ops)`: `setEl` added to ops/utils.js — missing named export causing SyntaxError in Ops module tree. Commit: 5810cd8
- `fix(rita)`: conflict marker removed from scenarios.js — survived Run B merge resolution. Commit: 30a5c47
- FC-IMP + FC-MERGE gates added to all 3 skill DoDs to prevent recurrence. Commits: 68ae873, 9f306e4

## Blockers

None — complete.

---

## Notes

- Full requirements: `REQUIREMENTS.md`
- Overall compliance before this feature: 82%
- Target compliance after Run A: 100%
- Estimated effort: ~9 hrs total; split across 2 /enhance runs
