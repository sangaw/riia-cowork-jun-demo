"""
Update API Reference page — v1.0 Complete (post observability refactoring).

Reflects the completed refactoring (2026-04-25): all 30 endpoints now live in
their correct ADR-001 tier files. observability.py has been deleted.

Run from project root:
    CONFLUENCE_EMAIL=contact@ravionics.nl python project-office/confluence/pages/publish_api_reference_v1.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from confluence.publish import ConfluenceClient, SECTION

PAGE_TITLE = "API Reference — v1.0 Complete"
PAGE_ID = "66650113"   # Original Sprint 2 page — updating in place

PAGE_BODY = """
<h1>API Reference — v1.0 Complete</h1>

<p>
  <strong>Last updated: 2026-04-25.</strong> This page supersedes the Sprint 2 stub.
  It documents every endpoint live in the v1.0 codebase, grouped by their correct
  architectural tier per <strong>ADR-001</strong>.
</p>
<p>
  All responses carry an <code>X-Request-ID</code> trace header.
  Error bodies follow <code>{"detail": "...", "trace_id": "..."}</code>.
  The API is served by <strong>FastAPI + Uvicorn</strong>.
  SQLite (SQLAlchemy 2.x) is the backing store per <strong>ADR-003</strong>.
</p>
<p>
  <strong>Observability refactoring complete (2026-04-25):</strong>
  All 30 endpoints previously in <code>api/v1/observability.py</code> have been
  migrated to their correct tier files. <code>observability.py</code> has been deleted.
  All existing URLs are preserved — no frontend JS changes were needed.
  All four dashboards (RITA, FnO, Ops, DS) are now 100% ADR-001 compliant.
</p>

<table>
  <thead>
    <tr><th>Tier</th><th>URL prefix</th><th>Purpose</th><th>Auth</th></tr>
  </thead>
  <tbody>
    <tr><td>Infrastructure</td><td><code>/health</code>, <code>/readyz</code>, etc.</td><td>k8s probes + reset</td><td>None</td></tr>
    <tr><td>1 — System</td><td><code>/api/v1/</code></td><td>Pure CRUD, one repo, zero business logic</td><td>None</td></tr>
    <tr><td>2 — Workflow</td><td><code>/api/v1/</code></td><td>Stateful orchestrations and long-running ML jobs</td><td>JWT on POST /pipeline; None on others</td></tr>
    <tr><td>3 — Experience</td><td><code>/api/v1/</code> and <code>/api/experience/</code></td><td>Read-only UI-shaped payloads (BFF)</td><td>None</td></tr>
    <tr><td>Auth</td><td><code>/auth/</code></td><td>Token issuance</td><td>None</td></tr>
    <tr><td>Portfolio</td><td><code>/api/v1/portfolio/</code></td><td>Cross-instrument compute (heavy, read-only)</td><td>None</td></tr>
  </tbody>
</table>

<hr />

<h2>Infrastructure Probes</h2>
<p>Registered directly on the FastAPI app (no tier prefix). Required by k8s.</p>

<table>
  <thead><tr><th>Method</th><th>Path</th><th>Description</th><th>Response</th></tr></thead>
  <tbody>
    <tr>
      <td>GET</td><td><code>/health</code></td>
      <td>Liveness probe. Returns model file status, CSV data freshness, Sharpe trend, last pipeline run timestamp. Always HTTP 200.</td>
      <td>200 <code>{"status":"ok","model_exists":bool,"data_freshness":{...},...}</code></td>
    </tr>
    <tr>
      <td>GET</td><td><code>/readyz</code></td>
      <td>Readiness probe. Runs <code>SELECT 1</code> against SQLite. Returns 503 if DB unreachable.</td>
      <td>200 <code>{"status":"ready"}</code> | 503</td>
    </tr>
    <tr>
      <td>GET</td><td><code>/progress</code></td>
      <td>Pipeline step bar for the RITA dashboard. Returns 8 named steps with statuses derived from training and backtest run records.</td>
      <td>200 <code>{"steps":[{"name":"Goal","status":"completed"},...]}</code></td>
    </tr>
    <tr>
      <td>POST</td><td><code>/reset</code></td>
      <td>Session reset acknowledgement (stateless API — no state is cleared).</td>
      <td>200 <code>{"status":"ok"}</code></td>
    </tr>
    <tr>
      <td>GET</td><td><code>/metrics</code></td>
      <td>Prometheus scrape endpoint (prometheus-fastapi-instrumentator). Exposes <code>http_request_duration_seconds</code> histogram.</td>
      <td>200 Prometheus text format</td>
    </tr>
  </tbody>
</table>

<hr />

<h2>Authentication — <code>/auth</code></h2>

