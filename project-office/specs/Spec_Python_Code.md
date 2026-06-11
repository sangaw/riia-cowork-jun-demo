# RITA (Risk Informed Trading Approach) — Python Code Specification

High-density reference for AI agents. Read before writing or modifying any Python in this repository.

**IMPORTANT FOR AI AGENTS**: Before writing or modifying any code, read and adhere to these guidelines.

---

## 1. Tech Stack

| Tool | Version | Purpose |
|---|---|---|
| Python | 3.11+ | Runtime |
| FastAPI | latest | Web framework |
| Uvicorn | latest | ASGI server |
| Pydantic 2.x | | Validation + Settings |
| Pydantic-Settings | | Environment config |
| SQLAlchemy 2.x | | ORM |
| Alembic | 1.13+ | Migrations |
| SQLite | | v1 DB (swap to PostgreSQL in v2 via `database_url`) |
| Pandas, NumPy | | Data engineering |
| Stable-baselines3 | | DoubleDQN RL |
| LangGraph | | Multi-agent workflow (agent_panel.py) |
| structlog | | JSON structured logging |
| prometheus-fastapi-instrumentator | 6.1+ | Metrics |
| pytest, pytest-asyncio | | Testing |
| sentence-transformers | | Local intent classifier |
| python-jose | | JWT |
| slowapi | | Rate limiting |

---

## 2. Three-Tier API Architecture (ADR-001)

### Tier 1: System (`src/rita/api/v1/system/`)

Pure CRUD — **one repository per router, zero business logic, no cross-table reads**.

| File | Router prefix | Key endpoints |
|---|---|---|
| `positions.py` | `/api/v1/positions` | GET list, POST create, GET/{id}, PUT/{id}, DELETE/{id} |
| `orders.py` | `/api/v1/orders` | CRUD |
| `snapshots.py` | `/api/v1/snapshots` | CRUD |
| `trades.py` | `/api/v1/trades` | CRUD |
| `alerts.py` | `/api/v1/alerts` | CRUD |
| `audit.py` | `/api/v1/audit` | GET list, POST create |
| `market_data.py` | `/api/v1/market-data` | CRUD |
| `config_overrides.py` | `/api/v1/config-overrides` | CRUD |
| `instruments.py` | `/api/v1/instruments` | GET list, GET/{id}, PUT/{id} — instrument registry |
| `market_signals.py` | `/api/v1/market-signals` | `GET ?timeframe=daily\|weekly\|monthly&periods=N&instrument=X` — computes RSI/MACD/BB/ATR/EMA from `market_data_cache` |
| `training_runs.py` | `/api/v1/training-history`, `/api/v1/split-dates`, `/api/v1/backtest-status/{id}`, `/api/v1/training-metrics?instrument=` | Training run records + split date computation. `/api/v1/training-metrics` returns per-episode TD loss + reward for the latest training run from the `training_metrics` DB table (added `761e8ba`). |
| `drift.py` | `/api/v1/drift` | `GET` → `DriftDetector.run()` → `{summary, checks}` |
| `data_prep.py` | `/api/v1/data-prep/status`, `/api/v1/test-results`, `/api/v1/shap-values`, `/api/v1/data-understanding` | File system checks, JUnit XML parsing, SHAP values |

### Tier 2: Workflow (`src/rita/api/v1/workflow/`)

Stateful orchestration — **calls services only, JWT-protected (except pipeline.py and chat.py)**.

| File | Endpoints | Auth |
|---|---|---|
| `train.py` | `POST /api/v1/train` | JWT |
| `backtest.py` | `POST /api/v1/backtest` | JWT |
| `evaluate.py` | `POST /api/v1/evaluate` | JWT |
| `pipeline.py` | `POST /api/v1/instrument/select`, `GET /api/v1/pipeline/progress`, `POST /api/v1/pipeline/quick-backtest` | No JWT |
| `instrument_onboard.py` | `GET /api/v1/instrument/search`, `POST /api/v1/instrument/onboard` | No JWT |
| `chat.py` | `POST /api/v1/chat`, `POST /api/v1/chat/warmup` | No JWT |

