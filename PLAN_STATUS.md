# RITA Production Refactor — Daily Status
**Last updated:** 2026-03-31

---

## Current Sprint: SPRINT 0 — Architecture & Planning
**Current Day: Day 4** (Sprint 1 begins)

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
| Day 5 | Engineer B | Repository layer — CSV tables, file locking, schema validation | `[ ]` | |
| Day 6 | Ops | Multi-stage Dockerfile, CI v2 pipeline | `[ ]` | |
| Day 7 | QA | Config + repository tests | `[ ]` | |
| Day 8 | TechWriter | Confluence: Security & Config pages | `[ ]` | |

## Sprint 2 Tasks

| Day | Role | Task | Status | Notes |
|---|---|---|---|---|
| Day 9 | Engineer C | System APIs (CRUD routers) | `[ ]` | |
| Day 10 | Engineer C | Business Process API routers | `[ ]` | |
| Day 11 | Engineer C | BFF layer | `[ ]` | |
| Day 12 | Engineer C | Global exception handler, trace IDs | `[ ]` | |
| Day 13 | QA | API contract tests | `[ ]` | |
| Day 14 | TechWriter | Confluence: API Reference | `[ ]` | |

## Sprint 3 Tasks

| Day | Role | Task | Status | Notes |
|---|---|---|---|---|
| Day 15 | Engineer D | WorkflowService, BacktestService | `[ ]` | |
| Day 16 | Engineer D | ManoeuvreService, PortfolioService | `[ ]` | |
| Day 17 | Engineer E | structlog JSON logging throughout | `[ ]` | |
| Day 18 | Engineer E | Prometheus metrics, /health, /readyz | `[ ]` | |
| Day 19 | QA | Greeks tests, manoeuvre tests, workflow integration | `[ ]` | |
| Day 20 | TechWriter | Confluence: Observability & Runbook | `[ ]` | |

## Sprint 4 Tasks

| Day | Role | Task | Status | Notes |
|---|---|---|---|---|
| Day 21 | Engineer F | Decompose rita.html → ES modules | `[ ]` | |
| Day 22 | Engineer F | Decompose fno.html, ops.html → ES modules | `[ ]` | |
| Day 23 | Engineer F | Responsive CSS (480/768/1100px) | `[ ]` | |
| Day 24 | Engineer F | Remove localhost:8000 hardcoding | `[ ]` | |
| Day 25 | QA | Playwright e2e tests | `[ ]` | |
| Day 26 | TechWriter | Confluence: Frontend Architecture | `[ ]` | |

## Sprint 5 Tasks

| Day | Role | Task | Status | Notes |
|---|---|---|---|---|
| Day 27 | QA | Full end-to-end regression + coverage report | `[ ]` | |
| Day 28 | Security | CORS, JWT, rate limiting, input validation | `[ ]` | |
| Day 29 | Ops | k8s manifests, AlertManager, canary rollout | `[ ]` | |
| Day 30 | PM + TechWriter | Release checklist, v1.0 tag, release notes | `[ ]` | |

---

## Blockers

_None_

## Notes / Decisions

- 2026-03-30: Plan created. Master plan at RITA_PRODUCTION_PLAN.md.
- 2026-03-30: Sprint 0 complete (Days 1-3). ADR-001, ADR-002, 16 Pydantic schemas, full folder structure. ADR pages live on Confluence under Architecture section. Folder structure created under riia-jun-release/. ADR-001 (three-tier API) and ADR-002 (repository pattern) written to docs/. Config YAML hierarchy (base/dev/staging/prod) created. Git repo initialised, .gitignore set, remote pointed to github.com/sangaw/riia-cowork-jun-demo.git — not yet pushed.
