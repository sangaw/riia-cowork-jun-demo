---
description: Read PLAN_STATUS.md and report today's tasks, status, and blockers
---

Read `PLAN_STATUS.md` (the full file — it is the single source of truth for sprint progress).

Report the following in a concise table:
1. Current day number and sprint
2. Today's tasks — each with role, description, and status ([x] done / [ ] pending)
3. Any blockers listed
4. Overall project completion %

Then identify, for each pending task, which skill file maps to it:

| Task type | Skill file to use |
|---|---|
| Add/modify a FastAPI endpoint | `project-office/skills/skill-add-api-endpoint.md` |
| Fix a frontend JS bug | `project-office/skills/skill-fix-js-bug.md` |
| Add a DB model or repository | `project-office/skills/skill-add-db-model.md` |
| Add a chat intent | `project-office/skills/skill-add-chat-intent.md` |
| End-of-day routine | Use `/end-day` command |

Finally ask: "Which task should I start?" — do not start any work until the user confirms.
