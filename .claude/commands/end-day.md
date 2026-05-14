---
description: Run all 3 mandatory end-of-day steps: PLAN_STATUS + Confluence + git commit
---

Run all 3 end-of-day steps in order. Do not skip any step. Do not mark the day done until all 3 are complete.

## Step 1 — Update PLAN_STATUS.md
- Mark today's day row as `[x]` done
- Add a brief notes column entry (what was delivered)
- Update the "Last updated" date at the top to today's date
- Update the "Current Sprint" header if a sprint just completed

## Step 2 — Publish Confluence sprint board
Identify the current sprint number N from PLAN_STATUS.md.
Run: `CONFLUENCE_EMAIL=contact@ravionics.nl python project-office/confluence/sprint-boards/publish_sprint{N}_board.py`
(Run from the workspace root: `riia-cowork-jun/`)
If the script does not exist yet, skip this step and note it as a blocker.

## Step 3 — Git commit
Stage all files changed today. Commit with a message in this format:
```
<type>(<scope>): <what was delivered today>

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
```
Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`

After committing, run `git status` to confirm working tree is clean.

## Done
Report: "Day complete. All 3 end-of-day steps done. Commit: <short hash>"
