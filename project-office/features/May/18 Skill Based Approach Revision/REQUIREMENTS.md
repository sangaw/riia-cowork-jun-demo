# Feature 18 — Skill-Based Approach Revision

**Created:** 2026-05-26  
**Owner:** Project Office  
**Status:** In Progress  
**Skill:** `project-office/skills/` (meta — this feature improves the skill system itself)

---

## Objective

The current skill system works but has structural problems that compound over time: rules duplicated across 3–4 files, no explicit guardrail tier separation, commands and skills maintained in parallel, and inconsistent feature documentation. This feature revision fixes those structural problems without changing how agents are invoked.

**Success metric:** Any rule change requires editing exactly one file. Any new agent can load its complete guardrail set from three files (org + role + project), not from CLAUDE.md + agent card + skill file + codebase-constraints.

---

## Background

Problems identified in 2026-05-26 review session:

| Problem | Effect |
|---|---|
| Rules appear in 3–4 files simultaneously | Guardrail drift — one file updated, others miss the change |
| No explicit org/role/project separation | Agents cannot distinguish absolute rules from role-scoped or project-specific ones |
| Slash commands duplicate skill file content | Two files to update per rule change |
| Feature folders lack consistent structure | No standard for requirements, status tracking, or eng context |
| Review agent only does code review | No design review gate before Engineer starts work |

Full analysis: session notes 2026-05-26.

---

## Scope

### In Scope
- Create three-tier guardrail hierarchy (org / role / project)
- Refactor CLAUDE.md into a pure navigation map
- Establish skills as single source of truth; commands become thin wrappers
- Add Design Review gate to `/enhance` orchestrator (post-Architect, pre-Engineer)
- Add Code Review gate to `/enhance` orchestrator (post-Engineer, pre-QA)
- Upgrade `reviewer.md` agent card to cover both review modes
- Standardize feature folder template with three mandatory files
- Add skill-drift detection to `/end-day`

### Out of Scope
- Changes to application code in `riia-jun-release/`
- Changes to QA agent responsibilities
- New features in RITA, FnO, or Ops dashboards

---

## Phase 1 — Three-Tier Guardrail Hierarchy

**Goal:** One file per guardrail tier. Rules live in exactly one place. Skill files and agent cards reference rather than duplicate.

### Deliverables

| File | Content |
|---|---|
| `project-office/guardrails/org.md` | Universal rules: secrets, structlog, external data ban, data residency, file-read limits, agent quota |
| `project-office/guardrails/roles/engineer.md` | Engineer-scoped: worktree required, ADR-001/002, no print, no core/ without QA, no rita_input/ writes |
| `project-office/guardrails/roles/architect.md` | Architect-scoped: design output only, no code, task brief [Architect] section schema |
| `project-office/guardrails/roles/qa.md` | QA-scoped: tests only, no source changes, coverage threshold |
| `project-office/guardrails/roles/pm.md` | PM-scoped: PLAN_STATUS.md is the authority, validation only |
| `project-office/guardrails/roles/techwriter.md` | TechWriter-scoped: Confluence + spec update only |
| `project-office/guardrails/roles/reviewer.md` | Reviewer-scoped: report only, two modes (Design / Code), cite rule per finding |
| `project-office/guardrails/project.md` | RITA-specific: API tier routing table, lot sizes, data paths, HTML file size limits |

### Acceptance Criteria
- [ ] Every rule currently in CLAUDE.md "What NOT to Do" section maps to exactly one guardrail file
- [ ] Every rule in `codebase-constraints.md` maps to exactly one guardrail file
- [ ] `guardrails/org.md` contains no RITA-specific content
- [ ] `guardrails/project.md` contains no role-specific content (it applies to all roles equally)

---

## Phase 2 — CLAUDE.md Navigation Refactor

**Goal:** CLAUDE.md is a navigation map only. No rules embedded. Everything it used to enforce is now in a guardrail file it references.

### Deliverables
- Rewritten `CLAUDE.md` — removes "What NOT to Do" section, removes embedded API routing table, removes embedded agent team guardrails
- Adds three reference lines: "Org guardrails: `project-office/guardrails/org.md`", "Role guardrails: `project-office/guardrails/roles/`", "Project guardrails: `project-office/guardrails/project.md`"
- Agent team table stays (it is structure, not rules)
- Spec file routing table stays (it is navigation, not rules)
- Daily commands table stays (it is interface, not rules)

### Acceptance Criteria
- [ ] No imperative "do not" statements in CLAUDE.md (replaced by references)
- [ ] The API tier "Never" rows move entirely to `guardrails/project.md`
- [ ] CLAUDE.md line count drops by at least 30%
- [ ] Auto-load still works — CLAUDE.md remains the entry point, now as a clean index

---

## Phase 3 — Skills as Single Source of Truth

**Goal:** Slash commands become thin wrappers (15–20 lines). Skill files hold all task rules. No content is duplicated between the two.

### Deliverables
- All 12 skill files get a guardrail header block:
  ```
  Guardrail refs: org-guardrails · {role}-role · rita-project
  Last validated against spec: YYYY-MM-DD
  Spec source: Spec_X.md [+ Spec_Y.md]
  ```
- All 18 slash commands refactored to a standard wrapper format:
  ```
  You are a {Role} agent. Task: $ARGUMENTS
  Load guardrails: org + {role} + project
  Load skill: project-office/skills/skill-{name}.md
  Execute the skill's Step-by-Step exactly.
  ```
- `project-office/skills/` becomes the authoritative version-controlled knowledge layer
- `codebase-constraints.md` content merged into `guardrails/roles/engineer.md` and deprecated