### Tier 3: Experience Layer (`src/rita/api/experience/`)

Read-only aggregation — **no writes, no side effects, no DB commits**.

| File | Prefix | Endpoints |
|---|---|---|
| `dashboard.py` | `/api/experience` | `GET /rita` (DashboardPayload), `GET /fno` (FnoPayload), `GET /ops` (OpsPayload) — legacy |
| `fno.py` | `/api/experience/fno` | `GET /` → FnO aggregated payload (snapshots + portfolio + manoeuvres) |
| `portfolio_hedge.py` | `/api/v1/experience/fno` | `GET /portfolio-hedge?coverage=0-100&duration=1m\|3m\|1y` — per-holding Black-Scholes put + call pricing. Returns `PortfolioHedgeResponse`: `holdings[]` with `ann_vol_pct`, `cost_pct` (put premium), `call_sell_cost_pct` (call income), `strike_pct`, `strike_label`, `protected_pct`, `risk_score`, `duration`; plus `aggregate` (monthly_cost_pct, max_dd_protected_pct, max_dd_unhedged_pct) and `coverage`. JWT-required. `HoldingItem` dicts from `sa.JSON` column are parsed via `HoldingItem(**h) if isinstance(h, dict)` before attribute access. |
| `hedge_plan.py` | `/api/v1/experience/fno` | `GET /hedge-plan` — returns `HedgePlanOut` for authenticated user (404 if no plan). `PUT /hedge-plan` — upsert body `{hedged_ids: list[str], coverage: int, scenario_tab: str}`; `duration` always written as `"1y"`. Both JWT-required. Uses `UserHedgePlanRepo`. Added F29 Phase 1. |
| `portfolio_analytics.py` | `/api/v1/experience/fno` | `GET /portfolio-analytics?mode=real\|mock` — unified FnO dashboard analytics payload. Returns `PortfolioAnalyticsResponse` with: `portfolio_meta`, `market` (per-instrument OHLCV), `positions[]`, `greeks[]` (per-holding BS greeks), `net_greeks`, `net_delta`, `scenario_levels` (σ-anchored target/sl), `payoff` (21-pt portfolio+hedged grid), `stress[]` (5 hardcoded events), `hedge_quality` (HQS per instrument), `closed_positions=[]`, `realized_pnl=0`, `margin={}`. mode=mock: no auth, returns MOCK_PORTFOLIO constant. mode=real: JWT required via `get_optional_user()`; 401 without token, 404 if no portfolio. Greeks reuse BS formulas from portfolio_hedge.py. Added F30 Phase 1. |
| `ops.py` | `/api/experience/ops` | `GET /` (OpsPayload), `GET /metrics/summary`, `GET /step-log`, `GET /users`, `POST /users`, `DELETE /users/{id}` |
| `rita.py` | `/api/v1` | See Section 6 below |
| `pipeline_wizard.py` | `/api/v1` | `POST /goal`, `POST /market`, `POST /strategy` |
| `ds.py` | `/api/experience/ds` | `GET /` → instruments + training history + split dates |
| `agent_panel.py` | `/api/v1/agent-panel` | `POST /run-day`, `GET /plot/{day_index}` |

### Other (`src/rita/api/v1/`)

| File | Endpoints |
|---|---|
| `auth.py` | `POST /auth/token` — issues JWT (rate-limited 10/min). When the `username` matches an existing `users` row (e.g. the shared demo account `webmaster@ravionics.nl`), it also records login activity: updates `last_login_date`/`first_login_date` and inserts a `LoginEventModel`, mirroring the Google OAuth callback. Unknown subjects (e.g. `rita-dev`) still receive a token but are not persisted. |
| `users.py` | `GET /api/v1/users`, `POST /api/v1/users` |
| `portfolio.py` | See Section 7 below |

---

## 3. Repository Pattern (ADR-002 & ADR-003)

### Base class: `SqlRepository[T, M]` (`src/rita/repositories/base.py`)

