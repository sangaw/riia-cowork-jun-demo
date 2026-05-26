# Feature 18 — Skill-Based Approach Revision: Plan Status

**Last updated:** 2026-05-26  
**Overall status:** `[x] Complete`  
**Requirements:** `project-office/features/May/18 Skill Based Approach Revision/REQUIREMENTS.md`

---

## Phase Summary

| Phase | Title | Status | Blocker |
|---|---|---|---|
| Phase 1 | Three-Tier Guardrail Hierarchy | `[x] Complete` | — |
| Phase 2 | CLAUDE.md Navigation Refactor | `[x] Complete` | Phase 1 |
| Phase 3 | Skills as Single Source of Truth | `[x] Complete` | Phase 1 |
| Phase 4 | Review Agent (Design + Code) | `[x] Complete` | Phase 1 |
| Phase 5 | Feature Folder Standardization + Drift Detection | `[x] Complete` | Phase 3 |

---

## Phase 1 — Three-Tier Guardrail Hierarchy

**Status:** `[ ] Not started`  
**Agent:** Engineer (project-office files — no worktree needed; these are meta files)  
**Effort estimate:** ~2 hours

### Tasks

| # | Task | Status | Notes |
|---|---|---|---|
| 1.1 | Create `project-office/guardrails/org.md` | `[ ]` | Pull rules from CLAUDE.md "What NOT to Do", engineer.md, codebase-constraints.md |
| 1.2 | Create `project-office/guardrails/roles/engineer.md` | `[ ]` | Extract engineer-specific guardrails from engineer.md + codebase-constraints.md |
| 1.3 | Create `project-office/guardrails/roles/architect.md` | `[ ]` | Extract from architect.md |
| 1.4 | Create `project-office/guardrails/roles/qa.md` | `[ ]` | Extract from qa.md |
| 1.5 | Create `project-office/guardrails/roles/pm.md` | `[ ]` | Extract from project-manager.md |
| 1.6 | Create `project-office/guardrails/roles/techwriter.md` | `[ ]` | Extract from techwriter.md |
| 1.7 | Create `project-office/guardrails/roles/reviewer.md` | `[ ]` | New — covers Design Review and Code Review modes |
| 1.8 | Create `project-office/guardrails/project.md` | `[ ]` | API tier table, lot sizes, RITA-specific constraints |
| 1.9 | Verify: every rule exists in exactly one file | `[ ]` | Cross-check against CLAUDE.md and codebase-constraints.md |

### Acceptance Gate
All 8 files exist. No rule text is duplicated across guardrail files. `org.md` has no RITA-specific content. `project.md` has no role-specific content.

---

## Phase 2 — CLAUDE.md Navigation Refactor

**Status:** `[ ] Not started` — blocked on Phase 1  
**Agent:** Engineer (project-office)  
**Effort estimate:** 30 minutes

### Tasks

| # | Task | Status | Notes |
|---|---|---|---|
| 2.1 | Remove "What NOT to Do" section from CLAUDE.md | `[ ]` | Replace with reference to `guardrails/org.md` |
| 2.2 | Remove embedded API routing "Never" rows | `[ ]` | Move to `guardrails/project.md` |
| 2.3 | Add guardrail reference block to CLAUDE.md | `[ ]` | Three lines: org / roles / project |
| 2.4 | Verify line count reduction ≥ 30% | `[ ]` | Current: ~160 lines; target: ≤ 110 |
| 2.5 | Verify auto-load still works | `[ ]` | CLAUDE.md must remain the project entry point |

### Acceptance Gate
CLAUDE.md contains no imperative "do not" rules. References to guardrail files are present. Line count reduced.

---

## Phase 3 — Skills as Single Source of Truth

**Status:** `[ ] Not started` — blocked on Phase 1  
**Agent:** Engineer (project-office)  
**Effort estimate:** ~1.5 hours

### Tasks

| # | Task | Status | Notes |
|---|---|---|---|
| 3.1 | Add guardrail header block to all 12 skill files | `[ ]` | Header: guardrail refs + last-validated date + spec source |
| 3.2 | Refactor `add-endpoint.md` command → thin wrapper | `[ ]` | Remove all rule content; reference skill file |
| 3.3 | Refactor `add-rita-feature.md` command → thin wrapper | `[ ]` | |
| 3.4 | Refactor `add-fno-feature.md` command → thin wrapper | `[ ]` | |
| 3.5 | Refactor `add-ops-feature.md` command → thin wrapper | `[ ]` | |
| 3.6 | Refactor `add-db-model.md` command → thin wrapper | `[ ]` | |
| 3.7 | Refactor `add-chat-intent.md` command → thin wrapper | `[ ]` | |
| 3.8 | Refactor `add-data-feature.md` command → thin wrapper | `[ ]` | |
| 3.9 | Refactor `add-mobile-feature.md` command → thin wrapper | `[ ]` | |
| 3.10 | Refactor `fix-bug.md` command → thin wrapper | `[ ]` | |
| 3.11 | Refactor `engineer-task.md` command → thin wrapper | `[ ]` | |
| 3.12 | Deprecate `codebase-constraints.md` | `[ ]` | Add notice pointing to guardrail files; do not delete yet |
| 3.13 | Verify: no skill rule text appears in any command file | `[ ]` | Cross-read check |

