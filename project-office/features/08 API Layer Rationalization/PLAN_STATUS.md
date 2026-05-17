# Feature 08 — API Layer Rationalization — Plan Status

**Status:** Requirements Complete / Not Started  
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

### Run A — Compliance Fix (P1 issues)
- [ ] R1: Create 3 experience endpoints (`backtest-daily`, `risk-timeline`, `training-history`)
- [ ] R2: Update 8 JS files + mobile app to use new experience endpoints
- [ ] R3: Resolve 4 missing/mismatch routes (`man-action`, `/metrics`, `/users` x2)

### Run B — Monitoring + Optimization (P2+P3)
- [ ] R4: Session cache utility + apply to top 5 redundant endpoints
- [ ] R5.1: `api_call_log` DB table + Alembic migration + middleware (DB-persisted, not in-memory)
- [ ] R5.2: `GET /api/v1/experience/ops/api-metrics` endpoint reads from DB
- [ ] R5.3: Ops dashboard "API Metrics" panel
- [ ] R5.4: `aggregate_metrics.py` updated to include `api_metrics` block → automatic Agent Builds feed at end of every `/enhance` run via existing Step 7
- [ ] R6: Update CLAUDE.md with routing enforcement rules

---

## Decisions Logged (2026-05-17)

- **R3.1:** Renamed `man-action` → `adjust-position-action`. Option A confirmed: build the route. Uses existing `manoeuvres` table + `ManoeuvreService` — no new migration. Long-term intent: ML analysis of trader behaviour.
- **R3.2:** `/metrics` is dead code in `audit.js` — variable fetched but never used. Remove the fetch call; no backend work needed.

## Blockers

None — ready to run `/enhance`.

---

## Notes

- Full requirements: `REQUIREMENTS.md`
- Overall compliance before this feature: 82%
- Target compliance after Run A: 100%
- Estimated effort: ~9 hrs total; split across 2 /enhance runs
