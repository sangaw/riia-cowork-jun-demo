# Agent Skill System — Design & Build Guide

**Created:** 2026-04-23  
**Status:** Complete — all three phases built (2026-04-23)  
**Goal:** Reduce per-session token cost from ~25,000 (spec reads) to ~5,000 (skill reads) by pre-merging agent knowledge into task-specific skill files.

---

## Problem: Where Tokens Are Lost

Each engineer session currently burns 15,000–25,000 tokens *before the first line of code*:

| Step | Tokens |
|---|---|
| CLAUDE.md auto-load | ~1,500 |
| PLAN_STATUS.md read | ~1,000 |
| 3–5 spec files read | ~8,000–12,000 |
| Source file slices | ~4,000–8,000 |
| **Total before acting** | **~15,000–25,000** |

Root cause: agent cards describe *roles*, not *tasks*. Every session the agent rediscovers the same rules from the same spec files.

---

## Solution: Three-Layer Skill System

### Layer 1 — Custom Slash Commands (`.claude/commands/`)

Claude Code auto-loads `*.md` files from `.claude/commands/` as project slash commands.  
Invoke as `/start-day`, `/engineer-task`, `/end-day` — no typing long agent prompts.

**Commands to build:**

| Command file | Invoked as | Does |
|---|---|---|
| `start-day.md` | `/start-day` | Reads PLAN_STATUS.md, reports today's tasks, asks which to start |
| `engineer-task.md` | `/engineer-task <description>` | Scoped engineer agent with inline rules, no spec reads |
| `end-day.md` | `/end-day` | Runs all 4 end-of-day steps in sequence |
| `fix-bug.md` | `/fix-bug <description>` | JS→API→DOM trace protocol, no server start |

### Layer 2 — Task Skill Files (`project-office/skills/`)

One file per *class of work* — pre-merging everything the agent needs.  
Agent reads ONE skill file (~300 tokens) instead of FOUR spec files (~4,000 tokens).

| Skill file | Used when | Replaces |
|---|---|---|
| `skill-add-api-endpoint.md` | Adding any new FastAPI route | Spec_Python_Code + ADR-001 + ADR-002 + JS contract rules |
| `skill-fix-js-bug.md` | Debugging a frontend defect | Spec_JS_Code + JS pitfall table + debug trace protocol |
| `skill-add-db-model.md` | New SQLAlchemy model + repo | Spec_DB + SqlRepository contract + migration commands |
| `skill-add-chat-intent.md` | New chat classifier intent | Spec_Chat_Feature + intent→handler pattern |
| `skill-end-of-day.md` | End-of-day routine | PM card all 4 steps inline |

### Layer 3 — Agent Prompt Templates (`project-office/agents/prompts/`)

Complete, ready-to-use agent() call prompts. User fills in `$TASK`, pastes rest.  
Eliminates re-explaining context per session for complex multi-agent tasks.

---

## Build Order

### Phase 1 — DONE
1. `.claude/commands/engineer-task.md`
2. `.claude/commands/start-day.md`
3. `.claude/commands/end-day.md`
4. `project-office/skills/skill-add-api-endpoint.md`

### Phase 2 — DONE
5. `project-office/skills/skill-fix-js-bug.md`
6. `project-office/skills/skill-add-db-model.md`
7. `.claude/commands/fix-bug.md`

### Phase 3 — DONE
8. `project-office/skills/skill-add-chat-intent.md`
9. `project-office/skills/skill-end-of-day.md`
10. `project-office/agents/prompts/prompt-engineer-task.md`
11. `project-office/agents/prompts/prompt-qa-sprint.md`
12. `project-office/agents/prompts/prompt-review.md`
13. `project-office/agents/prompts/prompt-techwriter-sprint.md`

---

## Skill File Template

Every skill file follows this structure:

```markdown
# Skill: <Task Name>

## When to use this skill
<1-2 sentences — the class of work this covers>

## Pre-conditions (check before starting)
- [ ] <what must be true before acting>

## Rules (inline — do not read spec files)
### Rule 1: <name>
<rule text — copy verbatim from spec, condensed>

## Step-by-step
1. <action>
2. <action>

## Files to touch
| File | Action |
|---|---|
| `path/to/file.py` | Create/Edit — <what to add> |

## Definition of Done
- [ ] <checklist item>
- [ ] Spec file updated if API contract changed
```

---

## Slash Command Template

Every command file follows this structure:

```markdown
---
description: <one line — shown in /help>
---

<System context (brief inline, not "read spec X")>

<Task: $ARGUMENTS>

<Exact steps to follow>

<Output: what to produce and where>
```

---

## Token Budget Impact (estimated)

| Session type | Before skills | After skills | Saving |
|---|---|---|---|
| Engineer (add endpoint) | ~22,000 | ~7,000 | ~68% |
| Engineer (fix JS bug) | ~18,000 | ~5,000 | ~72% |
| End of day | ~12,000 | ~4,000 | ~67% |
| Architect (new ADR) | ~25,000 | ~8,000 | ~68% |

---

## Maintenance Rule

When a spec file changes (new API contract, schema change, pattern update):
1. Update the relevant spec file (existing rule — Definition of Done)
2. **Also update the relevant skill file** — skills are derived from specs

Skill files go stale if only the spec is updated. Both must be updated in the same commit.