### Acceptance Criteria
- [ ] No skill rule text appears in any slash command file
- [ ] All 12 skill files have guardrail header + last-validated date
- [ ] `codebase-constraints.md` has a deprecation notice pointing to the guardrail files
- [ ] Existing slash commands still work identically from the user's perspective

---

## Phase 4 — Review Agent (Design + Code)

**Goal:** Add two review gates to the `/enhance` orchestrator. Design Review runs after Architect and before Engineer. Code Review runs after Engineer and before QA. QA continues unchanged.

### Review Agent — Two Modes

#### Mode A: Design Review (post-Architect)
- **Reads:** requirements section of task brief + `[Architect] Design` section
- **Validates:**
  - Does the proposed API contract satisfy the stated requirements?
  - Are all UI DOM targets specified?
  - Is the tier placement correct per ADR-001?
  - Are the files-to-touch complete (backend + frontend + spec)?
  - Is the Definition of Done checklist populated?
- **Output:** `[Reviewer] Design Review` section in task brief — PASS or FAIL with specific gap list
- **Gate:** Orchestrator does not spawn Engineer if Design Review = FAIL

#### Mode B: Code Review (post-Engineer)
- **Reads:** task brief (requirements + architect design) + changed files from engineer's branch
- **Validates:**
  - Does the implementation match the architect's design (endpoint path, response fields, DOM targets)?
  - Are all engineer-role guardrails followed (worktree, ADR compliance, no print, spec updated)?
  - Does the JS contract match the handler's return dict (field-by-field)?
  - Does `ruff check src/` pass?
- **Output:** `[Reviewer] Code Review` section in task brief — PASS, CONDITIONAL (advisory issues), or FAIL (blocking issues)
- **Gate:** Orchestrator does not spawn QA if Code Review = FAIL

### Deliverables
- Updated `project-office/agents/reviewer.md` — covers both modes with explicit input/output/gate rules
- Updated `project-office/task-briefs/TEMPLATE.md` — adds `[Reviewer] Design Review` and `[Reviewer] Code Review` sections
- Updated `.claude/commands/enhance.md` — adds Review agent spawns at Steps 3.5 (after Architect) and 4.5 (after Engineer)
- Updated `Agentic_AI_Enterprise_Approach.md` — documents Review agent in orchestration flow diagram

### Orchestration Flow (updated)
```
PM → Architect → [Design Review] → Engineer → [Code Review] → QA → TechWriter
```

### Acceptance Criteria
- [ ] `/enhance` orchestrator spawns Design Reviewer after Step 3 (Architect) and Code Reviewer after Step 4 (Engineer)
- [ ] Orchestrator re-invokes the relevant agent (Architect or Engineer) on FAIL with the reviewer's gap list
- [ ] QA agent prompt and responsibilities unchanged
- [ ] Task brief template has both reviewer sections with required fields
- [ ] reviewer.md documents what the agent can and cannot do (report only — no code, no design changes)

---

## Phase 5 — Feature Folder Standardization + Drift Detection

**Goal:** Every feature has the same three-file structure. Skill drift is automatically surfaced at end of day.

### Feature Folder Template
Create `project-office/features/TEMPLATE/` with:
- `REQUIREMENTS.md` — sections: Objective, Background, Scope (in/out), Phases with Acceptance Criteria
- `PLAN_STATUS.md` — sections: current status, session log, pending tasks table
- `eng-context.md` — sections: API contract, files to touch, key decisions, open questions

Every new feature created by the orchestrator (`/enhance`) auto-creates these three stubs from the template.

### Skill Drift Detection (added to `/end-day`)
Add one step to the `/end-day` skill:
```
Check skill drift: run git log --since="7 days ago" --name-only -- project-office/specs/
For each spec file changed, check the matching skill file's "Last validated against spec" date.
If date is older than the spec change, flag: "[DRIFT] skill-X.md not updated after Spec_Y.md changed on DATE"
```

### Deliverables
- `project-office/features/TEMPLATE/REQUIREMENTS.md` (stub with section headers)
- `project-office/features/TEMPLATE/PLAN_STATUS.md` (stub)
- `project-office/features/TEMPLATE/eng-context.md` (stub)
- Updated `project-office/skills/skill-end-of-day.md` — adds drift detection step
- Updated `/enhance` orchestrator — Step 0 auto-creates feature folder from template when a task-brief is created

### Acceptance Criteria
- [ ] Template folder has all three stubs with correct section headings
- [ ] `/end-day` skill includes the drift check step with exact `git log` command
- [ ] `/enhance` creates a feature folder stub when `BRIEF_PATH` is created
- [ ] At least 3 recent features (May/14, May/15, May/16) backfilled with `eng-context.md`

---

## Dependencies

| Phase | Depends on |
|---|---|
| Phase 2 | Phase 1 complete (CLAUDE.md references guardrail files that must exist) |
| Phase 3 | Phase 1 complete (skills reference guardrail files) |
| Phase 4 | Phase 1 complete (reviewer role guardrail file must exist) |
| Phase 5 | Phase 3 complete (drift detection references skill file headers added in Phase 3) |
| Phase 4 | Can be done in parallel with Phases 2 and 3 |

---

## Definition of Done

- [ ] All five phases complete with acceptance criteria checked
- [ ] `reviewer.md` agent card covers both Design Review and Code Review modes
- [ ] `/enhance` orchestrator includes both review gates with re-invoke-on-fail logic
- [ ] CLAUDE.md is a pure navigation map (no embedded rules)
- [ ] Every rule exists in exactly one guardrail file
- [ ] All 12 skill files have guardrail headers with last-validated dates
- [ ] Feature folder template exists and is referenced by `/enhance`
- [ ] Session committed to git with message referencing Feature 18