<table>
  <thead><tr><th>Method</th><th>Path</th><th>Description</th><th>Response</th></tr></thead>
  <tbody>
    <tr>
      <td>POST</td><td><code>/auth/token</code></td>
      <td>Issue a JWT. Rate-limited to 10 req/min. Body: <code>{"username":"...","password":"..."}</code>. Token lifetime configured via <code>jwt_expire_minutes</code> in settings.</td>
      <td>200 <code>{"access_token":"...","token_type":"bearer"}</code></td>
    </tr>
  </tbody>
</table>

<hr />

<h2>Tier 1 — System CRUD Routers</h2>

<p>
  One router per table. Rules: call one repository only; zero business logic;
  never call a service or another router. Standard CRUD pattern throughout.
</p>

<h3>Positions — <code>/api/v1/system/positions</code></h3>
<table>
  <thead><tr><th>Method</th><th>Path</th><th>Description</th><th>Response</th></tr></thead>
  <tbody>
    <tr><td>GET</td><td><code>/</code></td><td>List all open positions</td><td>200 <code>list[Position]</code></td></tr>
    <tr><td>GET</td><td><code>/{id}</code></td><td>Fetch one position</td><td>200 <code>Position</code> | 404</td></tr>
    <tr><td>PUT</td><td><code>/{id}</code></td><td>Upsert a position</td><td>200 <code>Position</code></td></tr>
    <tr><td>DELETE</td><td><code>/{id}</code></td><td>Remove a position</td><td>204 | 404</td></tr>
  </tbody>
</table>

<h3>Orders — <code>/api/v1/system/orders</code></h3>
<table>
  <thead><tr><th>Method</th><th>Path</th><th>Description</th><th>Response</th></tr></thead>
  <tbody>
    <tr><td>GET</td><td><code>/</code></td><td>List all orders</td><td>200 <code>list[Order]</code></td></tr>
    <tr><td>GET</td><td><code>/{id}</code></td><td>Fetch one order</td><td>200 <code>Order</code> | 404</td></tr>
    <tr><td>PUT</td><td><code>/{id}</code></td><td>Upsert an order</td><td>200 <code>Order</code></td></tr>
    <tr><td>DELETE</td><td><code>/{id}</code></td><td>Remove an order</td><td>204 | 404</td></tr>
  </tbody>
</table>

<h3>Snapshots — <code>/api/v1/system/snapshots</code></h3>
<table>
  <thead><tr><th>Method</th><th>Path</th><th>Description</th><th>Response</th></tr></thead>
  <tbody>
    <tr><td>GET</td><td><code>/</code></td><td>List all portfolio snapshots</td><td>200 <code>list[Snapshot]</code></td></tr>
    <tr><td>GET</td><td><code>/{id}</code></td><td>Fetch one snapshot</td><td>200 <code>Snapshot</code> | 404</td></tr>
    <tr><td>PUT</td><td><code>/{id}</code></td><td>Upsert a snapshot</td><td>200 <code>Snapshot</code></td></tr>
    <tr><td>DELETE</td><td><code>/{id}</code></td><td>Remove a snapshot</td><td>204 | 404</td></tr>
  </tbody>
</table>

<h3>Trades — <code>/api/v1/system/trades</code></h3>
<table>
  <thead><tr><th>Method</th><th>Path</th><th>Description</th><th>Response</th></tr></thead>
  <tbody>
    <tr><td>GET</td><td><code>/</code></td><td>List all executed trades</td><td>200 <code>list[Trade]</code></td></tr>
    <tr><td>GET</td><td><code>/{id}</code></td><td>Fetch one trade</td><td>200 <code>Trade</code> | 404</td></tr>
    <tr><td>PUT</td><td><code>/{id}</code></td><td>Upsert a trade record</td><td>200 <code>Trade</code></td></tr>
    <tr><td>DELETE</td><td><code>/{id}</code></td><td>Remove a trade</td><td>204 | 404</td></tr>
  </tbody>
</table>

<h3>Alerts — <code>/api/v1/system/alerts</code></h3>
<table>
  <thead><tr><th>Method</th><th>Path</th><th>Description</th><th>Response</th></tr></thead>
  <tbody>
    <tr><td>GET</td><td><code>/</code></td><td>List all risk alerts</td><td>200 <code>list[Alert]</code></td></tr>
    <tr><td>GET</td><td><code>/{id}</code></td><td>Fetch one alert</td><td>200 <code>Alert</code> | 404</td></tr>
    <tr><td>PUT</td><td><code>/{id}</code></td><td>Upsert an alert</td><td>200 <code>Alert</code></td></tr>
    <tr><td>DELETE</td><td><code>/{id}</code></td><td>Remove an alert</td><td>204 | 404</td></tr>
  </tbody>
</table>

