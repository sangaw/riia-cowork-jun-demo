# AI Commentary — Feature Plan Status
**Last updated:** 2026-05-15
**Overall status:** Complete — merged to master 2026-05-15

---

## What This Feature Does

Adds auto-generated narrative commentary to two RITA pages:
- **Overview page** — consolidated cross-instrument market view (fires on tab load)
- **Strategy page** — strategy rationale shown before the result grid (fires on Design Strategy click)

Fully local — no external LLM. Deterministic reasoning layer today; `_build_narrative()` is the single swap point when LLM is introduced.

---

## Key Design Decisions (locked — do not re-derive)

| Decision | Answer |
|---|---|
| Endpoint | `POST /api/v1/commentary` — new, workflow tier |
| Request schema | `{ app, page, instrument }` — `app` always required |
| Valid apps | `rita`, `ds`, `portfolio`, `ops` |
| Overview instruments | NVIDIA (US), ASML (EU), NIFTY + BANKNIFTY (India) |
| Overview trigger | Auto-fires on Overview section load |
| Strategy trigger | Fires in parallel with `POST /api/v1/strategy` on button click |
| Strategy display | Commentary typewriter first, then result grid below |
| Reasoning — overview | 3 axes: geographic (US/EU/India), D/W/M timeframe, relative ranking |
| Reasoning — strategy | Prose rationale from `get_allocation_recommendation()` outputs |
| Narrative assembly | `_build_narrative(data: dict) -> str` — rule-based templates today |
| Logging | New `commentary_logs` DB table — own ORM model + repository + Alembic migration; NOT the alerts table |
| Monitor KPIs | Add `commentary_count`, `commentary_avg_latency_ms`, `commentary_error_count` to `/api/v1/chat/monitor` — read from `commentary_logs` table |
| UI pattern | `_showCommentaryNarrator()` in new `commentary.js` — wraps agent-panel typewriter |

Full requirements: `project-office/features/May/06 ai-commentary/requirements.md`

---

## /enhance Run Status (Run ID: 20260515-1420)

Task brief: `project-office/task-briefs/task-brief-20260515-1420.md`

| Step | Agent | Status | Notes |
|---|---|---|---|
| Step 2 | PM | ✅ Complete | Approved. 4 risk flags (all manageable). |
| Step 3a | Architect | ✅ Complete | Design passed all 5 checks first attempt. 14 files to touch. |
| Step 3b | TechWriter (record design) | ✅ Complete | Design recorded into task brief. |
| Step 4 | Engineer | ▶ NEXT | Read task brief + skill file. Worktree isolation required. 14 files. Alembic hard gate. |
| Step 5 | QA | ⏳ Pending | — |
| Step 6 | TechWriter (Confluence) | ✅ Complete | Specs verified. Confluence page published. |

---

## Files to Be Created/Modified (expected)

| File | Type | Notes |
|---|---|---|
| `src/rita/api/v1/workflow/commentary.py` | New | Router + reasoning layer + DB audit write via CommentaryLogRepository |
| `src/rita/schemas/commentary.py` | New | Pydantic request/response + CommentaryLogCreate schemas |
| `src/rita/models/commentary_log.py` | New | SQLAlchemy ORM model for `commentary_logs` table |
| `src/rita/repositories/commentary_log.py` | New | CommentaryLogRepository (create + summary query) |
| `alembic/versions/xxxx_add_commentary_log.py` | New | Migration: CREATE TABLE commentary_logs |
| `src/rita/api/v1/workflow/chat.py` | Modify | Add 3 commentary KPI fields to monitor endpoint (reads from commentary_logs via repo) |
| `src/rita/main.py` | Modify | Register commentary router |
| `dashboard/js/rita/commentary.js` | New | `showOverviewCommentary()`, `showStrategyCommentary()`, `loadOverviewCommentary()` |
| `dashboard/js/rita/export.js` | Modify | Refactor `runStrategy()` to `Promise.allSettled` with commentary |
| `dashboard/js/rita/market-signals.js` | Modify | Call `loadOverviewCommentary()` on section load |
| `dashboard/js/rita/main.js` | Modify | Import commentary module + window binding |
| `rita.html` | Modify | Add narrator DOM elements to overview + strategy sections |
| `project-office/specs/Spec_RITA_App.md` | Modify | Add endpoint to workflow tier table + update chat/monitor contract |
| `project-office/specs/Spec_JS_Code.md` | Modify | Add commentary.js to module structure |

---

## PM Risk Flags (from Step 2)

1. `_get_df()` must be confirmed accessible in the workflow commentary router context.
2. Chat monitor contract change (`Spec_RITA_App.md` + `Spec_JS_Code.md`) must land in same commit.
3. `runStrategy()` `Promise.all` refactor must not block either request.
4. `log_event()` helper signature must be verified before DB audit wiring.

---

## Post-Merge Task — Agent Build DB Write (do not defer as seeding patch)

When this /enhance run completes, the run data must be written directly to the `agent_build_runs`
table — not via a seed script applied later. Actual token counts (from API response metadata)
must be captured alongside the estimated values so the Agent Builds page can show the delta.

Required:
- `/enhance` Step 7 writes run log to both `runs/run-*.json` AND the `agent_build_runs` DB table
- Each agent record carries `token_estimate` (existing) + `token_actual` (from API response usage)
- `aggregate_metrics.py` reads `token_actual` when present, falls back to `token_estimate`
- Agent Builds page shows estimated vs actual columns side by side

This is infrastructure work on the `/enhance` orchestrator itself, not on the AI Commentary feature.
Track in a separate feature folder when scheduling.

---

## End-of-Feature Checklist

- [x] Update this file status to `complete`
- [x] Add one-line note to root `PLAN_STATUS.md`
- [x] Run Confluence sprint board script
- [x] Git commit
