# RITA Production Refactor — Master Plan
**Version:** 1.0 | **Created:** 2026-03-30

---

## Overview

Refactor RITA (Risk Informed Trading Approach) from POC to production-grade release.

| Item | Detail |
|---|---|
| **Source (POC)** | `../poc/rita-cowork-demo` (local — not in this repo) |
| **Target (Prod)** | `.` (this repo) |
| **Assessment** | `rita-cowork-demo/production_ready.md` (v2.0, 29-Mar-2026) |
| **Documentation** | https://ravionics.atlassian.net/wiki/spaces/RIIAProjec/overview |
| **Approach** | Claude Cowork — daily plan → execute → update cycle |

---

## Team Roles (Claude Cowork Agents)

| Role | Agent | Responsibility |
|---|---|---|
| **Project Manager (PM)** | `general-purpose` | Sprint planning, daily work breakdown, risk tracking, status updates |
| **Architect** | `Plan` | Target design, ADRs, module contracts, Pydantic schemas |
| **Engineer** | `general-purpose` (×N, isolated worktrees) | Code implementation, split by domain |
| **QA Tester** | `general-purpose` | Unit tests, integration tests, coverage reports |
| **Ops Engineer** | `general-purpose` | Dockerfile, CI/CD, k8s manifests, secrets config |
| **Technical Writer** | `general-purpose` | Documentation authored in Markdown, published to Confluence |

---

## Token Budget Strategy (Claude Pro)

Claude Pro has per-session and daily usage limits. Each day follows this discipline:

### Daily Work Cycle
```
START OF DAY
  1. Review PLAN_STATUS.md (1 read — minimal tokens)
  2. Pick today's tasks from the day plan
  3. Launch agents sequentially or in targeted parallel pairs
     — NOT all agents at once (token spike)
  4. Each agent reads ONLY its scoped files (no full-codebase reads)

END OF DAY
  5. Update PLAN_STATUS.md with completed/blocked items
  6. Technical Writer agent drafts Confluence page for the day's output
  7. Publish to Confluence
```

### Token-Efficient Agent Rules
- **No agent reads production_ready.md in full** — it was pre-digested; agents receive only the relevant section (passed as a quoted excerpt in the prompt).
- **Large files (rest_api.py 1,533 ln, rita.html 4,000 ln) are read in slices** — each engineer agent reads only the section it will modify.
- **Worktree isolation** — parallel engineers work on isolated git branches; no merge conflicts mid-session.
- **Architect artifacts are written to files** — subsequent agents read the file, not re-derive the design.
- **One agent chain per session** — aim for 3-5 focused agent invocations per day, not 10+.

### Estimated Token Budget per Day
| Activity | Approx. Agents | Notes |
|---|---|---|
| Planning day | 1 (PM) | Light — reads status, outputs task list |
| Architecture day | 1 (Architect) + 1 (TechWriter) | Medium — design work |
| Engineering day | 2-3 (Engineers, isolated) | Heavy — read+write code |
| QA day | 1-2 (QA) | Medium — read code, write tests |
| Ops day | 1 (Ops) | Medium — config files |
| Doc day | 1 (TechWriter) | Light — read artifacts, write Confluence |

---

## Sprint Plan (5 Sprints × ~3-5 Work Days Each)

---

### SPRINT 0 — Architecture & Planning
**Goal:** Target structure defined, ADRs written, work tickets created, Confluence space bootstrapped.
**Token profile:** Light-medium. Architect reads small scoped files, not large monoliths.

| Day | Who | Task | Output |
|---|---|---|---|
| **Day 1** | PM + Architect | Sprint plan finalised; target `src/` folder structure designed | `PLAN_STATUS.md`, `docs/ADR-001-api-tiers.md`, `docs/ADR-002-repository-pattern.md` |
| **Day 2** | Architect | Pydantic schemas for all 15 CSV tables; dependency injection contracts | `src/rita/schemas/` (one file per domain) |
| **Day 3** | TechWriter | Bootstrap Confluence space: Home, Architecture page, Sprint board | Confluence pages published |

**Done when:** ADRs approved, schemas written, Confluence has home + architecture overview.

---

### SPRINT 1 — Foundation (Config, Security, Data Layer, Ops)
**Goal:** The three pillars that everything else depends on: validated config, repository pattern, CI/CD.
**Token profile:** Medium. Engineers read targeted sections only.

