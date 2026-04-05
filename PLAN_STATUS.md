# RITA Production Refactor — Daily Status
**Last updated:** 2026-04-05 (Day 24)

---

## Current Sprint: SPRINT 3 — Service Layer & Observability
**Current Day: Day 24 complete — SPRINT 3 DONE. Sprint 4 Day 25 next.**

---

## Sprint 0 Tasks

| Day | Role | Task | Status | Notes |
|---|---|---|---|---|
| Day 1 | PM + Architect | Target folder structure; ADR-001, ADR-002 | `[x]` | Structure created, ADRs written to docs/ |
| Day 2 | Architect | Pydantic schemas for all 15 CSV tables | `[x]` | 16 schema files written to src/rita/schemas/ — derived from actual POC CSV headers |
| Day 3 | TechWriter | Bootstrap Confluence: Architecture section, ADR pages, Sprint board | `[x]` | ADR-001 [65568776] and ADR-002 [65536002] published to Architecture section |

## Sprint 1 Tasks

| Day | Role | Task | Status | Notes |
|---|---|---|---|---|
| Day 4 | Engineer A | Pydantic Settings, config YAML hierarchy, remove hardcoded secrets | `[x]` | config.py, pyproject.toml, .env.example written; jwt_secret removed from YAML |
| Day 5 | Engineer B | Repository layer — CSV tables, file locking, schema validation | `[x]` | CsvRepository base + 15 concrete classes; per-instance lock; validation on read+write |
| Day 6 | Ops | Multi-stage Dockerfile, CI v2 pipeline | `[x]` | Multi-stage Dockerfile (builder lints+tests, runtime non-root); CI: lint→test→docker-build |
| Day 7 | QA | Config + repository tests | `[x]` | 8 config tests + 11 repo tests (incl. concurrency); coverage threshold raised to 80% |
| Day 8 | TechWriter | Confluence: Security & Config pages | `[x]` | Config Guide [65863699] + Security page [65994769] published under Engineering section |

## Sprint 2 Tasks

| Day | Role | Task | Status | Notes |
|---|---|---|---|---|
| Day 9 | Engineer C | System APIs (CRUD routers) | `[x]` | 8 CRUD routers (positions, orders, snapshots, trades, alerts, audit, market_data, config_overrides); wired into main.py |
| Day 10 | Engineer C | Business Process API routers | `[x]` | WorkflowService (train) + BacktestService (backtest/evaluate); 3 routers wired into main.py; services create status=pending records; ML dispatch is Sprint 3 |
| Day 11 | Engineer C | BFF layer | `[x]` | 3 Experience Layer routers: DashboardPayload (positions+model state+alerts), FnoPayload (snapshots+portfolio+manoeuvres), OpsPayload (training+backtest runs+audit); wired into main.py |
| Day 12 | Engineer C | Global exception handler, trace IDs | `[x]` | TraceIDMiddleware (X-Request-ID header, ContextVar); 4 exception handlers (HTTPException, RequestValidationError, RepositoryValidationError, Exception→500); consistent {detail, trace_id} JSON shape |
| Day 13 | QA | API contract tests | `[x]` | 78 tests: 30 system CRUD, 18 workflow, 15 experience, 15 middleware; 100% pass; 1 pre-existing config test failure flagged |
| Day 14 | TechWriter | Confluence: API Reference | `[x]` | Sprint 2 API Reference [66650113] + Master Plan overview updated; all 3 tiers documented |

## Sprint 2.5 Tasks — Database Layer (SQLite + SQLAlchemy)

> **Decision (2026-04-02):** Replace CSV backend with SQLite via SQLAlchemy 2.x ORM.
> ADR-003 written. Zero changes to routers, services, or schemas — repository layer only.
> PostgreSQL upgrade in v2: change one `database_url` config value.