### Acceptance Gate
All 12 skills have guardrail headers. All refactored commands are ≤ 25 lines. `codebase-constraints.md` has deprecation notice. No content duplication verified.

---

## Phase 4 — Review Agent (Design + Code)

**Status:** `[ ] Not started` — blocked on Phase 1 (reviewer role guardrail must exist)  
**Agent:** Engineer (project-office) — can run in parallel with Phases 2 and 3  
**Effort estimate:** ~2 hours

### Tasks

| # | Task | Status | Notes |
|---|---|---|---|
| 4.1 | Rewrite `project-office/agents/reviewer.md` | `[ ]` | Cover Design Review mode + Code Review mode; two explicit sub-sections |
| 4.2 | Update task brief template | `[ ]` | Add `[Reviewer] Design Review` section (after `[Architect]`) |
| 4.3 | Update task brief template | `[ ]` | Add `[Reviewer] Code Review` section (after `[Engineer]`) |
| 4.4 | Update `/enhance` orchestrator — Design Review gate | `[ ]` | Insert between Step 3 (Architect) and Step 4 (Engineer); re-invoke Architect on FAIL |
| 4.5 | Update `/enhance` orchestrator — Code Review gate | `[ ]` | Insert between Step 4 (Engineer) and Step 5 (QA); re-invoke Engineer on FAIL |
| 4.6 | Update `Agentic_AI_Enterprise_Approach.md` flow diagram | `[ ]` | Add Reviewer to PM→Arch→[Rev]→Eng→[Rev]→QA→TW chain |
| 4.7 | Verify QA agent prompt unchanged | `[ ]` | QA responsibilities must not shift |

### Acceptance Gate
`/enhance` orchestration has two Review gates. Each gate can PASS (advance) or FAIL (re-invoke with gap list). QA agent card is unchanged. Both reviewer sections appear in the task brief template.

---

## Phase 5 — Feature Folder Standardization + Drift Detection

**Status:** `[ ] Not started` — blocked on Phase 3 (drift detection requires skill headers from Phase 3)  
**Agent:** Engineer (project-office)  
**Effort estimate:** 1 hour

### Tasks

| # | Task | Status | Notes |
|---|---|---|---|
| 5.1 | Create `project-office/features/TEMPLATE/REQUIREMENTS.md` | `[ ]` | Stub with mandatory sections |
| 5.2 | Create `project-office/features/TEMPLATE/PLAN_STATUS.md` | `[ ]` | Stub with status + task table |
| 5.3 | Create `project-office/features/TEMPLATE/eng-context.md` | `[ ]` | Stub with API contract + files-to-touch |
| 5.4 | Add drift detection step to `skill-end-of-day.md` | `[ ]` | git log check + last-validated date comparison |
| 5.5 | Update `/enhance` Step 0 | `[ ]` | Auto-create feature folder from template when task brief is created |
| 5.6 | Backfill `eng-context.md` for May/14, May/15, May/16 | `[ ]` | Retrospective — pull key decisions from session notes |

### Acceptance Gate
Template folder has 3 stubs. `/end-day` skill includes drift check step. `/enhance` creates feature folder. Three recent features have `eng-context.md` filled.

---

## Session Log

| Date | Session | Work Done |
|---|---|---|
| 2026-05-26 | Initial | Requirements written; PLAN_STATUS created; reviewer.md upgraded; feature folder created |
| 2026-05-26 | Implementation | All 5 phases implemented in single session. 8 guardrail files, CLAUDE.md refactored, 12 skill headers, 8 commands converted to wrappers, Design + Code Review gates wired into enhance.md, task brief template updated, feature TEMPLATE folder with 3 stubs, drift detection added to skill-end-of-day.md, codebase-constraints.md deprecated. |

---

## Open Questions

| # | Question | Owner | Status |
|---|---|---|---|
| Q1 | Should the Review agent be a separate Claude Code agent type or always `general-purpose`? | PM | Open |
| Q2 | On Code Review FAIL, should the orchestrator re-invoke Engineer or prompt the user to decide? | PM | Open — recommend: re-invoke once automatically; escalate to user on second fail |
| Q3 | Should `codebase-constraints.md` be deleted in Phase 3 or kept with deprecation notice? | Engineer | Open — recommend: keep with notice for one sprint, then delete |
