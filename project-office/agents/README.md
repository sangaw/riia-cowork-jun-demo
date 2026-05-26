# Agent Reference Cards

One file per role. Each card covers: responsibilities, input sources, outputs, guardrails, ADRs referenced, and quality gates.

| Agent | File | Invoked as | When |
|-------|------|-----------|------|
| Project Manager | [project-manager.md](project-manager.md) | `general-purpose` | Day 1, Day 30, every end-of-day |
| Architect | [architect.md](architect.md) | `Plan` agent | Sprint Day 1–2; `/enhance` Step 3 |
| Engineer | [engineer.md](engineer.md) | `general-purpose` + `isolation: "worktree"` | Sprint Days 4–5, 9–12, 15–18, 21–24; `/enhance` Step 4 |
| **Reviewer** | **[reviewer.md](reviewer.md)** | `general-purpose` | **`/enhance` Step 3.5 (Design Review) + Step 4.5 (Code Review)** |
| QA Tester | [qa.md](qa.md) | `general-purpose` | Sprint Days 7, 13, 19, 25, 27; `/enhance` Step 5 |
| Ops Engineer | [ops.md](ops.md) | `general-purpose` | Days 6, 29 |
| Technical Writer | [techwriter.md](techwriter.md) | `general-purpose` | Days 3, 8, 14, 20, 26, 30; `/enhance` Step 6 |

## Orchestration Flow (Feature 18 onward)

```
PM → Architect → [Design Review] → Engineer → [Code Review] → QA → TechWriter
         ↑ re-invoke on FAIL ↓         ↑ re-invoke on FAIL ↓
```

- **Design Review** gate: Reviewer reads requirements + Architect design. Blocks Engineer if design does not fully address requirements or has incomplete API/frontend contract.
- **Code Review** gate: Reviewer reads design + changed code. Blocks QA if implementation deviates from design or violates engineer guardrails.
- **QA** is unchanged — tests, coverage, end-to-end functional verification.
- Both review gates write their own section to the task brief. Re-invoke ceiling: 1 automatic re-invoke; escalate to user on second FAIL.
