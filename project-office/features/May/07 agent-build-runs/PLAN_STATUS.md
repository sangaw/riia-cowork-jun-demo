# Agent Build Runs — Actual Token Tracking (DB Write) — Feature Plan Status
**Last updated:** 2026-05-15
**Feature brief:** `project-office/task-briefs/task-brief-20260515-1500.md`
**Run log:** `riia-ai-org/agent-ops/runs/run-20260515-1500.json` (not yet written — Engineer not started)

---

## Current Status: COMPLETE — merged to master at 89fb5dd (2026-05-16)

---

## /enhance Rollout

| Step | Role | Task | Status | Notes |
|---|---|---|---|---|
| Step 1 | Orchestrator | Task brief created | `[x]` | Brief: task-brief-20260515-1500.md |
| Step 2 | PM | Sprint validation | `[x]` | Approved. 5 risk flags (see brief). Token estimate: ~13,800 |
| Step 3 | Architect | Full technical design | `[x]` | No new endpoints. 3 files to change + 1 migration to apply. 8-item DoD. Design recorded in brief. |
| Step 4 | Engineer | Implement — migration, repo write methods, helper script, enhance.md update | `[x]` | Branch: worktree-agent-a9b1e7c77854a2689, commit 802da99, DoD 8/8 |
| Step 5 | QA | Unit tests + contract check | `[x]` | 23/23 tests passed, full contract match |
| Step 6 | TechWriter | Confluence + spec confirmation | `[x]` | Engineering page updated to v11 |
| Merge | Engineer | Merge worktree branch into master | `[x]` | Merge commit 89fb5dd |

---

## Resume Instructions — Step 4 (Engineer)

Run `/enhance` is **already in progress**. Do NOT restart from Step 1.

**Spawn Engineer agent with `isolation: "worktree"`** using the brief at:
`project-office/task-briefs/task-brief-20260515-1500.md`

Engineer must do exactly these 5 things (in order):

1. **Apply the existing migration** — run from `riia-jun-release/`:
   ```
   python -m alembic upgrade head
   ```
   Expected output: `Running upgrade 47b9b71fa2f6 -> a3f9c1e82b5d, add actual_tokens_total to agent_build_agents`
   The migration file already exists at `alembic/versions/a3f9c1e82b5d_add_actual_tokens_total.py` — do not create a new one.

2. **Add write methods to `AgentBuildRepository`** (`src/rita/repositories/agent_builds.py`):
   - `upsert_run(run_data: dict) -> AgentBuildRunModel` — upserts by run_id, sets recorded_at on insert only
   - `upsert_agents(run_id: str, agents: list[dict], actual_tokens_total: int | None) -> list[AgentBuildAgentModel]` — upserts by agent_id=f"{run_id}-{role}", maps actual_tokens dict→int, commits once

3. **Create `riia-ai-org/agent-ops/write_run_to_db.py`** — standalone CLI script:
   - Args: `<run_json_path>` (positional) + `--actual-tokens <int>` (optional)
   - Validates run_id, app, overall_status present in JSON before upsert
   - If --actual-tokens: injects `{"total_tokens": N}` into each agent's actual_tokens in JSON, rewrites file
   - Catches OperationalError (missing table) with clear message → exit 1
   - Exits 0 on success; prints `DB write complete: run_id={run_id}, agents={n}`
   - Uses `SessionLocal()` directly (not FastAPI get_db); must be run from `riia-jun-release/` for SQLite path

4. **Update `.claude/commands/enhance.md` Step 7** — after the `✓ Run log written` line, before `aggregate_metrics.py`, add:
   ```
   python ../riia-ai-org/agent-ops/write_run_to_db.py ../{RUN_LOG_PATH} [--actual-tokens {integer if known}]
   ```
   DB write failure is non-blocking — orchestrator continues if script exits 1.

5. **Run ruff, commit, fill in brief** — `ruff check src/`; commit `feat(ops): write actual run tokens to agent_build_runs DB`; update `[Engineer] Implementation Log` in brief.

**Key design decisions already made (do not re-open):**
- No new API endpoint — write via CLI script, not HTTP
- `actual_tokens_total` stored as Integer in DB; `AgentOut.actual_tokens` dict shape unchanged
- `aggregate_metrics.py` needs no code changes — helper writes back to JSON file

---

## Feature Scope

| Area | Change |
|---|---|
| `riia-jun-release/alembic/versions/a3f9c1e82b5d_...py` | Apply (already on disk) — `alembic upgrade head` |
| `riia-jun-release/src/rita/repositories/agent_builds.py` | Add `upsert_run()` + `upsert_agents()` write methods |
| `riia-ai-org/agent-ops/write_run_to_db.py` | New helper script (create) |
| `.claude/commands/enhance.md` | Update Step 7 to call helper after JSON write |
| `riia-ai-org/agent-ops/aggregate_metrics.py` | No change — confirm only |

---

## Blockers

None — design is complete, migration file exists, all decisions resolved.

---

## Run Log

| Step | Timestamp | Agent | Branch | Commit | Outcome |
|---|---|---|---|---|---|
| Steps 1–3 | 2026-05-15-1500 | /enhance orchestrator | — | — | PM + Architect complete |


Handoff state:
  - Feature 07 PLAN_STATUS.md — updated with step-by-step Engineer resume instructions
  - Root PLAN_STATUS.md — one-line pointer added
  - Memory + MEMORY.md index — reflect current status with locked design decisions

  Next session: Start at Step 4 — spawn Engineer agent with isolation: "worktree", point at task-brief-20260515-1500.md. The brief has the full Architect
  design. Migration file already exists on disk, just needs alembic upgrade head. 3 files to write.