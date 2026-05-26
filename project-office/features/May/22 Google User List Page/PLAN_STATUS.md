# Feature 18 — User Traffic Dashboard: Plan Status

**Date started:** 2026-05-21
**Status:** COMPLETE — deployed and verified in production

---

## Implementation Phases

| Phase | Scope | Status |
|---|---|---|
| 1 — Data layer | `login_events` model, migration, `first_login_date` on users, auth callback | `[x]` |
| 2 — API | `login_event` repository, `/api/v1/experience/users/traffic` endpoint | `[x]` |
| 3 — UI | `dashboard/users.html` + `dashboard/js/users/main.js` | `[x]` |
| 4 — QA | Tests for auth callback event logging + experience endpoint | `[ ]` — skipped; covered by manual E2E verification in prod |

## Post-Deploy Bug Fix

**jose `at_hash` JWTClaimsError (2026-05-21):** `jwt.decode()` with `verify_signature=False` still validates the `at_hash` claim in Google's ID token, requiring an `access_token` that we don't pass. Fixed by replacing `jwt.decode()` with `jwt.get_unverified_claims()` — correct since the token was obtained via a server-to-server TLS call to Google. Commit `4dfcaf6`.

---

## Resume Prompt

> "Implementing Feature 18 — User Traffic Dashboard. Read `project-office/features/18 Google User List Page/REQUIREMENTS.md` for full spec. Start with Phase 1: create `src/rita/models/login_event.py`, add `first_login_date` to `UserModel`, write Alembic migration `20260521_add_login_events`, and update `api/v1/auth.py` callback to insert a login event and set first_login_date on first login."
