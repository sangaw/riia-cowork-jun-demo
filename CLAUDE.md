# RITA Production Refactor — Project Guide for Claude

Auto-loaded every session. Navigation map only — rules live in `project-office/guardrails/`.

---

## Guardrails (load before acting)

| File | When to load |
|---|---|
| `project-office/guardrails/org.md` | Every session — universal rules |
| `project-office/guardrails/roles/<role>.md` | Match to your agent role |
| `project-office/guardrails/project.md` | Any task touching `riia-jun-release/` code |

Available roles: `engineer` · `architect` · `qa` · `pm` · `techwriter` · `reviewer`

---

## What This Project Is

**RITA** — Nifty 50 Double DQN RL trading system + FnO portfolio manager, POC → production refactor.

- **Daily status:** `PLAN_STATUS.md` — read this first every session
- **POC source:** `../poc/rita-cowork-demo` (local, not in repo)
- **Assessment:** `rita-cowork-demo/production_ready.md` — never read in full; use targeted excerpts only

---

## Agent Team

| Role | Invoke as | Scope |
|---|---|---|
| Project Manager | `general-purpose` | Reads PLAN_STATUS.md; outputs task list and risk updates |
| Architect | `Plan` agent | Reads targeted POC files + ADR excerpts; outputs design docs to `docs/` |
| Engineer | `general-purpose` + `isolation: "worktree"` | Reads scoped spec + source slice; writes code to `src/` |
| **Reviewer** | `general-purpose` | **Design Review (post-Architect) + Code Review (post-Engineer)** |
| QA Tester | `general-purpose` | Reads new code; writes tests to `tests/` |
| Ops Engineer | `general-purpose` | Reads pyproject.toml + config; writes Dockerfile, CI, k8s/ |
| Technical Writer | `general-purpose` | Reads sprint artifacts; publishes via `publish_confluence.py` |

Full agent cards: `project-office/agents/`  
Orchestration flow: `PM → Architect → [Design Review] → Engineer → [Code Review] → QA → TechWriter`

---

## Spec Files — Read Before Touching Code

All specs: `project-office/specs/` — read spec first, source file second.

| Spec | Read when... |
|---|---|
| `Spec_RITA_App.md` | General app overview, API inventory, key flows, agent panel |
| `Spec_Python_Code.md` | Any Python (routes, services, repos, core) |
| `Spec_DB.md` | Database, migrations, ORM models, repository classes |
| `Spec_Data.md` | Data files, data_loader, seeding, output paths |
| `Spec_JS_Code.md` | Any JS in `dashboard/js/` |
| `Spec_HTML_Code.md` | Any HTML in `dashboard/` |
| `Spec_Chat_Feature.md` | Chat pipeline, classifier, `/api/v1/chat` |
| `Spec-Agent-Workflow.md` | Agent intent coverage, agentic AI architecture |
| `Spec_Invest_Game.md` | Invest Game standalone page — `investgame.html`, agent chain, mock data |
| `Spec_Mobile_App.md` | PWA at `riia-jun-release/mobileapp/index.html` — served at `/mobileapp` |
| `Spec_MCP_Server.md` | MCP server, mcp_logger, `/api/v1/mcp-calls`, Claude Desktop config |
| `SPEC_Prod_Deploy.md` | Production deployment — two-repo setup, EC2, Docker, secrets, common failures |

---

## Workspace Structure

```
riia-cowork-jun/
├── CLAUDE.md                    ← this file (navigation only)
├── PLAN_STATUS.md               ← daily tracker
├── project-office/
│   ├── guardrails/              ← org.md + project.md + roles/
│   ├── agents/                  ← agent role cards
│   ├── skills/                  ← compiled task skill files (source of truth)
│   ├── specs/                   ← all Spec_*.md files
│   ├── features/                ← per-feature REQUIREMENTS + PLAN_STATUS + eng-context
│   ├── task-briefs/             ← /enhance run audit trail
│   ├── confluence/              ← ConfluenceClient + page scripts
│   ├── context/                 ← domain-notes, confluence-guide (load on demand)
│   ├── sprint-boards/           ← one script per sprint board
│   └── scripts/                 ← utility scripts
└── riia-jun-release/            ← RITA APPLICATION CODE
    ├── src/rita/
    │   ├── api/v1/system/       ← pure CRUD routers
    │   ├── api/v1/workflow/     ← business process routers
    │   ├── api/experience/      ← Experience Layer routers
    │   ├── services/            ← business logic
    │   ├── repositories/        ← data access (one class per table)
    │   ├── schemas/             ← Pydantic contracts
    │   └── core/                ← calculation/ML logic
    ├── config/{base,development,staging,production}.yaml
    ├── tests/{unit,integration,e2e}/
    ├── dashboard/js/{rita,fno,ops}/
    └── docs/                    ← ADRs (ADR-001 through ADR-005)
```

---

## Key Design Decisions

- **ADR-001:** Three-tier API — Experience Layer / Business Process / System CRUD
- **ADR-002:** Repository pattern — no direct DB/file I/O in routes or services
- **v1:** SQLite + SQLAlchemy 2.x ORM, stateless API, JWT-secured
- **v2:** PostgreSQL replaces SQLite via one config change — zero code changes

Full API routing rules: `project-office/guardrails/project.md §1`

---

## Daily Commands

| User says | Action |
|---|---|
| `Start Day N` | Read PLAN_STATUS.md → confirm tasks → launch agents |
| `End day` | Run `/end-day` skill — 5 mandatory steps including skill drift check |
| `What's next?` | Read PLAN_STATUS.md → report current day and tasks |
| `Show blockers` | Read PLAN_STATUS.md → list blocked items |
| `Fix defect: <description>` | 1. Identify affected layer (spec → source slice) → 2. Engineer agent with `isolation: "worktree"` → 3. QA agent for regression test → 4. Update PLAN_STATUS.md → 5. git commit |

---

## Context Detail Files (load on demand)

| File | Load when... |
|---|---|
| `project-office/context/confluence-guide.md` | Running any Confluence publish script |
| `project-office/context/domain-notes.md` | Touching `core/`, lot sizes, Greeks, or data paths |
| `project-office/context/codebase-constraints.md` | *(Deprecated — rules moved to `guardrails/roles/engineer.md` and `guardrails/project.md`)* |