| Day | Role | Task | Status | Notes |
|---|---|---|---|---|
| Day 15 | Engineer D | SQLAlchemy setup: database.py, 15 ORM models, config.py DB settings, ADR-003 to Confluence | `[x]` | pyproject.toml: sqlalchemy>=2.0, alembic>=1.13; database.py: engine + SessionLocal + Base + get_db(); 15 model files (17 classes); DatabaseSettings in config.py; ADR-003 published [66650129] |
| Day 16 | Engineer D | Repository migration: rewrite base.py (SqlRepository), update all 15 concrete repos, update main.py lifespan | `[x]` | SqlRepository[T,M] added to base.py; 15 repos + new risk.py migrate to SQLAlchemy; services (workflow, backtest) take db: Session; all 14 routers inject get_db(); main.py lifespan creates tables on startup; 78/78 API tests pass |
| Day 17 | Ops | Alembic setup + CI update | `[x]` | alembic init; env.py imports Base + all 17 models, resolves SQLite path to absolute; 16 CREATE TABLE migration verified (upgrade head + downgrade base); CI: alembic upgrade head step added before pytest; Dockerfile: copies alembic/, CMD runs migrations before uvicorn |
| Day 18 | QA | Test suite migration | `[x]` | conftest.py: db_session fixture (sqlite:///:memory:, function-scoped) + client fixture overriding get_db; test_repository.py rewritten for SqlRepository; 96/97 tests pass (1 pre-existing TestJwtSecretFromEnvVar failure); 78 API contract tests confirmed passing |

## Sprint 3 Tasks — Service Layer & Observability

| Day | Role | Task | Status | Notes |
|---|---|---|---|---|
| Day 19 | Engineer D | WorkflowService, BacktestService (real ML dispatch stubs) | `[x]` | core/ml_dispatch.py + core/backtest_dispatch.py; daemon threads via SessionLocal; pending→running→complete/failed; 96/97 tests pass |
| Day 20 | Engineer D | ManoeuvreService, PortfolioService | `[x]` | ManoeuvreService (record/list_all/list_recent/list_by_date) + PortfolioService (record/list_all/get_by_date/get_latest); fno.py ADR-001 fixed to inject services; 96/97 tests pass |
| Day 21 | Engineer E | structlog JSON logging throughout | `[x]` | logging_config.py; middleware binds trace_id; exception handlers log errors; WorkflowService + BacktestService log job transitions; 96/97 tests pass |
| Day 22 | Engineer E | Prometheus metrics, /health, /readyz | `[x]` | prometheus-fastapi-instrumentator>=6.1; metrics.py with instrument_app(); /health liveness (no DB); /readyz readiness (SELECT 1, 503 on failure); 11 pre-existing ruff warnings fixed; 96/97 tests pass |
| Day 23 | QA | Greeks tests, manoeuvre tests, workflow integration | `[x]` | test_greeks.py (8 B-S reference tests, math only); test_services.py (6 manoeuvre + 4 portfolio); test_workflow_integration.py (6 incl. daemon thread e2e); 120/121 pass |
| Day 24 | TechWriter | Confluence: Observability & Runbook | `[x]` | Observability & Runbook published to operations section [67895297]; structlog format, health probes table, Prometheus metrics, 4 runbook scenarios, k8s probe YAML |

## Sprint 4 Tasks — Frontend & Responsive Design

| Day | Role | Task | Status | Notes |
|---|---|---|---|---|
| Day 25 | Engineer F | Decompose rita.html → ES modules | `[ ]` | |
| Day 26 | Engineer F | Decompose fno.html, ops.html → ES modules | `[ ]` | |
| Day 27 | Engineer F | Responsive CSS (480/768/1100px) | `[ ]` | |
| Day 28 | Engineer F | Remove localhost:8000 hardcoding | `[ ]` | |
| Day 29 | QA | Playwright e2e tests | `[ ]` | |
| Day 30 | TechWriter | Confluence: Frontend Architecture | `[ ]` | |

## Sprint 5 Tasks — Integration, Security & Release

| Day | Role | Task | Status | Notes |
|---|---|---|---|---|
| Day 31 | QA | Full end-to-end regression + coverage report | `[ ]` | |
| Day 32 | Security | CORS, JWT, rate limiting, input validation | `[ ]` | |
| Day 33 | Ops | Terraform: k8s manifests, AlertManager, cloud provider swap | `[ ]` | Local Docker deployment scaffolded (terraform/ dir); Day 33 extends to cloud |
| Day 34 | PM + TechWriter | Release checklist, v1.0 tag, release notes | `[ ]` | |

---

## Blockers

_None_

## Notes / Decisions

- 2026-03-30: Plan created.
- 2026-03-30: Sprint 0 complete (Days 1-3). ADR-001, ADR-002, 16 Pydantic schemas, full folder structure. ADR pages live on Confluence. Config YAML hierarchy created. Git repo initialised, remote pointed to github.com/sangaw/riia-cowork-jun-demo.git — not yet pushed.
- 2026-03-31: Terraform deployment scaffolded. Local deployment uses kreuzwerker/docker provider. Files in riia-jun-release/terraform/. rita_input/ read-only, rita_output/ writable. Sprint 5 Day 33 scoped for cloud.
- 2026-04-02: Sprint 2.5 added — SQLite via SQLAlchemy 2.x replaces CSV backend. ADR-003 written to docs/. Repository interface unchanged; zero impact on routers/services/schemas. Project extends to 34 days total. PostgreSQL upgrade path: change database_url in v2.
