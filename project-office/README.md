# project-office

All Claude Cowork management code for the RITA production refactor project.
This folder is NOT part of the RITA application — it contains the tooling that
runs the project: sprint tracking, Confluence publishing, and cowork scripts.

## Structure

```
project-office/
├── confluence/          # Confluence publishing scripts
│   ├── publish.py       # Core publisher utility (reusable)
│   └── pages/           # One script per Confluence section
├── sprint-boards/       # Sprint board Confluence pages (published per sprint)
└── scripts/             # Utility scripts (JIRA, reporting, etc.)
```

## Key files at project root (not in this folder)
- `CLAUDE.md`        — Auto-loaded by Claude Code; project context for all agents
- `PLAN_STATUS.md`   — Daily status tracker; read by PM agent each session
