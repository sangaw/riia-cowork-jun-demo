---
description: Run all 4 mandatory end-of-day steps: PLAN_STATUS + session run log + Confluence + git commit
---

Run all 4 end-of-day steps in order. Do not skip any step. Do not mark the day done until all 4 are complete.

## Step 1 — Update PLAN_STATUS.md
- Mark today's day row as `[x]` done
- Add a brief notes column entry (what was delivered)
- Update the "Last updated" date at the top to today's date
- Update the "Current Sprint" header if a sprint just completed

## Step 2 — Session Run Log + Metrics Refresh
This ensures Agent Build data is current after every session.

**2a — Write a run log if needed.**
Check `riia-ai-org/agent-ops/runs/` for a run log covering today's session:
- If `/enhance` ran today, the orchestrator already wrote one — skip 2a.
- If today's work was a direct fix or multi-session continuation without a `/enhance` run, write one now:
  `riia-ai-org/agent-ops/runs/run-{YYYYMMDD-HHMM}.json`

  Minimal format for direct/manual work:
  ```json
  {
    "run_id": "{YYYYMMDD-HHMM}",
    "app": "{rita|fno|ops|ds}",
    "request": "{one-line description}",
    "skill_file": "n/a",
    "agents": [{
      "role": "engineer", "status": "pass",
      "steps_required": 3, "steps_completed": 3, "adherence_score": 1.0,
      "token_estimate": 800,
      "grounding_checks": { "branch_created": false, "code_changed": true, "spec_updated": false, "ruff_passed": true, "contract_matches_architect": true },
      "failure_modes": [], "notes": "{what changed, commit hash}"
    }],
    "overall_status": "pass",
    "total_tokens_estimated": 800,
    "duration_minutes": 5,
    "branch": "master", "merge_status": "merged", "merge_commit": "{short hash}"
  }
  ```

**2b — Regenerate metrics.json** (always run after 2a):
```
python riia-ai-org/agent-ops/aggregate_metrics.py
```
Run from workspace root `riia-cowork-jun/`. Note any `[ALERT]` lines in the session summary.

## Step 3 — Publish Confluence sprint board
Identify the current sprint number N from PLAN_STATUS.md.
Run: `CONFLUENCE_EMAIL=contact@ravionics.nl python project-office/confluence/sprint-boards/publish_sprint{N}_board.py`
(Run from the workspace root: `riia-cowork-jun/`)
If the script does not exist yet, skip this step and note it as a blocker.

## Step 4 — Git commit
Stage all files changed today. Commit with a message in this format:
```
<type>(<scope>): <what was delivered today>

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
```
Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`

After committing, run `git status` to confirm working tree is clean.

## Done
Report: "Day complete. All 4 end-of-day steps done. Commit: <short hash>"
