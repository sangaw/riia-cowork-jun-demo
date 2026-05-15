# Feature 0501 — Agent Builds Page: Defect Fix + Actual Token Tracking
**Last updated:** 2026-05-15
**Status:** COMPLETE — merged at a872db1

---

## Fixes Applied

| Fix | Root Cause | Commit |
|---|---|---|
| Ops nav completely broken | `utilities.js` imported `{ api }` which doesn't exist in `ops/api.js` — fatal ES module linking error | `8ca753d` |
| DB empty, no runs showing | `agent_build_runs` table had 0 rows — `seed_agent_builds.py` not re-run after 2 new run logs added | Re-ran seed |
| P1 — Metric Trend Lines: 3 of 4 lines always empty | `mountTrendChart` read `overall_status`, `human_score.csat` off `grounding_trend` items — fields not present; only Grounding Score rendered | `a872db1` |
| P1 — Skill Version History: improvement data not shown | `get_agent_builds` built `skill_version_history` from DB only, ignoring `metrics.json`; `recent_commits` type was `list[str]` but data is `list[dict]` | `a872db1` |
| P2 — Token Estimate result cards never populate | `submitTokenEstimate` wrote result to `#ab-estimate-result` only; three grid cards (`ab-res-complexity`, `ab-res-total`, `ab-res-confidence`) never written to | `a872db1` |
| P3 — recent_commits shown as [object Object] | `renderSkillVersions` called `esc(c)` on `{hash, message}` objects | `a872db1` |

---

## New Feature: Actual Token Tracking from Claude API

| Requirement | Delivered | Notes |
|---|---|---|
| R1 — Capture actual tokens per agent run | Partial — schema + API ready; capture requires orchestrator change | `actual_tokens: Optional[dict]` added to `AgentOut`; populated from run JSON |
| R2 — Store in run JSON + DB | Done | `actual_tokens_total` column added to `agent_build_agents` via Alembic migration `a3f9c1e82b5d`; DB migrated |
| R3 — Show actual vs estimated in UI | Done | Run history "Est / Actual" column; Token chart dual datasets; Forecast chart uses actual sum |
| R4 — Feed actual into forecast calibration | Done | `aggregate_metrics.py` prefers `actual_tokens.total_tokens` over `total_tokens_estimated` |
| R5 — Cache Hit Rate KPI | Done | `ab-kpi-cache-hit` card added to `ops.html`; `renderKpiCards` computes avg cache hit rate |

---

## Defects Discovered During This Run

| Defect | Root Cause | Resolution |
|---|---|---|
| Engineer skipped `ops.html` | "Never read HTML" misread as "never touch HTML" | Re-invoked Engineer; fixed in commit `c85abdd`. Feedback + guardrail added to all skill files |
| QA agent ran in background — no permissions | Orchestrator used `run_in_background: true` | Re-ran in foreground; 18/18 tests passed. Feedback recorded: never run agents in background during /enhance |
| Alembic migration committed but not applied | Engineer created migration file but did not run `alembic upgrade head` | Applied manually: `a3f9c1e82b5d`. Hard gate added to all skill files + enhance.md step 7c |
| May 15 run not showing in dashboard | `seed_agent_builds.py` not re-run after new run log added | Re-ran seed: 1 run inserted, 18 skipped |

---

## Files Changed (merge a872db1)

| File | Change |
|---|---|
| `src/rita/schemas/agent_builds.py` | Added `actual_tokens`, `human_score_csat`; `recent_commits` type corrected |
| `src/rita/models/agent_builds.py` | Added `actual_tokens_total` column |
| `alembic/versions/a3f9c1e82b5d_add_actual_tokens_total.py` | New migration (applied) |
| `src/rita/api/experience/ops.py` | Populated `skill_version_history` from `metrics.json`; added `human_score_csat` + `actual_tokens` per agent |
| `dashboard/js/ops/agent-builds.js` | All 4 defect fixes + Actual Token Tracking UI (7 function changes) |
| `dashboard/ops.html` | Added `ab-kpi-cache-hit` KPI card |
| `riia-ai-org/agent-ops/aggregate_metrics.py` | Prefers actual tokens in `by_feature_type` avg |
| `project-office/specs/Spec_RITA_App.md` | Updated agent-builds endpoint row |
| `project-office/specs/Spec_JS_Code.md` | Updated agent-builds.js module row |

---

## QA

- 18/18 unit tests pass (`tests/unit/test_agent_builds_defects.py`)
- API-frontend contract: MATCH — all 6 new/changed fields verified
- DB migration confirmed applied: `Running upgrade 47b9b71fa2f6 -> a3f9c1e82b5d`