```python
class SqlRepository(Generic[T, M]):
    def __init__(self, db: Session) -> None: ...
    def read_all(self) -> list[T]: ...
    def find_by_id(self, id: str) -> T | None: ...
    def upsert(self, obj: T) -> T: ...         # calls db.commit() internally
    def delete(self, id: str) -> bool: ...
```

**Critical rule:** `upsert()` calls `db.commit()` — **never commit again after calling upsert**.

### Concrete repositories

| File | Class | Table | Notes |
|---|---|---|---|
| `repositories/positions.py` | `PositionsRepository` | `positions` | |
| `repositories/orders.py` | `OrdersRepository` | `orders` | |
| `repositories/snapshots.py` | `SnapshotsRepository` | `snapshots` | |
| `repositories/trades.py` | `TradesRepository` | `trades` | |
| `repositories/alerts.py` | `AlertsRepository` | `alerts` | |
| `repositories/audit.py` | `AuditLogRepository` | `audit_log` | |
| `repositories/market_data.py` | `MarketDataCacheRepository` | `market_data_cache` | |
| `repositories/config_overrides.py` | `ConfigOverridesRepository` | `config_overrides` | |
| `repositories/instrument.py` | `InstrumentRepository` | `instruments` | |
| `repositories/training.py` | `TrainingRunsRepository` | `training_runs` | |
| `repositories/backtest.py` | `BacktestRunsRepository`, `BacktestResultsRepository` | `backtest_runs`, `backtest_results` | |
| `repositories/risk.py` | `RiskTimelineRepository` | `risk_timeline` | |
| `repositories/manoeuvres.py` | `ManoeuvresRepository` | `manoeuvres` | |
| `repositories/portfolio.py` | `PortfolioRepository` | `portfolio` | |
| `repositories/model_registry.py` | `ModelRegistryRepository` | `model_registry` | |
| `repositories/paper_positions.py` | `PaperPositionsRepository` | `paper_positions` | Paper/simulation positions |

### FastAPI dependency injection pattern

```python
from rita.database import get_db

def get_my_service(db: Session = Depends(get_db)) -> MyService:
    return MyService(db)

@router.get("/endpoint")
def endpoint(svc: MyService = Depends(get_my_service)) -> dict:
    return svc.do_something()
```

### Background thread pattern

```python
from rita.database import SessionLocal

def _background_worker(run_id: str) -> None:
    db = SessionLocal()
    try:
        repo = MyRepository(db)
        # ... work ...
    finally:
        db.close()
```

---

## 4. ORM Models (`src/rita/models/`)

| File | Class | Key columns |
|---|---|---|
| `instrument.py` | `InstrumentModel` | `instrument_id (PK)`, `name`, `exchange`, `country_code`, `lot_size`, `is_available` |
| `market_data.py` | `MarketDataCacheModel` | `cache_id (PK)`, `date`, `underlying`, `open/high/low/close`, `shares_traded`, `recorded_at` |
| `paper_positions.py` | `PaperPositionModel` | `position_id (PK)`, `instrument`, `underlying`, `product`, `option_type`, `strike`, `expiry`, `quantity`, `avg_price`, `last_traded_price`, `pnl`, `pct_change`, `currency`, `lot_size`, `sl_price`, `target_price`, `entry_date`, `expiry_date`, `recorded_at` |
| `training.py` | `TrainingRunModel` | `run_id (PK)`, `status`, `instrument`, `model_version`, `algorithm`, `timesteps`, `train_sharpe/mdd/return/trades`, `val_sharpe/mdd/return/cagr/trades`, `backtest_sharpe/mdd/return/cagr/trades/constraints_met`, `recorded_at`, `ended_at` |
| `backtest.py` | `BacktestRunModel`, `BacktestResultModel` | Run: `run_id, instrument, start_date, end_date, strategy params, total_trades, status`. Result: `result_id, run_id, date, portfolio_value, benchmark_value, allocation, close_price, sharpe_ratio, max_drawdown` |
| `risk.py` | `RiskTimelineModel` | Composite PK, day-by-day allocation + drawdown + regime |
| `positions.py` | `PositionModel` | FnO broker positions |
| `orders.py` | `OrderModel` | Intraday orders |
| `manoeuvres.py` | `ManoeuvreModel` | `id, date, timestamp, action, lot_key, from_group, to_group, nifty_spot, ...` |
| `portfolio.py` | `PortfolioModel` | `id, date, group_name, group_id, underlying, view, lot_count, pnl_now, sl_pnl, target_pnl, nifty_spot, banknifty_spot` |
| `config_overrides.py` | `ConfigOverrideModel` | `key (PK), value` |
| `audit.py` | `AuditLogModel` | `id, timestamp, endpoint, method, status_code, trace_id` |
| `alerts.py` | `AlertModel` | Chat/query confidence log |
| `user.py` | `UserModel` | `user_id, username, email, hashed_password, is_active, is_admin, created_at` |
| `model_registry.py` | `ModelRegistryModel` | Model version tracking |

