# AgentOps Failure Catalog

Pre-populated failure modes observed or anticipated in the RITA multi-agent pipeline.
Each entry maps to the agent role that causes it and the skill file rule that prevents it.

---

## FC-001 spec_not_updated
- **Agent role:** Engineer
- **Skill file:** `project-office/skills/skill-add-{app}-feature.md`
- **Rule to add:** "After changing any API contract or data schema, update the relevant Spec file in the same task — before marking Engineer section complete."
- **Observed:** 1 time (run 20260430-1415, rita)
- **Symptom:** Engineer section marked complete but spec file timestamp unchanged; QA/TechWriter work from stale contract.

---

## FC-002 api_contract_missing
- **Agent role:** Architect
- **Skill file:** `project-office/skills/skill-add-{app}-feature.md`
- **Rule to add:** "The [Architect] Design section must include an explicit API contract block: method, path, request schema, response schema. If no new endpoint is needed, write 'No new endpoint — frontend-only change'."
- **Observed:** 0 times
- **Symptom:** Engineer spawned without a clear contract; implements a different endpoint shape than PM expected; QA tests wrong surface.

---

## FC-003 dod_checklist_incomplete
- **Agent role:** Architect
- **Skill file:** `project-office/skills/skill-add-{app}-feature.md`
- **Rule to add:** "Every item in the Definition of Done checklist must be filled with a concrete value (file path, test name, etc.) — never left blank or marked N/A without an explicit reason."
- **Observed:** 0 times
- **Symptom:** Engineer and QA agents skip steps because the DoD items were vague or missing; gate validation passes on incomplete work.

---

## FC-004 test_coverage_skipped
- **Agent role:** QA
- **Skill file:** `project-office/skills/skill-add-{app}-feature.md`
- **Rule to add:** "QA must write at least one unit test and one integration test per task. A coverage delta of 0% is a hard failure — the QA section must not be marked complete without at least one new test file or new test function."
- **Observed:** 0 times
- **Symptom:** QA section written but no new test files exist in the worktree; coverage delta is 0; regressions go undetected.

---

## FC-005 confluence_page_not_found
- **Agent role:** TechWriter
- **Skill file:** `project-office/skills/skill-add-{app}-feature.md`
- **Rule to add:** "TechWriter must verify the Confluence page ID before updating. Read `project-office/confluence/` for the correct page ID constants. If the page cannot be found, halt and surface a warning rather than creating a duplicate."
- **Observed:** 0 times
- **Symptom:** TechWriter creates a new orphaned Confluence page instead of updating the canonical one; duplicate pages accumulate.

---

## FC-006 branch_not_created
- **Agent role:** Engineer
- **Skill file:** `project-office/skills/skill-add-{app}-feature.md`
- **Rule to add:** "Engineer must create a feature branch named `feature/{app}-{short-description}` before writing any code. Committing directly to master is a hard failure."
- **Observed:** 0 times
- **Symptom:** Code changes land on master; no PR created; Architect and PM lose traceability; git history is polluted.

---

## FC-007 pm_approved_without_sprint_check
- **Agent role:** PM
- **Skill file:** `project-office/skills/skill-add-{app}-feature.md`
- **Rule to add:** "PM must read PLAN_STATUS.md and confirm the request fits the current sprint before setting approved: yes. If the sprint is frozen or quota is >80%, PM must set approved: no and explain."
- **Observed:** 0 times
- **Symptom:** Feature approved and built during a merge freeze or quota crunch; engineer work is wasted or must be reverted.