<h3>Audit Log — <code>/api/v1/system/audit</code></h3>
<table>
  <thead><tr><th>Method</th><th>Path</th><th>Description</th><th>Response</th></tr></thead>
  <tbody>
    <tr><td>GET</td><td><code>/</code></td><td>List all audit log entries</td><td>200 <code>list[AuditLog]</code></td></tr>
    <tr><td>GET</td><td><code>/{id}</code></td><td>Fetch one entry</td><td>200 <code>AuditLog</code> | 404</td></tr>
    <tr><td>PUT</td><td><code>/{id}</code></td><td>Upsert an entry</td><td>200 <code>AuditLog</code></td></tr>
    <tr><td>DELETE</td><td><code>/{id}</code></td><td>Remove an entry</td><td>204 | 404</td></tr>
  </tbody>
</table>

<h3>Market Data Cache — <code>/api/v1/system/market-data</code></h3>
<table>
  <thead><tr><th>Method</th><th>Path</th><th>Description</th><th>Response</th></tr></thead>
  <tbody>
    <tr><td>GET</td><td><code>/</code></td><td>List all cached OHLCV rows</td><td>200 <code>list[MarketDataCache]</code></td></tr>
    <tr><td>GET</td><td><code>/{id}</code></td><td>Fetch one row</td><td>200 <code>MarketDataCache</code> | 404</td></tr>
    <tr><td>PUT</td><td><code>/{id}</code></td><td>Upsert a row</td><td>200 <code>MarketDataCache</code></td></tr>
    <tr><td>DELETE</td><td><code>/{id}</code></td><td>Remove a row</td><td>204 | 404</td></tr>
  </tbody>
</table>

<h3>Config Overrides — <code>/api/v1/system/config-overrides</code></h3>
<table>
  <thead><tr><th>Method</th><th>Path</th><th>Description</th><th>Response</th></tr></thead>
  <tbody>
    <tr><td>GET</td><td><code>/</code></td><td>List all runtime config overrides</td><td>200 <code>list[ConfigOverride]</code></td></tr>
    <tr><td>GET</td><td><code>/{id}</code></td><td>Fetch one override</td><td>200 <code>ConfigOverride</code> | 404</td></tr>
    <tr><td>PUT</td><td><code>/{id}</code></td><td>Upsert an override</td><td>200 <code>ConfigOverride</code></td></tr>
    <tr><td>DELETE</td><td><code>/{id}</code></td><td>Remove an override</td><td>204 | 404</td></tr>
  </tbody>
</table>

<h3>Instruments — <code>/api/v1/instruments</code> — <code>system/instruments.py</code></h3>
<p>Manages the instrument registry (NIFTY, BANKNIFTY, ASML, NVIDIA). Seeded on startup.</p>
<table>
  <thead><tr><th>Method</th><th>Path</th><th>Description</th><th>Response</th></tr></thead>
  <tbody>
    <tr><td>GET</td><td><code>/api/v1/instruments</code></td><td>List all instruments with <code>data_ready</code> flag</td><td>200 <code>list[InstrumentSummary]</code></td></tr>
    <tr><td>POST</td><td><code>/api/v1/instruments</code></td><td>Register a new instrument</td><td>201 <code>{"status":"created","instrument_id":"..."}</code></td></tr>
    <tr><td>GET</td><td><code>/api/v1/instrument/active</code></td><td>Return the currently selected instrument (id, name, flag, exchange, lot_size)</td><td>200 <code>InstrumentActive</code></td></tr>
    <tr><td>PATCH</td><td><code>/api/v1/instruments/{id}/availability</code></td><td>Toggle <code>is_available</code> to show/hide instrument from users</td><td>200 <code>{"instrument_id":"...","is_available":bool}</code> | 404</td></tr>
  </tbody>
</table>

<h3>Market Signals — <code>/api/v1/market-signals</code> — <code>system/market_signals.py</code></h3>
<p>Technical indicators time series. Reads from the market-data cache or CSV fallback.</p>
<table>
  <thead><tr><th>Method</th><th>Path</th><th>Description</th><th>Response</th></tr></thead>
  <tbody>
    <tr>
      <td>GET</td><td><code>/api/v1/market-signals</code></td>
      <td>
        Returns RSI-14, MACD, Bollinger Bands, ATR-14, EMA-5/13/26/50, trend score per bar.<br/>
        Params: <code>instrument</code> (default NIFTY), <code>timeframe</code> (daily/weekly/monthly),
        <code>periods</code> (default 252).
      </td>
      <td>200 <code>list[SignalBar]</code></td>
    </tr>
  </tbody>
</table>

<h3>Training Run Reads — <code>system/training_runs.py</code></h3>
<table>
  <thead><tr><th>Method</th><th>Path</th><th>Description</th><th>Response</th></tr></thead>
  <tbody>
    <tr>
      <td>GET</td><td><code>/api/v1/training-history</code></td>
      <td>All training runs newest-first, enriched with Sharpe/MDD/return/CAGR percentages per phase (train, val, backtest). Param: <code>instrument</code>.</td>
      <td>200 <code>list[TrainingHistoryRow]</code></td>
    </tr>
    <tr>
      <td>GET</td><td><code>/api/v1/training-split</code></td>
      <td>Actual train/val/backtest date ranges for an instrument. Derived from the CSV 80/20 split + latest completed backtest record.</td>
      <td>200 <code>{"train_start":str,"train_end":str,"val_start":str,"val_end":str,"backtest_start":str,"backtest_end":str}</code></td>
    </tr>
  </tbody>
