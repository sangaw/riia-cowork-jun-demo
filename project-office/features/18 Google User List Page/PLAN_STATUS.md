# Feature 18 — User Traffic Dashboard: Plan Status

**Date started:** 2026-05-21
**Status:** REQUIREMENTS COMPLETE — ready to implement

---

## Implementation Phases

| Phase | Scope | Status |
|---|---|---|
| 1 — Data layer | `login_events` model, migration, `first_login_date` on users, auth callback | `[ ]` |
| 2 — API | `login_event` repository, `/api/v1/experience/users/traffic` endpoint | `[ ]` |
| 3 — UI | `dashboard/users.html` + `dashboard/js/users/main.js` | `[ ]` |
| 4 — QA | Tests for auth callback event logging + experience endpoint | `[ ]` |

---

## Resume Prompt

> "Implementing Feature 18 — User Traffic Dashboard. Read `project-office/features/18 Google User List Page/REQUIREMENTS.md` for full spec. Start with Phase 1: create `src/rita/models/login_event.py`, add `first_login_date` to `UserModel`, write Alembic migration `20260521_add_login_events`, and update `api/v1/auth.py` callback to insert a login event and set first_login_date on first login."