| Day | Who | Task | Output |
|---|---|---|---|
| **Day 4** | Engineer A | Pydantic `Settings`, `config/` YAML hierarchy, remove hardcoded secrets from HTML | `src/rita/config.py`, `config/*.yaml`, updated `dashboard/*.html` |
| **Day 5** | Engineer B | Repository layer — one class per CSV table, file locking, schema validation on read/write | `src/rita/repositories/` (12 files) |
| **Day 6** | Ops | Multi-stage Dockerfile, CI v2 (lint → type-check → pytest+coverage ≥80% → build), `.env.example` update | `Dockerfile`, `.github/workflows/ci.yml`, `.env.example` |
| **Day 7** | QA | Tests for config validation edge cases + repository read/write round-trips | `tests/test_config.py`, `tests/test_repositories.py` |
| **Day 8** | TechWriter | Document: Config guide, Repository contracts, Security setup | Confluence: Security & Config pages |

**Done when:** Config validated at startup, all CSV access via repositories, CI runs and enforces coverage gate.

---

### SPRINT 2 — API Decomposition
**Goal:** Break the 1,533-line monolith into three tiers. Add global error handling + trace IDs.
**Token profile:** Heavy (large file). Read rest_api.py in sections across multiple days.

| Day | Who | Task | Output |
|---|---|---|---|
| **Day 9** | Engineer C | Extract System APIs (pure CRUD): positions, orders, scenario_levels, snapshots | `src/rita/api/v1/system/` routers |
| **Day 10** | Engineer C | Extract Business Process APIs: workflow, backtest, training, model_registry | `src/rita/api/v1/workflow/` routers |
| **Day 11** | Engineer C | Build BFF layer: dashboard_bff, fno_bff, ops_bff aggregation endpoints | `src/rita/api/bff/` routers |
| **Day 12** | Engineer C | Global exception handler, trace IDs, structured error responses, NaN safety | `src/rita/api/middleware.py` |
| **Day 13** | QA | API contract tests for all tiers using `httpx.AsyncClient` | `tests/api/` |
| **Day 14** | TechWriter | Document: API reference (all endpoints), error codes, trace ID guide | Confluence: API Reference pages |

**Done when:** `rest_api.py` replaced by router modules, all endpoints tested, no silent failures.

---

### SPRINT 3 — Service Layer & Observability
**Goal:** Business logic extracted from routes into services. Logging and metrics wired up.
**Token profile:** Medium. Services are new files; reads are targeted.

| Day | Who | Task | Output |
|---|---|---|---|
| **Day 15** | Engineer D | `WorkflowService`, `BacktestService` — extract from workflow/api routes | `src/rita/services/workflow.py`, `backtest.py` |
| **Day 16** | Engineer D | `ManoeuvreService`, `PortfolioService` — extract from FnO routes | `src/rita/services/manoeuvre.py`, `portfolio.py` |
| **Day 17** | Engineer E | Replace all `print()` with `structlog` JSON logging; add correlation IDs | All `src/rita/` modules updated |
| **Day 18** | Engineer E | Prometheus metrics (request latency, snapshot counter, training events), `/health` + `/readyz` endpoints | `src/rita/api/v1/system/health.py`, `src/rita/observability/metrics.py` |
| **Day 19** | QA | Core tests: Greeks vs Black-Scholes reference, manoeuvre snapshot round-trip, workflow integration | `tests/test_greeks.py`, `tests/test_manoeuvre.py`, `tests/test_workflow_integration.py` |
| **Day 20** | TechWriter | Document: Service layer guide, observability runbook, alerting rules | Confluence: Observability & Runbook pages |

**Done when:** All business logic in services, structured logs in JSON, Prometheus metrics exported.

---

### SPRINT 4 — Frontend Decomposition & Responsive Design
**Goal:** Break 4,000-line HTML monoliths into ES modules. Mobile/tablet responsive support.
**Token profile:** Heavy (large HTML files). Read in sections.