</table>

<h3>System Health Data — <code>system/data_prep.py</code></h3>
<table>
  <thead><tr><th>Method</th><th>Path</th><th>Description</th><th>Response</th></tr></thead>
  <tbody>
    <tr>
      <td>GET</td><td><code>/api/v1/data-prep/status</code></td>
      <td>Data pipeline stage checks: raw CSV, manual daily extension, model files. Returns per-stage ok/warn/error and overall status.</td>
      <td>200 <code>{"status":"ok"|"warn"|"error","stages":[...]}</code></td>
    </tr>
    <tr>
      <td>GET</td><td><code>/api/v1/test-results</code></td>
      <td>Reads JUnit XML from <code>test-results/</code>. Returns pass/fail counts grouped by e2e suite (rita/fno/ops) and by unit/integration module.</td>
      <td>200 <code>{"data_available":bool,"total":int,"passed":int,"suite_summary":{...},"modules":[...],"suites":[...]}</code></td>
    </tr>
    <tr>
      <td>GET</td><td><code>/api/v1/mcp-calls</code></td>
      <td>MCP tool call log. Always returns empty list in this deployment (no external MCP servers).</td>
      <td>200 <code>[]</code></td>
    </tr>
  </tbody>
</table>

<h3>Drift — <code>/api/v1/drift</code> — <code>system/drift.py</code></h3>
<table>
  <thead><tr><th>Method</th><th>Path</th><th>Description</th><th>Response</th></tr></thead>
  <tbody>
    <tr>
      <td>GET</td><td><code>/api/v1/drift</code></td>
      <td>
        Five-check model health report via <code>DriftDetector</code>:
        <code>sharpe_drift</code>, <code>return_degradation</code>,
        <code>data_freshness</code>, <code>pipeline_health</code>, <code>constraint_breach</code>.
        Overall status is the worst across all checks (ok &lt; warn &lt; alert).
      </td>
      <td>200 <code>{"summary":{"overall":"ok"|"warn"|"alert","checks":{...}},"checks":{...}}</code></td>
    </tr>
  </tbody>
</table>

<hr />

<h2>Tier 2 — Workflow Routers</h2>

<p>
  Stateful orchestrations and long-running ML jobs. All workflow routes are
  <strong>JWT-protected</strong> (Bearer token from <code>/auth/token</code>).
  Jobs dispatch to background daemon threads and return <code>202 Accepted</code>
  immediately. Poll the corresponding GET endpoint for status.
</p>

<h3>Training — <code>/api/v1/workflow/train</code></h3>
<table>
  <thead><tr><th>Method</th><th>Path</th><th>Description</th><th>Response</th></tr></thead>
  <tbody>
    <tr><td>POST</td><td><code>/</code></td><td>Submit a new DoubleDQN training job. Dispatches daemon thread. Body: <code>TrainingRunCreate</code>.</td><td>202 <code>TrainingRun</code></td></tr>
    <tr><td>GET</td><td><code>/</code></td><td>List all training runs</td><td>200 <code>list[TrainingRun]</code></td></tr>
    <tr><td>GET</td><td><code>/{run_id}</code></td><td>Fetch one training run</td><td>200 <code>TrainingRun</code> | 404</td></tr>
    <tr><td>GET</td><td><code>/{run_id}/metrics</code></td><td>Episode-level reward/loss metrics for a run</td><td>200 <code>list[TrainingMetric]</code> | 404</td></tr>
  </tbody>
</table>

<h4>TrainingRunCreate body</h4>
<pre>
{
  "instrument":      "NIFTY",           // instrument id (uppercase)
  "model_version":   "v1.0",
  "algorithm":       "DoubleDQN",
  "timesteps":       200000,
  "learning_rate":   0.0001,
  "buffer_size":     50000,
  "net_arch":        "[128, 128]",
  "exploration_pct": 0.1,
  "notes":           ""
}
</pre>

<h3>Backtest — <code>/api/v1/workflow/backtest</code></h3>
<table>
  <thead><tr><th>Method</th><th>Path</th><th>Description</th><th>Response</th></tr></thead>
  <tbody>
    <tr><td>POST</td><td><code>/</code></td><td>Submit a backtest job against a trained model. Body: <code>BacktestRunCreate</code>.</td><td>202 <code>BacktestRun</code></td></tr>
    <tr><td>GET</td><td><code>/</code></td><td>List all backtest runs</td><td>200 <code>list[BacktestRun]</code></td></tr>
    <tr><td>GET</td><td><code>/{run_id}</code></td><td>Fetch one backtest run</td><td>200 <code>BacktestRun</code> | 404</td></tr>
    <tr><td>GET</td><td><code>/{run_id}/results</code></td><td>Daily backtest result rows for a run</td><td>200 <code>list[BacktestResult]</code> | 404</td></tr>
  </tbody>
