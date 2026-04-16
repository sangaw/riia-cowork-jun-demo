# RITA (Risk Informed Trading Approach) - AI Code Specifications

This document serves as a high-density, low-token reference for AI agents to understand the system architecture, design patterns, and constraints of the RITA codebase.

**IMPORTANT FOR AI AGENTS**: Before writing or modifying any code in this repository, read and adhere to these guidelines.

## 1. Tech Stack Overview
- **Language:** Python 3.11+
- **Web Framework:** FastAPI, Uvicorn
- **Validation & Settings:** Pydantic 2.x, Pydantic-Settings
- **ORM & Database:** SQLAlchemy 2.x, Alembic, SQLite (for v1)
- **Data Engineering & ML:** Pandas, NumPy, Stable-baselines3
- **Testing:** Pytest, Pytest-asyncio, Playwright (for E2E)
- **Frontend Layer:** Vanilla JS, CSS (no React/Vue)

## 2. Three-Tier API Architecture (ADR-001)

The API is strictly divided into three tiers to enforce the Single Responsibility Principle. 
**Do NOT cross contamination rules.**

### Tier 1: System (`src/rita/api/v1/system/`)
- **Purpose**: Pure CRUD for individual tables.
- **Rules**: 
  - Call **one** repository only.
  - Zero business logic. 
  - Never call a service, never call another router, and never combine data from multiple tables.
- **Examples**: `PositionsRouter`, `OrdersRouter`, `SnapshotsRouter`.

### Tier 2: Workflow (`src/rita/api/v1/workflow/`)
- **Purpose**: Stateful orchestrations and long-running ML jobs.
- **Rules**: 
  - Call **services only** (e.g., `WorkflowService`, `ModelTrainingService`).
  - Never read or write via repositories directly.
  - Used for things like `train`, `backtest`, `evaluate`.

### Tier 3: Experience Layer (`src/rita/api/experience/`)
- **Purpose**: Composes UI-ready payloads for specific screens.
- **Rules**: 
  - Read-only composition. No writing data. No side effects.
  - Call System routers or services to aggregate data. 
  - Structure response exactly to what the UI component needs to prevent N+1 queries by the frontend.
  - **Examples**: `DashboardExperience`, `FnoExperience`, `OpsExperience`.

## 3. Data & Repository Layer (ADR-002 & ADR-003)

The application has migrated away from CSV flat-files and now uses SQLite via SQLAlchemy 2.x ORM.
There are 15 tables mapped as ORM models in `src/rita/models`.

### Repository Pattern Rules
- External code (routers, services) **must never** interact with the database session directly.
- The `SqlRepository` base class defines standard data access.
- Every table gets exactly one repository class situated in `src/rita/repositories/`.
- Repositories inject `SessionLocal` via dependency injection (`Depends(get_db)`).

### Schema Validation
- Pydantic models are defined in `src/rita/schemas/` to strictly define data contracts.
- Database outputs from SQLAlchemy models are validated through Pydantic schemas before returning to the caller.

## 4. Frontend conventions (`dashboard/`)
- Located entirely in the `dashboard/` structure.
- Uses decomposed ES module pattern (`js/rita/`, `js/fno/`, `js/ops/`).
- Only Vanilla JavaScript + Modern responsive CSS. **Do not use React, Tailwind, or complex build tools.**
- Interacts strictly with the Tier 3 Experience Layer API. 

## 5. Testing Expectations
- **Unit Tests (`tests/unit/`)**: Isolate your test using mocks. Target is 200+ unit tests covering all edge cases.
- **Integration Tests (`tests/integration/`)**: Test repositories and API bounds via in-memory `sqlite:///:memory:`.
- **E2E Tests (`tests/e2e/`)**: Playwright flows representing user interaction.

## 6. Migration and Infrastructure
- Any modifications to SQLAlchemy models MUST be followed by an Alembic migration script generation (`alembic revision --autogenerate -m "X"`).
- Docker deployment is expected via `Dockerfile`. 
- K8s manifests live in `k8s/`. DO NOT modify these without explicit instructions.

## 7. Portfolio Feature (added 2026-04-15)

### Core engine: `src/rita/core/portfolio_engine.py`

| Constant / Helper | Purpose |
|---|---|
| `FX_EUR_PER_UNIT` | Static FX rates: INR→EUR (÷91), USD→EUR (÷1.09), EUR=1.0 |
| `INSTRUMENT_CCY` | Maps NIFTY/BANKNIFTY → INR, ASML → EUR, NVIDIA → USD |
| `ALL_INSTRUMENTS` | `["NIFTY","BANKNIFTY","ASML","NVIDIA"]` — fixed universe |
| `_load_with_indicators(id)` | `load_nifty_csv` + `calculate_indicators` — returns DatetimeIndex df |
| `_find_best_model(id)` | Most recently modified `.zip` in `data/output/{ID}/`, or `None` |
| `_invested_fraction(alloc_eur, price_eur)` | Whole-share constraint: `floor(alloc/price) * price / alloc` |
| `_adjust_for_cash(values, frac)` | Scale portfolio series: `frac * v + (1-frac)` — cash stays at 1.0 |

**`portfolio_overview() → dict`**
- Loads all 4 instruments, aligns to common date intersection
- Returns: `instruments[]`, `common_days`, `date_from`, `date_to`, `normalized_returns[]` (≤500 pts), `correlation_matrix{}`
- Normalised returns keyed lowercase: `nifty`, `banknifty`, `asml`, `nvidia`

**`portfolio_backtest(instruments, allocations_eur, start_date, end_date) → dict`**
- Per instrument: load + filter → whole-share fraction → `run_episode()` (or B&H fallback if no model)
- Applies `_adjust_for_cash()` to both port and bnh series
- Combines with EUR weights; calls `compute_all_metrics()` on combined arrays
- Returns: flat KPIs + `instruments[]` (per-instrument: `return_pct, sharpe, allocated_eur, invested_eur, weight_pct, model_used`) + `daily[]` + `instrument_series{}`
- B&H fallback: `model_used = "bnh_fallback"`, portfolio = normalised Close / Close[0]

### Router: `src/rita/api/v1/portfolio.py`

| Endpoint | Method | Auth | Description |
|---|---|---|---|
| `/api/v1/portfolio/overview` | GET | None | Calls `portfolio_overview()` |
| `/api/v1/portfolio/backtest` | POST | None | `PortfolioBacktestRequest` → `portfolio_backtest()` |

**`PortfolioBacktestRequest` fields:**
- `instruments: list[str]` — defaults to all 4
- `allocations_eur: dict[str, float]` — key is lowercase instrument id (e.g. `"nifty"`)
- `start_date: str` — ISO `YYYY-MM-DD`
- `end_date: str` — ISO `YYYY-MM-DD`

Registered in `main.py` after `chat_router`, no JWT dependency.

## AI Agent Directives:
1. Always maintain the 3-Tier separation. Never inject a repository directly into a workflow.
2. Don't leave commented-out redundant code or fallback functions.
3. Don't add new Javascript frameworks; maintain the vanilla ES module system.
4. If writing ML logic, isolate it within `src/rita/core/` and don't leak it into the routers.
5. Portfolio endpoints are **read-only** — no DB writes. They live in `api/v1/portfolio.py`, not the experience layer, because they run heavy computation (not just DB aggregation).