| Day | Who | Task | Output |
|---|---|---|---|
| **Day 21** | Engineer F | Decompose `rita.html` → `dashboard/js/rita/` ES modules (one file per section) | `dashboard/js/rita/*.js` |
| **Day 22** | Engineer F | Decompose `fno.html` → `dashboard/js/fno/` ES modules; `ops.html` → `dashboard/js/ops/` | `dashboard/js/fno/*.js`, `dashboard/js/ops/*.js` |
| **Day 23** | Engineer F | Responsive CSS: 480px/768px/1100px breakpoints, sidebar overlay, bottom tab bar for mobile | `dashboard/css/responsive.css`, updated HTML |
| **Day 24** | Engineer F | Remove `localhost:8000` hardcoding; inject `window.RITA_API_BASE` from config | All dashboard HTML/JS |
| **Day 25** | QA | Playwright smoke tests: load dashboard, trigger API, chart renders at 3 breakpoints | `tests/e2e/` |
| **Day 26** | TechWriter | Document: Frontend architecture, component guide, responsive design system | Confluence: Frontend pages |

**Done when:** No monolithic HTML files, responsive on mobile/tablet, no hardcoded URLs.

---

### SPRINT 5 — Integration, Security Audit & Release
**Goal:** Full regression, security hardening, k8s manifests, production release.
**Token profile:** Medium. Mostly review and targeted fixes.

| Day | Who | Task | Output |
|---|---|---|---|
| **Day 27** | QA | Full end-to-end test: load → train → backtest → FnO positions → snapshot; coverage report | `tests/e2e/test_full_workflow.py`, coverage HTML |
| **Day 28** | Security (Engineer) | CORS lockdown, JWT auth + refresh, rate limiting (slowapi), input validation audit | `src/rita/api/middleware/security.py` |
| **Day 29** | Ops | k8s manifests: Deployment, Service, Ingress, HPA, PVC; AlertManager rules; canary rollout | `k8s/` directory |
| **Day 30** | PM + TechWriter | Final release checklist, version tag, Confluence: Release Notes + Operations Manual | `CHANGELOG.md`, Confluence: Release v1.0 |

**Done when:** Coverage ≥80%, security audit passed, k8s manifests valid, release notes published.

---

## Status Tracking

**File:** `PLAN_STATUS.md` (updated at end of each work day)

Fields per task: `[ ]` todo / `[~]` in-progress / `[x]` done / `[!]` blocked

---

## Confluence Documentation Plan

| Page | Sprint | Author Agent | Content |
|---|---|---|---|
| **Home / Overview** | S0 | TechWriter | Project goal, team, links to all pages |
| **Architecture Overview** | S0 | TechWriter | Three-tier diagram, ADR summaries |
| **ADR-001: API Tiers** | S0 | TechWriter | Decision record: BFF/BP/System design |
| **ADR-002: Repository Pattern** | S0 | TechWriter | Decision record: CSV v1 / DB v2 strategy |
| **Data Schema Reference** | S0 | TechWriter | All 15 CSV table schemas with field types |
| **Security & Config Guide** | S1 | TechWriter | JWT setup, Pydantic Settings, secrets |
| **Repository Contracts** | S1 | TechWriter | Repository API, file locking, validation |
| **API Reference** | S2 | TechWriter | All endpoints (System / BP / BFF), errors |
| **Service Layer Guide** | S3 | TechWriter | Services, dependency injection, flow |
| **Observability Runbook** | S3 | TechWriter | Logs, metrics, alerts, dashboards |
| **Frontend Architecture** | S4 | TechWriter | Module map, responsive breakpoints |
| **Test Strategy** | S4 | TechWriter | Pyramid, coverage targets, how to run |
| **Operations Manual** | S5 | TechWriter | k8s deployment, rollback, monitoring |
| **Release Notes v1.0** | S5 | TechWriter | What changed, migration notes |

---

## Risk Register

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | Token budget exhausted mid-sprint on large files | High | Medium | Read files in slices; agents scoped to specific sections |
| R2 | Parallel engineers create merge conflicts | Medium | High | Worktree isolation per agent; merge only at end of day |
| R3 | Greeks calculation regressions during refactor | Medium | Critical | QA writes reference tests before engineers touch core/ |
| R4 | Confluence API auth fails | Low | Low | TechWriter drafts locally first; publish manually if needed |
| R5 | CSV race conditions surface in prod | Medium | High | Repository file locking (Sprint 1, Day 5) — highest priority fix |

---

## How Each Day Starts

At the start of each session, say:
> **"Start Day N"** — I will read `PLAN_STATUS.md`, confirm today's tasks, and launch the right agents.

Or:
> **"What's next?"** — I'll check status and tell you exactly what Day we're on and what to do.

---

*This plan is a living document. Updated daily via `PLAN_STATUS.md`.*