---

## 5. Schemas (`src/rita/schemas/`)

All schemas are Pydantic 2.x models. Each ORM model has a corresponding schema.

| Schema file | Key classes |
|---|---|
| `instrument.py` | `Instrument` |
| `market_data.py` | `MarketDataCache` |
| `paper_positions.py` | `PaperPosition` |
| `training.py` | `TrainingRun` |
| `backtest.py` | `BacktestRun`, `BacktestResult` |
| `risk.py` | `RiskTimeline` |
| `positions.py` | `Position` |
| `orders.py` | `Order` |
| `manoeuvres.py` | `Manoeuvre` |
| `portfolio.py` | `Portfolio` |
| `snapshots.py` | `Snapshot` |
| `trades.py` | `Trade` |
| `config_overrides.py` | `ConfigOverride` |
| `audit.py` | `AuditLog` |
| `alerts.py` | `Alert` |
| `model_registry.py` | `ModelRegistry` |
| `geography.py` | `GeoInstrument` (close, daily_return_pct, signal, return_1y_pct, return_5y_pct, return_15y_pct, risk_score, sector, horizons[]), `GeoRegion`, `GeographyOverviewResponse` |
| `user_portfolio.py` | `HoldingItem` (`instrument_id`, `allocation_pct` [required, >0], `shares: int\|None` [optional — whole-share count], `cash_eur: float\|None` [optional — leftover cash after buying whole shares]); `UserPortfolioCreate` (`name`, `holdings: list[HoldingItem]`, `total_value_eur?`); `UserPortfolioOut` (adds `portfolio_id`, `key_id`, `created_at`, `updated_at`, `is_active`). `shares` and `cash_eur` stored in the `sa.JSON` holdings column alongside `allocation_pct` — no migration needed. |

---

## 6. Experience Layer — `rita.py` Endpoints

**Prefix:** `/api/v1`

| Endpoint | Method | Key logic |
|---|---|---|
| `/instrument/active` | GET | Reads `active_instrument_id` from `config_overrides`; returns `{id, name, flag, exchange, lot_size}` |
| `/performance-summary` | GET | Latest backtest KPIs for active instrument. Returns `_run_instrument_id` and `_active_instrument_id` for stale-check. |
| `/backtest-daily` | GET | Daily portfolio/benchmark/allocation series for latest completed backtest of active instrument |
| `/performance-feedback` | GET | Calls `build_performance_feedback(backtest_df, perf_metrics, training_rounds)` |
| `/portfolio-comparison` | GET | Calls `build_portfolio_comparison(backtest_df, portfolio_inr)` |
| `/risk-timeline?phase=all&instrument=NIFTY` | GET | Per-day risk stats: drawdown, rolling vol, VaR 95, regime, trend_score |
| `/trade-events` | GET | Entry/exit events derived from allocation changes (threshold 0.05) — includes sharpe_at_trade, delta_var |
| `/stress-scenarios` | GET | Calls `simulate_stress_scenarios(portfolio_inr, [-20,-10,-5,5,10,20], rita_allocation_pct)` |

