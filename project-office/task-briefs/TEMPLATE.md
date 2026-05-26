# Task Brief — {timestamp}
**Run ID:** {YYYYMMDD-HHMM}
**Status:** {in-progress | complete | failed}

---

## Request
{original user request, verbatim — copy exactly from /enhance command input}

## App Target
{rita | fno | ops}

## Skill Selected
`project-office/skills/skill-add-{app}-feature.md`

## Spec Reference
- `project-office/specs/Spec_RITA_App.md`
- `project-office/specs/Spec_JS_Code.md`

---

## [PM] Validation

**Sprint alignment:** {in scope | out of scope — reason}

**Risk flags:**
- {none | list each risk}

**Dependencies:** {none | list blockers or prerequisite tasks}

**Approved to proceed:** {yes | no}

> If no: state reason and stop. Do not spawn Architect agent.

---

## [Architect] Design

**Feature summary:** {1-2 sentences — what this feature does for the user}

**API contract:**
| Field | Value |
|---|---|
| Method | {GET \| POST \| PUT \| DELETE} |
| Path | `/api/...` |
| Query params | {param: type — or "none"} |
| Request body | {field: type — or "none"} |
| Response shape | {field: type for each key field} |
| Auth required | {yes — JWT \| no} |

**Frontend target:**
| Item | Value |
|---|---|
| JS module | `dashboard/js/{app}/{name}.js` |
| Section id | `sec-{name}` |
| DOM element IDs | {list each id that setEl() or mkChart() will target} |
| Window bindings | {list each function to expose on window.*} |

**Files to touch:**
| File | Change |
|---|---|
| `src/rita/api/experience/{app}.py` | Add endpoint |
| `src/rita/schemas/{name}.py` | Add response schema |
| `dashboard/js/{app}/{name}.js` | New module |
| `dashboard/js/{app}/main.js` | Register loader + window bindings |
| `project-office/specs/Spec_RITA_App.md` | Update endpoint inventory |
| `project-office/specs/Spec_JS_Code.md` | Add module to module structure table |

**Edge cases to handle:**
- {list each edge case: empty data, null fields, API errors}

**Definition of Done checklist:**
- [ ] API contract matches (schema fields = JS reads)
- [ ] Experience tier read-only (no db.commit())
- [ ] Section loader registered in main.js
- [ ] Window bindings set in main.js
- [ ] Error handled in JS (try/catch, shows — on failure)
- [ ] Spec updated (both Spec_RITA_App.md and Spec_JS_Code.md)
- [ ] Ruff passes (ruff check src/)
- [ ] No hardcoded values (no localhost, no hardcoded lot sizes)

> Architect: complete ALL fields above before handing off to Engineer. Incomplete sections will be returned.

---

## [Reviewer] Design Review

**Mode:** Design Review  
**Status:** {PASS | FAIL}  
**Reviewed:** [Architect] Design section  
**Against:** Requirements in ## Request

**Findings:**

| # | Finding | Severity | Rule cited | Resolution required |
|---|---|---|---|---|
| — | {description or "No findings"} | {BLOCKING / ADVISORY} | {ADR-001 / project.md §N} | {what must change} |

**Checklist:**
- [ ] Requirements coverage: {PASS / FAIL}
- [ ] API contract completeness: {PASS / FAIL}
- [ ] Frontend contract completeness: {PASS / FAIL}
- [ ] Files-to-touch completeness: {PASS / FAIL}
- [ ] Definition of Done populated: {PASS / FAIL}

**Decision:** {PASS — proceed to Engineer. | FAIL — return to Architect. Must address: [list blocking findings].}

> If FAIL: Orchestrator re-invokes Architect with the blocking findings list. Re-invoke ceiling: 1 automatic retry; escalate to user on second FAIL.

---

## [Engineer] Implementation Log

**Branch:** `feature/{name}-{app}` — never master

**Worktree path:** {from git rev-parse --show-toplevel}

**Commit hash:** {short hash from git log --oneline -1}

**Files changed:**
| File | Change made |
|---|---|
| {file} | {what was changed} |

**API contract verified:** {yes | no — if no, explain deviation}

**Spec updated:** {yes | no — if no, explain why deferred}

**Ruff result:** {passed | failed — paste error if failed}

**Definition of Done — Engineer check:**
- [ ] API contract matches
- [ ] Experience tier read-only
- [ ] Section loader registered
- [ ] Window bindings set
- [ ] Error handled
- [ ] Spec updated
- [ ] Ruff passes
- [ ] No hardcoded values

> Engineer: all 8 DoD items must be checked before marking this section complete.

---

## [Reviewer] Code Review

**Mode:** Code Review  
**Status:** {PASS | CONDITIONAL | FAIL}  
**Reviewed:** [Engineer] Implementation Log + changed files  
**Against:** [Architect] Design + engineer-role guardrails

**Findings:**

| # | File | Line | Finding | Severity | Rule cited |
|---|---|---|---|---|---|
| — | {file or "No findings"} | {line / N/A} | {description} | {BLOCKING / ADVISORY} | {ADR / guardrails/roles/engineer.md §N} |

**Checklist:**
- [ ] Implementation matches design (paths, fields, DOM targets): {PASS / FAIL}
- [ ] JS frontend contract verified: {PASS / FAIL / N/A}
- [ ] Engineer guardrails followed (worktree, no print, no hardcoded secrets/lot sizes): {PASS / FAIL}
- [ ] Spec updated: {PASS / FAIL / N/A}

**Decision:** {PASS — proceed to QA. | CONDITIONAL — proceed to QA; engineer addresses advisory items in follow-up. | FAIL — return to Engineer. Must fix: [list blocking findings].}

> If FAIL: Orchestrator re-invokes Engineer with the blocking findings list. Re-invoke ceiling: 1 automatic retry; escalate to user on second FAIL.

---

## [QA] Test Results

**Tests written:** {n}

**Test file:** `tests/{unit|integration}/{name}_test.py`

**Tests passed:** {n} / {n}

**Coverage delta:** {+/- n%} (run: `pytest --cov=src/rita tests/`)

**Contract check:** {list each response field in schema vs handler return — match | mismatch}
| Schema field | Handler returns | Match? |
|---|---|---|
| {field} | {value/type} | {yes \| no} |

**Edge cases tested:**
- {list each edge case from Architect section — tested? yes/no}

**Definition of Done — QA check:**
- [ ] At least 1 unit test per new endpoint
- [ ] All tests pass
- [ ] API-frontend contract verified (no field name mismatches)
- [ ] Edge cases from Architect section covered

---

## [TechWriter] Documentation

**Confluence page updated:** {URL | n/a — reason}

**Page section modified:** {section name on the Confluence page}

**Spec file confirmed current:** {yes | no — if no, update before closing}

**Task brief archived:** {yes — file renamed from TEMPLATE to task-brief-{timestamp}.md}

**Definition of Done — TechWriter check:**
- [ ] Confluence page reflects new feature
- [ ] Spec_RITA_App.md endpoint inventory is accurate
- [ ] Spec_JS_Code.md module structure table is accurate
- [ ] Task brief saved as completed artifact

---

*Brief generated by /enhance orchestrator. Each section written by the designated agent role.*
