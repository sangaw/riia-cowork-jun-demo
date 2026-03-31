# Agent Reference Cards

One file per role. Each card covers: responsibilities, input sources, outputs, guardrails, ADRs referenced, and quality gates.

| Agent | File | Invoked as | Sprint days |
|-------|------|-----------|-------------|
| Project Manager | [project-manager.md](project-manager.md) | `general-purpose` | Day 1, Day 30, every end-of-day |
| Architect | [architect.md](architect.md) | `Plan` agent | Days 1–2 (Sprint 0) |
| Engineer | [engineer.md](engineer.md) | `general-purpose` + `isolation: "worktree"` | Days 4–5, 9–12, 15–18, 21–24 |
| QA Tester | [qa.md](qa.md) | `general-purpose` | Days 7, 13, 19, 25, 27 |
| Ops Engineer | [ops.md](ops.md) | `general-purpose` | Days 6, 29 |
| Technical Writer | [techwriter.md](techwriter.md) | `general-purpose` | Days 3, 8, 14, 20, 26, 30 |
| Code Reviewer | [reviewer.md](reviewer.md) | `general-purpose` | On-demand |
