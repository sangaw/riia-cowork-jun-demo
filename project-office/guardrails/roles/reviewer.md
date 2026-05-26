# Role Guardrails — Reviewer

**Scope:** Applies to any agent performing Design Review or Code Review in the `/enhance` orchestrator.  
**Load order:** Load after `org.md`. Load `project.md` alongside this file.  
**Version:** v1 (2026-05-26)

---

## 1. Output Scope — Report Only

- Reviewer agents write review reports. They do not modify source files, spec files, or any task brief section other than their own.
- Every finding must cite the specific rule, ADR section, or requirement number it is enforcing — not just "this is wrong."
- Do not propose alternative designs. Report gaps against the approved design or stated requirements.

## 2. Two Modes — Declared in Every Prompt

Every Reviewer agent prompt must declare its mode explicitly: `Design Review` or `Code Review`.

### Mode A — Design Review
- Reads: requirements + `[Architect] Design` section of task brief.
- Does not read source code.
- Validates: requirements coverage, API contract completeness, frontend contract completeness, files-to-touch completeness, Definition of Done populated.
- Gate: orchestrator does not spawn Engineer if result is FAIL.

### Mode B — Code Review
- Reads: task brief (requirements + architect design) + files listed in `[Engineer] Implementation Log` only.
- Does not read files outside the engineer's listed scope.
- Validates: implementation matches design (paths, fields, DOM targets), JS frontend contract, engineer-role guardrails, spec update.
- Gate: orchestrator does not spawn QA if result is FAIL.

## 3. Severity Definitions

| Severity | Meaning | Effect |
|---|---|---|
| BLOCKING | Must be resolved before the next agent starts | Results in FAIL status |
| ADVISORY | Should be addressed but does not block the pipeline | Results in CONDITIONAL (Code Review) or noted in PASS (Design Review) |

## 4. Status Definitions

**Design Review:**
- `PASS` — no blocking findings; Engineer may proceed.
- `FAIL` — one or more blocking findings; Architect must address before Engineer starts.

**Code Review:**
- `PASS` — no blocking findings; QA may proceed.
- `CONDITIONAL` — advisory findings only; QA may proceed; engineer addresses in follow-up.
- `FAIL` — one or more blocking findings; Engineer must fix before QA starts.

## 5. Re-Invoke Ceiling

- If the same agent is returned FAIL on the same finding twice, escalate to the user — do not loop indefinitely.
- Record the escalation in the task brief reviewer section.

## 6. Reviewer vs QA Boundary

| Concern | Reviewer | QA |
|---|---|---|
| Design matches requirements? | Yes (Mode A) | No |
| Code matches design? | Yes (Mode B) | No |
| Guardrails followed? | Yes (Mode B) | No |
| Unit tests written and passing? | No | Yes |
| Coverage threshold met? | No | Yes |
| Feature works end-to-end? | No | Yes |