**`_get_active_instrument_id(db)`** — shared helper in both `rita.py` and `pipeline_wizard.py`:
```python
def _get_active_instrument_id(db: Session) -> str:
    cfg = ConfigOverridesRepository(db).find_by_id("active_instrument_id")
    return cfg.value.upper() if cfg and cfg.value else "NIFTY"
```

---

## 7. Portfolio Router — `api/v1/portfolio.py`

**Prefix:** `/api/v1/portfolio`

| Endpoint | Method | Key logic |
|---|---|---|
| `/overview` | GET | `portfolio_overview()` — loads all 4 instruments, aligns to common date intersection, returns normalised returns + correlation matrix |
| `/backtest` | POST | `PortfolioBacktestRequest` → `portfolio_backtest(instruments, allocations_eur, start_date, end_date)` |
| `/positions?mode=paper\|live` | GET | paper → `PaperPositionsRepository`; live → `PositionsRepository`. Returns `_position_to_row()` shaped list |
| `/summary` | GET | `PortfolioService.list_all()` + `MarketDataCacheRepository` → total_pnl, lot_count, spot prices, OHLCV `market` dict for all 4 instruments |
| `/price-history?periods=N` | GET | Last N NIFTY OHLCV records from `market_data_cache` |
| `/hedge-history` | GET | `ManoeuvreService.list_all()` filtered to hedge actions |
| `/man-groups` | GET | Aggregates portfolio records by group_name |
| `/man-snapshot` | POST | No-op with 200 OK (records snapshot intent) |
| `/man-pnl-history` | GET | `PortfolioService.list_all()` sorted by date |
| `/man-daily-status` | GET | Today's manoeuvre count + last manoeuvre record |
| `/man-daily-snapshot` | POST | No-op with 200 OK |

**`_position_to_row(r)`** — transforms Position/PaperPosition ORM row into JS-ready dict with `{instrument, full, und, exp, type, strike, side, qty, avg, ltp, chg, pnl, currency, lot_size, sl_price, target_price, entry_date, expiry_date}`.

---

## 8. Pipeline Wizard — `experience/pipeline_wizard.py`

**Prefix:** `/api/v1`

| Endpoint | Method | Request | Key logic |
|---|---|---|---|
| `/goal` | POST | `GoalRequest{target_return_pct, time_horizon_days, risk_tolerance}` | Computes feasibility (conservative/realistic/ambitious/unrealistic), yearly NIFTY returns, last 12m return |
| `/market` | POST | none | Calls `_compute_market_signals(db, instrument, "daily", 252)` → enriches latest bar with trend/RSI/MACD/BB labels |
| `/strategy` | POST | none | Returns algorithm config: DoubleDQN, timesteps, learning_rate, batch_size, gamma |

**`_compute_market_signals(db, instrument, timeframe, periods)`** — internal helper that:
1. Reads from `market_data_cache` (or falls back to CSV)
2. Resamples to weekly/monthly if needed
3. Computes RSI-14, MACD(12,26,9), BB(20,2σ), ATR-14, EMA-5/13/26/50, trend_score
4. Returns last `periods` bars

---

## 9. Agent Panel — `experience/agent_panel.py`

See `Spec_RITA_App.md` Section 9 for full AgentState and node details.

**LangGraph setup:**
```python
_workflow = StateGraph(AgentState)
_workflow.add_node("context", context_agent)
# ... 5 more nodes
_memory = MemorySaver()
_graph = _workflow.compile(checkpointer=_memory)
```

**Session state management (server-side):**
```python
SESSION_DATA: dict[str, dict] = {}  # thread_id → {cash, holdings, portfolio_value}
```
- Initialised to `{cash: 5000.0, holdings: 0.0, portfolio_value: 5000.0}` on day 0 or new thread
- Updated after each LangGraph invocation

**Data source:** ASML April 2026 data loaded eagerly at module import from `data/raw/ASML/asml_2001-2026.csv`

---

## 10. Core Engine — `src/rita/core/`

### `investment_horizons.py`

Configuration module for investment horizon screening thresholds. Edit this file to recalibrate rules without touching application code.