</table>

<h3>Evaluate — <code>/api/v1/workflow/evaluate</code></h3>
<table>
  <thead><tr><th>Method</th><th>Path</th><th>Description</th><th>Response</th></tr></thead>
  <tbody>
    <tr><td>POST</td><td><code>/</code></td><td>Submit a model evaluation job.</td><td>202 <code>EvaluationRun</code></td></tr>
    <tr><td>GET</td><td><code>/</code></td><td>List all evaluation runs</td><td>200 <code>list[EvaluationRun]</code></td></tr>
    <tr><td>GET</td><td><code>/{run_id}</code></td><td>Fetch one evaluation run</td><td>200 <code>EvaluationRun</code> | 404</td></tr>
  </tbody>
</table>

<h3>Chat — <code>/api/v1/workflow/chat</code></h3>
<table>
  <thead><tr><th>Method</th><th>Path</th><th>Description</th><th>Response</th></tr></thead>
  <tbody>
    <tr>
      <td>POST</td><td><code>/api/v1/chat</code></td>
      <td>
        Local intent classifier + OHLCV dispatch. Classifies the user message into an intent
        (price query, indicator, model status, help) and returns a structured response.
        No external API calls — all data is local.
      </td>
      <td>200 <code>{"intent":"...","response":"...","data":{...}}</code></td>
    </tr>
  </tbody>
</table>

<h3>Pipeline — <code>/api/v1/pipeline</code> — <code>workflow/pipeline.py</code></h3>
<p>
  Orchestrates a full train → backtest sequence in a single call. This is the primary
  entry point used by the RITA dashboard pipeline wizard. <strong>JWT required</strong> on POST.
</p>
<table>
  <thead><tr><th>Method</th><th>Path</th><th>Description</th><th>Response</th></tr></thead>
  <tbody>
    <tr>
      <td>POST</td><td><code>/api/v1/pipeline</code></td>
      <td>
        Triggers train + backtest pipeline asynchronously (202 Accepted).
        Reuses existing model when <code>force_retrain=false</code> and a <code>.zip</code> exists.
        Returns both <code>train_run_id</code> and <code>backtest_run_id</code> for polling.
      </td>
      <td>202 <code>{"status":"accepted","train_run_id":"...","backtest_run_id":"..."}</code></td>
    </tr>
  </tbody>
</table>

<h4>PipelineRequest body</h4>
<pre>
{
  "instrument":        "NIFTY",
  "target_return_pct": 15.0,
  "time_horizon_days": 365,
  "risk_tolerance":    "moderate",
  "timesteps":         200000,
  "force_retrain":     false,
  "n_seeds":           1,
  "sim_start":         null,    // ISO date override (YYYY-MM-DD)
  "sim_end":           null
}
</pre>

<h3>Instrument Selection — <code>workflow/pipeline.py</code></h3>
<table>
  <thead><tr><th>Method</th><th>Path</th><th>Description</th><th>Response</th></tr></thead>
  <tbody>
    <tr>
      <td>POST</td><td><code>/api/v1/instrument/select</code></td>
      <td>
        Sets the active instrument for subsequent pipeline runs and performance reads.
        Validates instrument exists in DB, then persists the selection to the
        <code>config_overrides</code> table (<code>override_id = "active_instrument_id"</code>) —
        survives server restarts.
      </td>
      <td>200 <code>InstrumentActive</code> | 404</td>
    </tr>
  </tbody>
</table>

<h3>Live Training Progress — <code>workflow/pipeline.py</code></h3>
<table>
  <thead><tr><th>Method</th><th>Path</th><th>Description</th><th>Response</th></tr></thead>
  <tbody>
    <tr>
      <td>GET</td><td><code>/api/v1/training-progress</code></td>
      <td>
        Live progress records polled every 2 s by the DS dashboard during training.
        Each record: <code>{"timestep":int,"loss":float,"ep_rew_mean":float}</code>.
        Returns <code>[]</code> when no run is active. Param: <code>run_id</code>.
      </td>
      <td>200 <code>list[ProgressRecord]</code></td>
    </tr>
  </tbody>
</table>

<hr />

<h2>Tier 3 — Experience Layer (BFF)</h2>

<p>
  Read-only aggregation routers. One request returns everything a UI view needs —
  no waterfall fetches from the browser. No writes, no side effects (ADR-001 Tier 3 rules).
</p>

<h3>Dashboard — <code>/api/experience/dashboard</code></h3>
<table>
  <thead><tr><th>Method</th><th>Path</th><th>Description</th><th>Response</th></tr></thead>
  <tbody>
    <tr>
      <td>GET</td><td><code>/</code></td>
      <td>
        Aggregated RITA trading dashboard payload: open positions + latest training run + recent alerts.
        Param: <code>alert_limit</code> (1–200, default 20).
      </td>
      <td>200 <code>DashboardPayload</code></td>
    </tr>
  </tbody>
