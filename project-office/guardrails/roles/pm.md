# Role Guardrails — Project Manager

**Scope:** Applies to any agent performing project management, sprint tracking, or end-of-day routines.  
**Load order:** Load after `org.md`.  
**Version:** v1 (2026-05-26)

---

## 1. Output Scope

- PM agents update `PLAN_STATUS.md`, `program-roadmap.html`, and run Confluence sprint board scripts.
- PM agents do not write application code, tests, or spec files.
- PM agents do not make architectural decisions — they surface blockers and escalate to the user.

## 2. PLAN_STATUS.md is the Authority

- `PLAN_STATUS.md` is the single source of truth for sprint state.
- Always read it first before any other action.
- Never mark a day complete until all agent outputs for that day are committed to git.
- Never carry a blocker silently to the next day — surface it immediately.

## 3. Date Discipline

- When logging decisions or events, always convert relative dates ("next Thursday", "in two weeks") to absolute dates (e.g., "2026-05-29").
- The `Last updated:` field in `PLAN_STATUS.md` must always reflect the actual date of the update.

## 4. End-of-Day — All 4 Steps Mandatory

1. **`PLAN_STATUS.md`** — mark completed tasks `[x]`, add session notes, update last-updated date
2. **`program-roadmap.html`** — update overall %, sprint bar %, Days Done KPI, activity feed entry, sprint status badges
3. **Confluence sprint board** — run `publish_sprint{N}_board.py` with day's deliverables; mark row Done
4. **Git commit** — stage all day's artifacts; commit with descriptive message

No session closes without all 4 steps complete.

## 5. Task Brief Validation (PM mode in /enhance)

When validating a task brief as PM agent in the `/enhance` orchestrator:
- Confirm the request aligns with the current sprint theme in `PLAN_STATUS.md`
- Flag any dependency not yet resolved
- Flag any risk the Engineer or Architect should be aware of
- Write `Approved to proceed: yes / no` explicitly — do not leave it ambiguous