```python
INVESTMENT_HORIZONS: dict[str, dict]
# Keys: "short_term" | "medium_term" | "long_term"
# Each entry: label, description, return_field, min_return_pct, lookback_td, years
```

Keys are sent verbatim in `GeoInstrument.horizons[]` — keep them stable identifiers. Consumed by `geography_overview()` in `experience/rita.py` to compute `return_5y_pct`, `return_15y_pct` (CAGR) and classify each instrument into matching horizon buckets.

---

### `data_loader.py`

**Feature 09:** `load_nifty_csv` renamed to `load_ohlcv_csv` (instrument-agnostic).
Backward-compat alias `load_nifty_csv = load_ohlcv_csv` retained in the same file.

```python
def load_ohlcv_csv(path: str) -> pd.DataFrame:
    """Returns DatetimeIndex df with columns: Open, High, Low, Close, Volume.
    Handles: IST timezone-aware dates, plain ISO, dd-MMM-yyyy formats.
    (Previously named load_nifty_csv — alias retained for compatibility.)"""

load_nifty_csv = load_ohlcv_csv  # backward-compat alias

def load_instrument_data(instrument: str) -> pd.DataFrame:
    """Load full OHLCV history for an instrument, merging three sources:
    1. Primary CSV via find_instrument_csv(instrument)
    2. Manual supplement: data/input/DAILY-DATA/{lower}_manual.csv (if exists)
    3. yfinance companion: data/raw/{INSTRUMENT}/{lower}_yf.csv (if exists — Feature 16)
    Deduplicates with keep='last' at each merge step. Returns date-sorted DataFrame."""
```

### `trading_env.py`

```python
class RITAEnv(gym.Env):
    """DoubleDQN trading environment. Actions: 0=sell, 1=hold, 2=buy."""

def train_best_of_n(env, n_seeds: int = 3) -> DoubleDQN:
    """Train n models with different seeds, return the one with best backtest Sharpe."""
```

### `ml_dispatch.py`

```python
def _run_training(run_id: str, instrument: str, n_seeds: int = 3) -> None:
    """Daemon thread function. Full cycle:
    1. Create TrainingRun record (pending → running)
    2. load_instrument_data(instrument)
    3. train_best_of_n(env, n_seeds) → saves .zip to models/{instrument}/
    4. TrainingTracker writes training_history.csv
    5. Update TrainingRun with all phase metrics (train/val/backtest Sharpe, MDD, return)
    6. status = complete | failed
    """
```

### `backtest_dispatch.py`

```python
def run_episode(model: DoubleDQN, df: pd.DataFrame) -> tuple[list, list]:
    """Real backtest engine (not a stub). Returns (portfolio_values, benchmark_values)."""
```

### `training_tracker.py`

```python
class TrainingTracker:
    def __init__(self, run_id: str, instrument: str): ...
    def record_step(self, timestep: int, reward: float, loss: float): ...
    def flush(self): ...  # writes training_history.csv
```

### `performance.py`

```python
def compute_all_metrics(port_values: list, bench_values: list, risk_free: float = 0.0) -> dict:
    """Returns: sharpe, sortino, calmar, max_drawdown, cagr, win_rate, total_days"""

def build_performance_feedback(backtest_df: pd.DataFrame, perf_metrics: dict, training_rounds: int) -> dict:
    """Structured feedback card: stage (Early|Developing|Consistent|Strong), guidance list, constraint checklist"""

def build_portfolio_comparison(backtest_df: pd.DataFrame, portfolio_inr: float) -> dict:
    """Compare RITA vs Conservative (20% eq)/Moderate (50% eq)/Aggressive (80% eq) profiles"""

def simulate_stress_scenarios(portfolio_inr: float, market_moves: list[int], rita_allocation_pct: float) -> dict:
    """Point-in-time stress test. Returns scenario rows: {move_pct, portfolio_pnl, mdd_breach, profiles}"""
```

### `portfolio_engine.py`