</table>
<pre>
DashboardPayload {
  positions:            list[Position],
  latest_training_run:  TrainingRun | null,
  recent_alerts:        list[Alert]
}
</pre>

<h3>FnO — <code>/api/experience/fno</code></h3>
<table>
  <thead><tr><th>Method</th><th>Path</th><th>Description</th><th>Response</th></tr></thead>
  <tbody>
    <tr>
      <td>GET</td><td><code>/</code></td>
      <td>Full FnO portfolio payload: market data, positions, greeks, margin, stress, payoff, manoeuvres.</td>
      <td>200 <code>FnoPayload</code></td>
    </tr>
    <tr>
      <td>GET</td><td><code>/manoeuvres</code></td>
      <td>All recorded manoeuvres (portfolio actions)</td>
      <td>200 <code>list[Manoeuvre]</code></td>
    </tr>
    <tr>
      <td>POST</td><td><code>/manoeuvres</code></td>
      <td>Record a new manoeuvre</td>
      <td>201 <code>Manoeuvre</code></td>
    </tr>
    <tr>
      <td>GET</td><td><code>/portfolio/history</code></td>
      <td>Historical portfolio valuation records</td>
      <td>200 <code>list[PortfolioRecord]</code></td>
    </tr>
  </tbody>
</table>

<h3>Ops — <code>/api/experience/ops</code></h3>
<table>
  <thead><tr><th>Method</th><th>Path</th><th>Description</th><th>Response</th></tr></thead>
  <tbody>
    <tr>
      <td>GET</td><td><code>/</code></td>
      <td>
        Aggregated Ops payload: training run history + backtest run history + recent audit log.
        Param: <code>audit_limit</code> (1–1000, default 100).
      </td>
      <td>200 <code>OpsPayload</code></td>
    </tr>
  </tbody>
</table>
<pre>
OpsPayload {
  training_runs:  list[TrainingRun],
  backtest_runs:  list[BacktestRun],
  recent_audit:   list[AuditLog]
}
</pre>

<h3>RITA Performance &amp; Risk — <code>experience/rita.py</code></h3>
<p>UI-shaped payloads for the RITA dashboard performance, risk, and trade-journal sections.</p>
<table>
  <thead><tr><th>Method</th><th>Path</th><th>Description</th><th>Response</th></tr></thead>
  <tbody>
    <tr>
      <td>GET</td><td><code>/api/v1/performance-summary</code></td>
      <td>
        KPI card data for the RITA dashboard top row.
        Computed from the latest completed backtest for the active instrument.
        Includes stale-check fields <code>_run_instrument_id</code> and <code>_active_instrument_id</code>
        so the frontend can blank KPIs when they are out of sync.
      </td>
      <td>200 <code>PerformanceSummary</code></td>
    </tr>
    <tr>
      <td>GET</td><td><code>/api/v1/backtest-daily</code></td>
      <td>Daily portfolio vs benchmark values for the performance chart. Latest completed backtest, active instrument.</td>
      <td>200 <code>list[{"date":str,"portfolio_value":float,"benchmark_value":float,"allocation":float}]</code></td>
    </tr>
    <tr>
      <td>GET</td><td><code>/api/v1/performance-feedback</code></td>
      <td>
        Structured performance feedback: return_metrics, risk_metrics, trade_activity,
        constraint status, training context, and forward-looking return expectations.
        Calls <code>core/performance.build_performance_feedback()</code>.
      </td>
      <td>200 <code>PerformanceFeedback</code></td>
    </tr>
    <tr>
      <td>GET</td><td><code>/api/v1/portfolio-comparison</code></td>
      <td>
        RITA RL model vs Conservative/Moderate/Aggressive fixed-allocation profiles.
        Param: <code>portfolio_inr</code> (default 1,000,000).
        Calls <code>core/performance.build_portfolio_comparison()</code>.
      </td>
      <td>200 <code>PortfolioComparison</code></td>
    </tr>
    <tr>
      <td>GET</td><td><code>/api/v1/risk-timeline</code></td>
      <td>
        Daily portfolio vs benchmark with drawdown, regime label (Bull/Neutral/Bear),
        and rolling volatility. Used by risk.js and trades.js.
        Params: <code>phase</code> (all/train/test), <code>instrument</code>.
      </td>
      <td>200 <code>list[RiskTimelineRow]</code></td>
    </tr>
  </tbody>
</table>

