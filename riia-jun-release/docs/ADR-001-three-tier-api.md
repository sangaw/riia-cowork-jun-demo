# ADR-001: Three-Tier API Design (Experience Layer / Business Process / System)

| Field | Value |
|---|---|
| **Status** | Accepted |
| **Date** | 2026-03-30 |
| **Sprint** | 0 |

---

## Context

The POC had a single monolithic `rest_api.py` (1,533 lines) that mixed three distinct concerns:

- **CRUD operations** on individual CSV tables (positions, orders, snapshots)
- **Business process logic** for long-running jobs (train, backtest, evaluate)
- **Aggregation** of multiple data sources into UI-ready payloads (dashboard, FnO view, ops view)

This violates the Single Responsibility Principle, makes unit testing impossible without loading the entire app, and creates merge conflicts whenever more than one engineer touches the API layer.

---

## Decision

Split all API routes into three tiers with strict rules about what each tier is allowed to do.

### Tier 1 — System (`api/v1/system/`)

Pure CRUD for individual CSV table resources. No business logic. Direct repository calls only.

| Router | Prefix | Responsibility |
|---|---|---|
| `PositionsRouter` | `/api/v1/system/positions/` | Create, read, update, delete position records |
| `OrdersRouter` | `/api/v1/system/orders/` | Create, read, update, delete order records |
| `SnapshotsRouter` | `/api/v1/system/snapshots/` | Create, read, update, delete snapshot records |

**Rule:** A System router may call **one repository** only. It must never call a service or another router.

### Tier 2 — Business Process (`api/v1/workflow/`)

Stateful workflows that orchestrate multiple services. Returns job status and results. These are long-running operations triggered by the user.

| Router | Prefix | Responsibility |
|---|---|---|
| `TrainRouter` | `/api/v1/workflow/train/` | Start, monitor, and retrieve DQN training runs |
| `BacktestRouter` | `/api/v1/workflow/backtest/` | Start, monitor, and retrieve backtest results |
| `EvaluateRouter` | `/api/v1/workflow/evaluate/` | Run model evaluation against live or historical data |

**Rule:** A Workflow router calls **services only** — never repositories directly, never Experience Layer routers.

### Tier 3 — Experience Layer (`api/experience/`)

Composes data from the System and Business Process tiers into a single, UI-optimised payload per view. Each router is shaped around what a specific screen needs — not around what the data model looks like. No business logic, no writes — composition only.

| Router | Prefix | Responsibility |
|---|---|---|
| `DashboardExperience` | `/api/experience/dashboard/` | RITA trading dashboard payload (positions + model state + alerts) |
| `FnoExperience` | `/api/experience/fno/` | FnO portfolio view payload (manoeuvres + Greeks + P&L) |
| `OpsExperience` | `/api/experience/ops/` | Ops dashboard payload (run history + metrics + health) |

**Rule:** An Experience Layer router calls **System routers or services** to compose responses. It must never write data or trigger side effects.

---

## Consequences

**Positive:**
- Each tier has a single responsibility — engineers can work independently without conflicts.
- Unit testing is clean: repositories and services are testable in isolation.
- The Experience Layer absorbs all N+1 query risk — the UI makes one call per view, not many.
- The workflow tier can be replaced with a task queue (Celery, ARQ) in v2 without touching the Experience Layer or System tiers.
- "Experience Layer" communicates intent clearly — these routes exist to serve a specific user experience, not to expose raw data.

**Negative:**
- More files and boilerplate than the POC monolith.
- Small features require touching multiple files (route + service + repository).

---

## Alternatives Considered

| Option | Reason Rejected |
|---|---|
| Keep single `rest_api.py` | Same monolith problem — untestable, merge-conflict prone |
| GraphQL | Team unfamiliar; resolver pattern adds complexity not justified for v1 |
| Microservices split | Premature — single deployable is correct for v1 CSV-backed system |
| Name tier 3 "BFF" (Backend For Frontend) | Jargon — unclear to anyone not familiar with the pattern; "Experience Layer" communicates purpose directly |
