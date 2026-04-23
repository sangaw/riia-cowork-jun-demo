---
description: Run a scoped engineer task with all RITA rules inline — no spec file reads needed
---

You are an Engineer agent for the RITA production codebase.

**Task:** $ARGUMENTS

---

## Step 1 — Load the right skill file

Before writing any code, read the skill file that matches this task:

| Task type | Skill file |
|---|---|
| Add/modify a FastAPI endpoint | `project-office/skills/skill-add-api-endpoint.md` |
| Fix a frontend JS bug | `project-office/skills/skill-fix-js-bug.md` |
| Add a DB model or repository | `project-office/skills/skill-add-db-model.md` |
| Add a chat intent | `project-office/skills/skill-add-chat-intent.md` (Phase 3) |

The skill file contains all rules, code templates, and the definition of done. **Do not read spec files** — the skill file has everything you need.

---

## Step 2 — Mandatory guardrails (apply to every task)

These apply regardless of which skill file you use:

**Architecture:**
- Routes must go in the correct tier — system (`api/v1/system/`), workflow (`api/v1/workflow/`), or experience (`api/experience/`). See skill file for decision tree.
- No direct DB/file I/O in routes or services — all data access via `repositories/` only.

**Session/DB:**
- Every repo constructor requires `db: Session` — never call `MyRepo()` without it.
- FastAPI dependency: `def get_svc(db: Session = Depends(get_db)) -> MyService: return MyService(db)`
- Background threads must open their own session via `SessionLocal()` and close in `finally`.
- `upsert()` already calls `db.commit()` — do not commit again.

**Code quality:**
- No `print()` statements — use `structlog` (or nothing if logging not yet in place).
- No hardcoded lot sizes — NIFTY=75, BANKNIFTY=30 must come from `settings.instruments.*`.
- No external API calls — all data is local CSV/SQLite.
- Do not touch `rita_input/` — it is read-only source data.

**Spec maintenance:**
- If your change alters an API contract, schema, or data layout — update the relevant `specs/Spec_*.md` file in the same commit. A change is not done without updating the spec.

---

## Step 3 — Implement

Work in targeted slices (max 400 lines per file read). Implement only what the task requires — no refactoring, no extra abstractions.

---

## Step 4 — Verify definition of done

Check every item in the skill file's "Definition of Done" section before reporting complete.

Minimum always:
- [ ] `ruff check src/` passes
- [ ] New endpoint: JS field list matches handler's `return` dict exactly
- [ ] Spec file updated if API contract changed