<h3>Ops Monitoring Summaries — <code>experience/ops.py</code></h3>
<table>
  <thead><tr><th>Method</th><th>Path</th><th>Description</th><th>Response</th></tr></thead>
  <tbody>
    <tr>
      <td>GET</td><td><code>/api/v1/metrics/summary</code></td>
      <td>
        Structured JSON of live Prometheus metrics + training KPIs.
        Composes: API request totals/error rates/latency from Prometheus REGISTRY
        + completed/failed step counts + latest Sharpe/MDD/CAGR from training_runs table.
      </td>
      <td>200 <code>{"api_requests":{...},"pipeline":{...},"training":{...}}</code></td>
    </tr>
    <tr>
      <td>GET</td><td><code>/api/v1/step-log</code></td>
      <td>
        Latest pipeline run composed as 4 logical steps: Load Data, Compute Indicators,
        Train Model, Backtest. Status and timings from the most recent training + backtest records.
      </td>
      <td>200 <code>list[StepRow]</code></td>
    </tr>
  </tbody>
</table>

<h3>DS Pipeline Wizard — <code>experience/pipeline_wizard.py</code></h3>
<p>Three sequential steps that render in the RITA Pipeline tab (goal → market → strategy).</p>
<table>
  <thead><tr><th>Method</th><th>Path</th><th>Description</th><th>Response</th></tr></thead>
  <tbody>
    <tr>
      <td>POST</td><td><code>/api/v1/goal</code></td>
      <td>
        Step 1: Feasibility analysis for a financial goal.
        Computes annualised target, monthly return requirement, feasibility rating
        (conservative/realistic/ambitious/unrealistic), and historical yearly returns.
        Body: <code>{"target_return_pct":float,"time_horizon_days":int,"risk_tolerance":str}</code>.
      </td>
      <td>200 <code>{"step":1,"name":"Financial Goal","result":{...}}</code></td>
    </tr>
    <tr>
      <td>POST</td><td><code>/api/v1/market</code></td>
      <td>
        Step 2: Market conditions snapshot for the active instrument.
        Returns RSI, MACD, Bollinger, ATR, EMAs, trend label, and sentiment proxy from
        the latest 252 bars.
      </td>
      <td>200 <code>{"step":2,"name":"Market Analysis","result":{...}}</code></td>
    </tr>
    <tr>
      <td>POST</td><td><code>/api/v1/strategy</code></td>
      <td>
        Step 3: Strategy configuration derived from application settings
        (algorithm, timesteps, risk tolerance, lot sizes, output directory).
      </td>
      <td>200 <code>{"step":3,"name":"Strategy Design","result":{...}}</code></td>
    </tr>
  </tbody>
</table>

<hr />

<h2>Portfolio — <code>/api/v1/portfolio</code></h2>

<p>
  Cross-instrument computation endpoints. These are <strong>read-only</strong> and run heavy
  computation (portfolio engine, backtest simulation). They live at <code>/api/v1/portfolio/</code>
  rather than the experience layer because they are not simple DB aggregations —
  they re-run the backtest engine and return multi-instrument results.
</p>

<table>
  <thead><tr><th>Method</th><th>Path</th><th>Description</th><th>Response</th></tr></thead>
  <tbody>
    <tr>
      <td>GET</td><td><code>/api/v1/portfolio/overview</code></td>
      <td>
        Loads all 4 instruments, aligns to common date intersection.
        Returns normalised returns (≤500 pts), correlation matrix, common days, date range.
      </td>
      <td>200 <code>PortfolioOverview</code></td>
    </tr>
    <tr>
      <td>POST</td><td><code>/api/v1/portfolio/backtest</code></td>
      <td>
        Multi-instrument portfolio backtest. Runs <code>run_episode()</code> per instrument
        (or B&amp;H fallback if no trained model), combines with EUR allocation weights.
        Body: <code>PortfolioBacktestRequest</code>.
      </td>
      <td>200 <code>PortfolioBacktestResult</code></td>
    </tr>
  </tbody>
</table>

<h4>PortfolioBacktestRequest body</h4>
<pre>
{
  "instruments":      ["NIFTY","BANKNIFTY","ASML","NVIDIA"],
  "allocations_eur":  {"nifty":10000,"banknifty":5000,"asml":5000,"nvidia":5000},
  "start_date":       "2024-01-01",
  "end_date":         "2025-01-01"
}
</pre>

<hr />

<h2>Common Patterns</h2>

<h3>Trace IDs</h3>
<p>Every request is assigned a UUID trace ID via <code>TraceIDMiddleware</code>.</p>
<pre>
HTTP/1.1 404 Not Found
X-Request-ID: 3f2a1b9c-...

{"detail": "Instrument 'XYZ' not found", "trace_id": "3f2a1b9c-..."}
</pre>

<h3>Error status codes</h3>
<table>
  <thead><tr><th>Status</th><th>Trigger</th></tr></thead>
  <tbody>
    <tr><td>400</td><td>Request body fails Pydantic validation (<code>RequestValidationError</code>)</td></tr>
    <tr><td>401</td><td>Missing or invalid JWT on a workflow route</td></tr>
    <tr><td>404</td><td>Resource not found (route handler explicit)</td></tr>
    <tr><td>422</td><td>Repository-level schema validation failure (<code>RepositoryValidationError</code>)</td></tr>
    <tr><td>429</td><td>Rate limit exceeded (slowapi: 60 req/min global, 10 req/min on /auth/token)</td></tr>
    <tr><td>500</td><td>Unhandled exception — detail suppressed, trace ID included</td></tr>
    <tr><td>503</td><td>DB unreachable (<code>/readyz</code> only)</td></tr>
  </tbody>
