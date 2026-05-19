# RITA Production Refactor — Project Guide for Claude

Auto-loaded every session. Navigation map only — detail lives in `project-office/context/`.

---

## What This Project Is

**RITA** — Nifty 50 Double DQN RL trading system + FnO portfolio manager, POC → production refactor.

- **Daily status:** `PLAN_STATUS.md` — read this first every session
- **POC source:** `../poc/rita-cowork-demo` (local, not in repo)
- **Assessment:** `rita-cowork-demo/production_ready.md` — never read in full; use targeted excerpts only

## Agent Team

| Role | Invoke as | Scope |
|---|---|---|
| Project Manager | `general-purpose` | Reads PLAN_STATUS.md; outputs task list and risk updates |
| Architect | `Plan` agent | Reads targeted POC files + ADR excerpts; outputs design docs to `docs/` |
| Engineer | `general-purpose` + `isolation: "worktree"` | Reads scoped spec + source slice; writes code to `src/` |
| QA Tester | `general-purpose` | Reads new code; writes tests to `tests/` |
| Ops Engineer | `general-purpose` | Reads pyproject.toml + config; writes Dockerfile, CI, k8s/ |
| Technical Writer | `general-purpose` | Reads sprint artifacts; publishes via `publish_confluence.py` |

Full agent cards: `project-office/agents/`

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
| `Spec_Mobile_App.md` | PWA at `riia-jun-release/mobileapp/index.html` — served at `/mobileapp` |
| `Spec_MCP_Server.md` | MCP server, mcp_logger, `/api/v1/mcp-calls`, Claude Desktop config |
| `SPEC_Prod_Deploy.md` | Production deployment — two-repo setup, EC2, Docker, secrets, common failures |

**Definition of Done:** Any change to an API contract, data schema, or architectural pattern must update the relevant spec in the same commit.

## Token Efficiency Rules

1. Read spec files first, source files second.
2. Read large files in slices — max 400 lines. (`rest_api.py` = 1,533 | `rita.html` = 4,000 | `fno.html` = 3,500)
3. Read `PLAN_STATUS.md` first — don't re-explore what's already tracked.
4. Engineer agents use `isolation: "worktree"` for all code-writing tasks.
5. Max 4 agent invocations per session (80% Claude Pro quota).

## Workspace Structure

```
riia-cowork-jun/
├── CLAUDE.md                    ← this file
├── PLAN_STATUS.md               ← daily tracker
├── project-office/
│   ├── agents/                  ← agent role cards
│   ├── confluence/              ← ConfluenceClient + page scripts
│   ├── context/                 ← detail files (constraints, confluence, domain)
│   ├── specs/                   ← all Spec_*.md files (moved here 2026-04-29)
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

- Engineer agents: all app code → `riia-jun-release/`
- TechWriter/PM/Ops agents: all management scripts → `project-office/`

## Key Design Decisions

- **ADR-001:** Three-tier API — Experience Layer / Business Process / System CRUD
- **ADR-002:** Repository pattern — no direct DB/file I/O in routes or services
- **v1:** SQLite + SQLAlchemy 2.x ORM, stateless API, JWT-secured
- **v2:** PostgreSQL replaces SQLite via one config change — zero code changes

## API Tier Routing Rules (Enforced)

Dashboard JS **must only call** Experience or Workflow tier endpoints. Calling system-tier routes directly from JS is a compliance violation (Feature 08).

| | Path pattern | Notes |
|---|---|---|
| ✅ Allowed | `/api/v1/experience/*` | Experience tier — all dashboards |
| ✅ Allowed | `/api/experience/*` | Experience tier (ops prefix variant) |
| ✅ Allowed | `/api/v1/portfolio/*` | Portfolio / FnO tier |
| ✅ Allowed | `/api/v1/chat*`, `/api/v1/commentary`, `/api/v1/instrument/*` | Workflow/chat operations |
| ✅ Allowed | `/api/v1/train`, `/api/v1/backtest`, `/api/v1/pipeline`, `/api/v1/goal`, `/api/v1/market`, `/api/v1/strategy` | Pipeline workflow operations |
| ✅ Allowed | `/api/v1/agent-panel/*`, `/api/v1/mcp-calls` | Agent/MCP read |
| ✅ Allowed | `/health`, `/progress`, `/reset` | App-root routes |
| ✅ Allowed | `/api/v1/market-signals`, `/api/v1/shap` | Raw indicators/ML artifacts — no experience wrapper needed |
| ❌ Never | `/api/v1/backtest-daily` | System tier — use `/api/v1/experience/rita/backtest-daily` |
| ❌ Never | `/api/v1/risk-timeline` | System tier — use `/api/v1/experience/rita/risk-timeline` |
| ❌ Never | `/api/v1/training-history` | System tier — use `/api/v1/experience/rita/training-history` |

**When adding a new JS module:**
1. Check if the data is already available via an experience endpoint
2. If not, create the experience endpoint first (in `src/rita/api/experience/`)
3. Never call system tier (`/api/v1/system/` or raw CRUD routes) directly from dashboard JS

Full audit: `project-office/features/08 API Layer Rationalization/REQUIREMENTS.md`

---

## Daily Commands

| User says | Action |
|---|---|
| `Start Day N` | Read PLAN_STATUS.md → confirm tasks → launch agents |
| `End day` | 1. Update PLAN_STATUS.md → 2. Update `project-office/program-roadmap.html` → 3. Run sprint board Confluence script → 4. git commit |
| `What's next?` | Read PLAN_STATUS.md → report current day and tasks |
| `Show blockers` | Read PLAN_STATUS.md → list blocked items |

## Context Detail Files (load on demand)

| File | Load when... |
|---|---|
| `project-office/context/codebase-constraints.md` | Writing any new service, router, or repository |
| `project-office/context/confluence-guide.md` | Running any Confluence publish script |
| `project-office/context/domain-notes.md` | Touching `core/`, lot sizes, Greeks, or data paths |

## What NOT to Do

- Do not read `rita.html`, `fno.html`, or `riia-jun-release/mobileapp/index.html` directly — use specs
- Do not delete or overwrite files in `rita_input/`
- Do not modify `core/` without QA running Greeks reference tests first
- Do not commit `confluence-api-key.txt` or `.env` files
- Do not add `print()` statements — use `structlog`
- Do not call external data providers — all data is local CSV
- Do not change an API contract, schema, or data layout without updating the spec in the same commit
