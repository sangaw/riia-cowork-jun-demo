---
description: Diagnose and fix a RITA dashboard JS bug by tracing code — no server start
---

You are an Engineer agent fixing a frontend defect in the RITA dashboard.

**Bug report:** $ARGUMENTS

---

## Step 1 — Load the skill file

Read `project-office/skills/skill-fix-js-bug.md` before doing anything else.
It contains: the module map, the 5-step trace protocol, known gotchas, and the definition of done.

---

## Step 2 — Absolute rules (never violate)

- **Do NOT start `uvicorn` or `python start.py`** to reproduce the bug
- **Do NOT `curl` endpoints** — read the handler's `return` dict from source
- **Do NOT read `rita.html` / `fno.html` / `ops.html` in full** — they are 2,900–4,000 lines; use `grep` for the specific element id you need
- **Do NOT refactor** surrounding code while fixing the bug
- **Fix must be minimal** — one function, one condition, one guard

---

## Step 3 — Trace and fix

Follow the 5-step trace protocol from the skill file:
1. Identify the broken section and its loader function
2. Find the `api()` call and list every field the JS reads from the response
3. Read the API handler — confirm every expected field is in the `return` dict
4. Trace every `setEl(id, ...)` call — confirm each element `id` exists in the HTML
5. Identify root cause category from the symptom table

Then make the minimal targeted fix.

---

## Step 4 — Verify definition of done

Before reporting complete, confirm every item in the skill file's "Definition of Done" section.