</table>

<h3>Authentication</h3>
<p>
  Workflow routes (<code>/api/v1/workflow/train</code>, <code>/backtest</code>, <code>/evaluate</code>)
  require a <code>Authorization: Bearer &lt;token&gt;</code> header.
  Obtain a token from <code>POST /auth/token</code>.
  All other routes (system, experience, portfolio, probes) are unauthenticated.
</p>

<h3>Dependency injection pattern (Sprint 2.5+)</h3>
<pre>
# All routers since Day 16 use this pattern:
def get_svc(db: Session = Depends(get_db)) -&gt; MyService:
    return MyService(db)

@router.get("/")
def my_endpoint(svc: MyService = Depends(get_svc)):
    return svc.do_work()
</pre>

<h3>DS Dashboard — <code>experience/ds.py</code></h3>
<p>Aggregated initial-load payload for the DS dashboard. One request returns everything the DS view needs.</p>
<table>
  <thead><tr><th>Method</th><th>Path</th><th>Description</th><th>Response</th></tr></thead>
  <tbody>
    <tr>
      <td>GET</td><td><code>/api/experience/ds/</code></td>
      <td>
        Returns instruments list + last 10 training runs + training/validation/backtest split dates.
        Param: <code>instrument</code> (default NIFTY).
        Split dates derived from CSV 80/20 boundary + latest completed backtest record.
      </td>
      <td>200 <code>{"instruments":[...],"training_context":{"history":[...],"split":{...}}}</code></td>
    </tr>
  </tbody>
</table>

<hr />

<h2>Observability Refactoring — Completed 2026-04-25</h2>

<p>
  <code>api/v1/observability.py</code> (30 endpoints, ~2,200 lines) has been deleted.
  All endpoints were mapped to their correct ADR-001 tier and moved to purpose-built files.
  All URLs are preserved — no frontend JS changes were required.
</p>

<table>
  <thead><tr><th>New file</th><th>Endpoints</th></tr></thead>
  <tbody>
    <tr><td><code>api/v1/system/instruments.py</code></td><td>GET/POST /instruments, GET /instrument/active, PATCH /instruments/{id}/availability</td></tr>
    <tr><td><code>api/v1/system/market_signals.py</code></td><td>GET /market-signals</td></tr>
    <tr><td><code>api/v1/system/training_runs.py</code></td><td>GET /training-history, GET /training-split, GET /backtest-status/{run_id}</td></tr>
    <tr><td><code>api/v1/system/drift.py</code></td><td>GET /drift</td></tr>
    <tr><td><code>api/v1/system/data_prep.py</code></td><td>GET /data-prep/status, GET /test-results, GET /mcp-calls, GET /shap, GET /data-understanding</td></tr>
    <tr><td><code>api/v1/workflow/pipeline.py</code></td><td>POST /pipeline (JWT), POST /instrument/select, GET /training-progress, POST /backtest</td></tr>
    <tr><td><code>api/experience/rita.py</code></td><td>GET /performance-summary, /backtest-daily, /performance-feedback, /portfolio-comparison, /risk-timeline, /trade-events, /stress-scenarios</td></tr>
    <tr><td><code>api/experience/ops.py</code> (extended)</td><td>GET /metrics/summary, GET /step-log</td></tr>
    <tr><td><code>api/experience/pipeline_wizard.py</code></td><td>POST /goal, POST /market, POST /strategy</td></tr>
    <tr><td><code>api/experience/ds.py</code> (new)</td><td>GET /api/experience/ds/</td></tr>
  </tbody>
</table>

<p><strong>Active instrument state:</strong> Migrated from in-memory global to <code>config_overrides</code>
table row (<code>override_id = "active_instrument_id"</code>) — selection now survives server restarts.</p>

<p><strong>ADR-001 compliance after refactoring:</strong></p>
<table>
  <thead><tr><th>App</th><th>Before</th><th>After</th></tr></thead>
  <tbody>
    <tr><td>RITA Dashboard</td><td>7%</td><td>100%</td></tr>
    <tr><td>FnO Dashboard</td><td>100%</td><td>100%</td></tr>
    <tr><td>Ops Dashboard</td><td>14%</td><td>100%</td></tr>
    <tr><td>DS Dashboard</td><td>0%</td><td>100%</td></tr>
  </tbody>
</table>
"""


if __name__ == "__main__":
    client = ConfluenceClient()

    pid, url = client.update_page(PAGE_ID, PAGE_TITLE, PAGE_BODY)
    print(f"Updated: {PAGE_TITLE}")
    print(f"  URL: {url}")