```python
FX_EUR_PER_UNIT = {"INR": 1/91, "USD": 1/1.09, "EUR": 1.0}
INSTRUMENT_CCY  = {"NIFTY": "INR", "BANKNIFTY": "INR", "ASML": "EUR", "NVIDIA": "USD"}
ALL_INSTRUMENTS = ["NIFTY", "BANKNIFTY", "ASML", "NVIDIA"]

def portfolio_overview() -> dict:
    """Loads all 4 instruments, aligns to common date intersection.
    Returns: instruments[], common_days, date_from, date_to,
             normalised_returns{nifty,banknifty,asml,nvidia} (≤500 pts),
             correlation_matrix{}"""

def portfolio_backtest(instruments, allocations_eur, start_date, end_date) -> dict:
    """Per instrument: load → filter → whole-share fraction → run_episode() (or B&H fallback).
    Combines with EUR weights; calls compute_all_metrics().
    Returns: flat KPIs + instruments[] + daily[] + instrument_series{}"""
```

### `drift_detector.py`

```python
class DriftDetector:
    """5 DB-backed checks: data_freshness, model_age, sharpe_trend, backtest_count, db_connectivity"""
    def run(self, db: Session) -> dict:
        """Returns: {summary: {overall: "ok"|"warn"|"err"}, checks: {name: {status, message}}}"""
```

### `classifier.py`

```python
# 20 intents grouped into:
# return_Xm/Xy (return estimation), market_sentiment, trend_direction,
# rsi_reading, volatility_check, invest_now, allocation_level,
# conservative_strategy, aggressive_strategy,
# stress_crash_10/20, stress_rally_10, stress_flat,
# backtest_performance, portfolio_compare, explain_decision

def classify_intent(query: str) -> tuple[str, float]:
    """Returns (intent_name, confidence). SentenceTransformer, cosine similarity."""

def dispatch(intent: str, confidence: float, db: Session) -> dict:
    """Routes to handler based on intent. Returns structured response."""
```

---

## 10b. Services (`src/rita/services/`)

Business logic layer called by workflow routers. Do not call repositories directly from routers — use services.

| File | Functions | Purpose |
|---|---|---|
| `workflow_service.py` | `get_live_progress()` | Training progress polling |
| `backtest_service.py` | `run_backtest()` | Single-instrument DDQN backtest |
| `portfolio_service.py` | `compute_portfolio_summary()` | Cross-instrument portfolio KPIs |
| `manoeuvre_service.py` | `evaluate_manoeuvres()` | FnO manoeuvre P&L computation |
| `instrument_onboard.py` | `search_tickers()`, `fetch_raw_data()`, `process_to_input()`, `seed_market_cache()` | Feature 09 — yfinance data fetch, normalize, DB seeding for new instruments |
| `data_refresh.py` | `check_gap()`, `fetch_and_write_raw()`, `rebuild_input()`, `upsert_cache_delta()`, `refresh_all()` | Feature 16 — delta data refresh for all instruments via yfinance. Skips ATHER. Per-instrument errors do not abort the loop. `upsert_cache_delta` uses `db.add_all()` with explicit date-existence check — no `db.merge()`, no DELETE. |

### `instrument_onboard.py` (Feature 09)

```python
def search_tickers(query: str, max_results: int = 10) -> list[dict]:
    """Search Yahoo Finance for EQUITY listings. Raises HTTPException(502) if unreachable."""

def fetch_raw_data(ticker: str) -> tuple[Path, int]:
    """Download from yfinance (2009-09-01), write data/raw/{TICKER}/{ticker_lower}_daily.csv.
    Raises ValueError if < 100 rows. Returns (raw_path, row_count)."""

def process_to_input(ticker: str, raw_path: Path) -> Path:
    """Normalize raw CSV → Open/High/Low/Close/Volume, filter year >= 2010, tz-naive.
    Writes data/input/{TICKER}/{ticker_lower}_daily.csv. Returns input_path."""

def seed_market_cache(db: Session, ticker: str, currency: str) -> int:
    """Bulk insert 2025+ rows into market_data_cache. Skips if already seeded.
    Returns count inserted (0 if skipped)."""
```

