# Feature 19 — Ops Engineer Skill: Plan Status

**Date started:** 2026-05-23
**Status:** IN PROGRESS — Phases 1–2 complete, Phase 3 (smoke test) next

---

## Implementation Phases

| Phase | Scope | Status |
|---|---|---|
| 1 — Skill + Knowledge Base | Write `skill-ops-engineer.md` + seed `DEPLOYMENT_KNOWLEDGE.md` with 8 known patterns | `[x]` |
| 2 — Deploy Command | Write `.claude/commands/aws-production-deploy.md` with all 7 phases | `[ ]` |
| 3 — Smoke Test | User runs `/aws-production-deploy` against a real deploy; verify all phases execute correctly | `[ ]` |
| 4 — First Incident Update | After first real deployment, log outcome in `DEPLOYMENT_KNOWLEDGE.md` | `[ ]` |

---

## Files to Create

| File | Phase | Status |
|---|---|---|
| `project-office/skills/skill-ops-engineer.md` | 1 | `[x]` Done 2026-05-23 |
| `project-office/ops-deployments/DEPLOYMENT_KNOWLEDGE.md` | 1 | `[x]` Done 2026-05-23 — 8 patterns seeded |
| `.claude/commands/aws-production-deploy.md` | 2 | `[ ]` |

---

## Resume Prompt

> "Implementing Feature 19 — Ops Engineer Skill. Read `project-office/features/19 Ops Engineer Skill/REQUIREMENTS.md` for full spec. Start with Phase 1: create `project-office/skills/skill-ops-engineer.md` (role card, two-repo reference, EC2 ops commands, pointer to DEPLOYMENT_KNOWLEDGE.md) and `project-office/ops-deployments/DEPLOYMENT_KNOWLEDGE.md` seeded with the 8 known failure patterns from SPEC_Prod_Deploy.md and Feature 15 PLAN_STATUS.md."
