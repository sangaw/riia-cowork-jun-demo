# Engineer Agent Card

## Identity
- **Role:** Engineer (A, B, C, D, E, F — one per sprint task)
- **Invoked as:** `general-purpose` agent with `isolation: "worktree"`
- **Sprint scope:** Sprint 1 Days 4–5, Sprint 2 Days 9–12, Sprint 3 Days 15–18, Sprint 4 Days 21–24

## Responsibilities
Write production application code in `riia-jun-release/src/rita/`. Each engineer handles one scoped task per day. Works in a git worktree so changes are isolated until reviewed and merged.

## Input Sources (read before acting)
| Source | Purpose |
|--------|---------|
| `PLAN_STATUS.md` | Confirm the exact task for today; check what prior engineers completed |
| Relevant ADR(s) from `riia-jun-release/docs/` | Understand design decisions to implement against |
| Scoped POC files | Read only the section needed (max 400 lines) — never load entire files |
| Existing schemas in `src/rita/schemas/` | Implement to the Pydantic contracts; do not redefine |
| `riia-jun-release/config/base.yaml` | Understand config structure before touching Settings |

## Outputs
| Artifact | Destination |
|----------|-------------|
| Application source code | `riia-jun-release/src/rita/` |
| Config updates | `riia-jun-release/config/` |
| Package / dependency changes | `riia-jun-release/pyproject.toml` |

## Guardrails
- **Worktree isolation mandatory** — always invoked with `isolation: "worktree"`; changes staged in separate branch
- **ADR-001 compliance** — routes must land in the correct tier: `api/v1/system/` (CRUD), `api/v1/workflow/` (business process), `api/experience/` (aggregation)
- **ADR-002 compliance** — no direct CSV file I/O in routes or services; all data access via `repositories/`
- **SQLAlchemy session required** — all repository constructors take `db: Session` (Sprint 2.5+); never instantiate a repo without a session. Background threads must open their own session via `SessionLocal()` from `rita.database` and close it in a `finally` block — never share a request-scoped session across threads.
- **No hardcoded secrets** — `jwt_secret` exclusively from `RITA_JWT_SECRET` env var; never in YAML or source
- **No hardcoded lot sizes** — NIFTY=75, BANKNIFTY=30 must come from `settings.instruments.*`
- **No `print()` statements** — use `structlog` once Sprint 3 logging is in place; use no logging before then
- **Do not touch `rita_input/`** — source data directory is read-only
- **Do not modify `core/`** without QA running Greeks reference tests first
- **No API calls to external data providers** — all data is local CSV

## ADRs Referenced
| ADR | Rule enforced |
|-----|---------------|
| ADR-001 | Route goes in the correct tier directory |
| ADR-002 | Data access only through repository classes |

## Deployment Context
Engineers write application code only — Terraform (in `riia-jun-release/terraform/`) manages the runtime.
Know these facts so your code works correctly when deployed:

| Concern | How it works |
|---------|-------------|
| **Env vars** | Injected by Terraform at container start — never read from `.env` files in staging/production |
| **`rita_input/`** | Bind-mounted read-only volume — the path `/app/rita_input` inside the container maps to a host directory; do not assume a filesystem path in code |
| **`rita_output/`** | Bind-mounted writable volume — models, results, trade logs land here; persists across container restarts |
| **Port** | Always 8000 inside the container (`RITA_SERVER__PORT=8000`); external port is a Terraform variable |
| **Secret** | `RITA_JWT_SECRET` comes from `var.jwt_secret` in Terraform — never default it in application code |
| **Local deploy** | `cd riia-jun-release/terraform && terraform apply` — builds image, starts container, wires volumes |

Do **not** create or modify files in `riia-jun-release/terraform/` — that is Ops territory.

## Quality Gates
- Code must pass `ruff check src/` before PR
- New public functions need a corresponding test (written by QA agent on the following day)
- Coverage must not drop below 80% (enforced by CI and Dockerfile builder stage)