### `data_refresh.py` (Feature 16)

**File:** `src/rita/services/data_refresh.py`

**Constants:**
- `YF_TICKER_MAP` — maps instrument ID to yfinance ticker (11 instruments)
- `COMPANION_FILE_INSTRUMENTS` — `{"NIFTY", "BANKNIFTY"}` — full-overwrite _yf.csv strategy
- `SKIP_INSTRUMENTS` — `{"ATHER"}` — excluded from all refresh runs

**Functions:**
- `check_gap(instrument_id, db) -> dict` — returns last_date, gap_days, yf_ticker from market_data_cache
- `fetch_and_write_raw(instrument_id, yf_ticker, last_date) -> tuple[Path, int]` — downloads delta from yfinance; NIFTY/BANKNIFTY overwrite companion _yf.csv; others append to _daily.csv
- `rebuild_input(instrument_id) -> Path` — calls load_instrument_data(), writes normalized output CSV
- `upsert_cache_delta(db, instrument_id) -> int` — inserts only new (instrument, date) pairs into market_data_cache; no deletes
- `refresh_all(db) -> list[dict]` — orchestrates full pipeline for all instruments; per-instrument errors caught, loop continues

**Endpoint:** `POST /api/v1/instrument/refresh-all` → returns `RefreshAllResponse`
**Slash command:** `/refresh-all-instruments-data`
**Standalone script:** `project-office/scripts/run_data_refresh.py`

---

## 11. Config (`src/rita/config.py`)

Uses `pydantic-settings` with YAML hierarchy: `config/base.yaml` → `config/{env}.yaml` → env vars.

Key settings:
- `settings.app.name`, `settings.app.version`
- `settings.database.database_url` → `"sqlite:///./rita_output/rita.db"`
- `settings.security.cors_origins`, `settings.security.jwt_secret`
- `settings.data.input_dir`, `settings.data.output_dir`
- `settings.model.path`
- `settings.instruments.nifty.lot_size` (default 75), `settings.instruments.banknifty.lot_size` (default 30)

**Never hardcode lot sizes** — always read from `get_settings().instruments`.

---

## 12. Database Setup (`src/rita/database.py`)

```python
engine = create_engine(settings.database.database_url, ...)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency. Yields a session; closes on exit."""
```

---

## 13. Startup Seeding (`src/rita/main.py` `lifespan()`)

On every startup (idempotent — skip if table already populated):

1. `Base.metadata.create_all(bind=engine)` — creates new tables
2. **Column migrations** — `ALTER TABLE ... ADD COLUMN ...` for new columns (swallows error if already exists)
3. **Instruments seed** — 4 rows: NIFTY (lot 75), BANKNIFTY (lot 30), NVIDIA, ASML; one-time rename NVDA→NVIDIA
4. **Market data seed** — all 4 instruments, year 2025+2026, `db.add_all()` bulk insert (< 2 sec each)
5. **Paper positions seed** — 2 ASML paper options: ASML26MAY1300CE (short, EUR) and ASML26JUN1300CE (short, EUR); upsert on startup (updates ltp/pnl/pct_change each restart)

---

## 14. AI Agent Directives

1. **Always maintain the 3-tier separation.** System: one repo. Workflow: services only. Experience: read-only aggregation.
2. **Never inject a repository directly into a workflow router.** Use service classes.
3. **Experience tier has zero writes.** `db.commit()` in experience routers = bug.
4. **`_get_active_instrument_id(db)`** is defined independently in both `rita.py` and `pipeline_wizard.py`. Do not import across these files.
5. **LangGraph dependency** — `agent_panel.py` imports `langgraph`. Do not import it in core or system routers.
6. **Don't add `print()` statements** — use `structlog.get_logger()`.
7. **Don't hardcode lot sizes** — always use `get_settings().instruments`.
8. **Don't make external API calls** — all data is local CSV or DB.
9. **Paper positions** live in `paper_positions` table, not in `positions`. Route via `/api/v1/portfolio/positions?mode=paper`.
