"""
Day 14 — Publish Sprint 2 API Reference to Confluence.

Covers all three API tiers from Sprint 2:
  - Tier 1: System CRUD routers (8 tables)
  - Tier 2: Workflow routers (train, backtest, evaluate)
  - Tier 3: Experience Layer routers (dashboard, fno, ops)

Run from project root:
    CONFLUENCE_EMAIL=contact@ravionics.nl python project-office/confluence/pages/publish_sprint2_api_reference.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from confluence.publish import ConfluenceClient, SECTION

PAGE_TITLE = "Sprint 2: API Reference"
PAGE_ID = "66650113"

PAGE_BODY = """
<h1>Sprint 2: API Reference</h1>

<p>
  RITA exposes a three-tier REST API built with <strong>FastAPI</strong>, structured
  per <a href="ADR-001">ADR-001</a>. All responses include a <code>X-Request-ID</code>
  trace header. Error bodies follow the shape <code>{"detail": "...", "trace_id": "..."}</code>.
</p>

<table>
  <thead>
    <tr>
      <th>Tier</th><th>Prefix</th><th>Purpose</th>
    </tr>
  </thead>
  <tbody>
    <tr><td>1 — System</td><td><code>/api/v1/system/</code></td><td>Pure CRUD over CSV tables</td></tr>
    <tr><td>2 — Workflow</td><td><code>/api/v1/workflow/</code></td><td>Business-process operations (train, backtest, evaluate)</td></tr>
    <tr><td>3 — Experience</td><td><code>/api/experience/</code></td><td>Aggregated BFF payloads for the dashboard UI</td></tr>
  </tbody>
</table>

<hr />

<h2>Tier 1 — System CRUD Routers</h2>

<p>
  Eight routers, one per CSV table. All follow the same pattern:
  <code>GET /</code> (list), <code>GET /{id}</code> (fetch one),
  <code>PUT /{id}</code> (upsert), <code>DELETE /{id}</code> (remove).
</p>

<h3>Positions — <code>/api/v1/system/positions</code></h3>
<table>
  <thead><tr><th>Method</th><th>Path</th><th>Description</th><th>Response</th></tr></thead>
  <tbody>
    <tr><td>GET</td><td>/</td><td>List all open positions</td><td>200 <code>list[Position]</code></td></tr>
    <tr><td>GET</td><td>/{id}</td><td>Fetch a single position by ID</td><td>200 <code>Position</code> | 404</td></tr>
    <tr><td>PUT</td><td>/{id}</td><td>Upsert a position record</td><td>200 <code>Position</code></td></tr>
    <tr><td>DELETE</td><td>/{id}</td><td>Remove a position</td><td>204 | 404</td></tr>
  </tbody>
</table>

<h3>Orders — <code>/api/v1/system/orders</code></h3>
<table>
  <thead><tr><th>Method</th><th>Path</th><th>Description</th><th>Response</th></tr></thead>
  <tbody>
    <tr><td>GET</td><td>/</td><td>List all orders</td><td>200 <code>list[Order]</code></td></tr>
    <tr><td>GET</td><td>/{id}</td><td>Fetch a single order</td><td>200 <code>Order</code> | 404</td></tr>
    <tr><td>PUT</td><td>/{id}</td><td>Upsert an order</td><td>200 <code>Order</code></td></tr>
    <tr><td>DELETE</td><td>/{id}</td><td>Remove an order</td><td>204 | 404</td></tr>
  </tbody>
</table>

<h3>Snapshots — <code>/api/v1/system/snapshots</code></h3>
<table>
  <thead><tr><th>Method</th><th>Path</th><th>Description</th><th>Response</th></tr></thead>
  <tbody>
    <tr><td>GET</td><td>/</td><td>List all portfolio snapshots</td><td>200 <code>list[Snapshot]</code></td></tr>
    <tr><td>GET</td><td>/{id}</td><td>Fetch a snapshot</td><td>200 <code>Snapshot</code> | 404</td></tr>
    <tr><td>PUT</td><td>/{id}</td><td>Upsert a snapshot</td><td>200 <code>Snapshot</code></td></tr>
    <tr><td>DELETE</td><td>/{id}</td><td>Remove a snapshot</td><td>204 | 404</td></tr>
  </tbody>
</table>

<h3>Trades — <code>/api/v1/system/trades</code></h3>
<table>
  <thead><tr><th>Method</th><th>Path</th><th>Description</th><th>Response</th></tr></thead>
  <tbody>
    <tr><td>GET</td><td>/</td><td>List all executed trades</td><td>200 <code>list[Trade]</code></td></tr>
    <tr><td>GET</td><td>/{id}</td><td>Fetch a single trade</td><td>200 <code>Trade</code> | 404</td></tr>
    <tr><td>PUT</td><td>/{id}</td><td>Upsert a trade record</td><td>200 <code>Trade</code></td></tr>
    <tr><td>DELETE</td><td>/{id}</td><td>Remove a trade</td><td>204 | 404</td></tr>
  </tbody>
</table>

<h3>Alerts — <code>/api/v1/system/alerts</code></h3>
<table>
  <thead><tr><th>Method</th><th>Path</th><th>Description</th><th>Response</th></tr></thead>
  <tbody>
    <tr><td>GET</td><td>/</td><td>List all risk alerts</td><td>200 <code>list[Alert]</code></td></tr>
    <tr><td>GET</td><td>/{id}</td><td>Fetch a single alert</td><td>200 <code>Alert</code> | 404</td></tr>
    <tr><td>PUT</td><td>/{id}</td><td>Upsert an alert</td><td>200 <code>Alert</code></td></tr>
    <tr><td>DELETE</td><td>/{id}</td><td>Remove an alert</td><td>204 | 404</td></tr>
  </tbody>
</table>

<h3>Audit Log — <code>/api/v1/system/audit</code></h3>
<table>
  <thead><tr><th>Method</th><th>Path</th><th>Description</th><th>Response</th></tr></thead>
  <tbody>
    <tr><td>GET</td><td>/</td><td>List all audit log entries</td><td>200 <code>list[AuditEntry]</code></td></tr>
    <tr><td>GET</td><td>/{id}</td><td>Fetch a single audit entry</td><td>200 <code>AuditEntry</code> | 404</td></tr>
    <tr><td>PUT</td><td>/{id}</td><td>Upsert an audit entry</td><td>200 <code>AuditEntry</code></td></tr>
    <tr><td>DELETE</td><td>/{id}</td><td>Remove an audit entry</td><td>204 | 404</td></tr>
  </tbody>
</table>

<h3>Market Data — <code>/api/v1/system/market-data</code></h3>
<table>
  <thead><tr><th>Method</th><th>Path</th><th>Description</th><th>Response</th></tr></thead>
  <tbody>
    <tr><td>GET</td><td>/</td><td>List all market data rows</td><td>200 <code>list[MarketData]</code></td></tr>
    <tr><td>GET</td><td>/{id}</td><td>Fetch a single market data row</td><td>200 <code>MarketData</code> | 404</td></tr>
    <tr><td>PUT</td><td>/{id}</td><td>Upsert a market data row</td><td>200 <code>MarketData</code></td></tr>
    <tr><td>DELETE</td><td>/{id}</td><td>Remove a market data row</td><td>204 | 404</td></tr>
  </tbody>
</table>

<h3>Config Overrides — <code>/api/v1/system/config-overrides</code></h3>
<table>
  <thead><tr><th>Method</th><th>Path</th><th>Description</th><th>Response</th></tr></thead>
  <tbody>
    <tr><td>GET</td><td>/</td><td>List all runtime config overrides</td><td>200 <code>list[ConfigOverride]</code></td></tr>
    <tr><td>GET</td><td>/{id}</td><td>Fetch a single override</td><td>200 <code>ConfigOverride</code> | 404</td></tr>
    <tr><td>PUT</td><td>/{id}</td><td>Upsert a config override</td><td>200 <code>ConfigOverride</code></td></tr>
    <tr><td>DELETE</td><td>/{id}</td><td>Remove a config override</td><td>204 | 404</td></tr>
  </tbody>
</table>

<hr />

<h2>Tier 2 — Workflow Routers</h2>

<p>
  Business-process operations. All writes go via a service layer; repositories are
  never called directly from workflow routes (ADR-001). ML dispatch is deferred to
  Sprint 3 — <em>start_training</em> and <em>start_backtest</em> currently create
  a <code>status=pending</code> record and return <code>202 Accepted</code>.
</p>

<h3>Training — <code>/api/v1/workflow/train</code></h3>
<table>
  <thead><tr><th>Method</th><th>Path</th><th>Description</th><th>Response</th></tr></thead>
  <tbody>
    <tr><td>POST</td><td>/</td><td>Submit a new DQN training job. Returns <code>status=pending</code>.</td><td>202 <code>TrainingRun</code></td></tr>
    <tr><td>GET</td><td>/</td><td>List all training runs</td><td>200 <code>list[TrainingRun]</code></td></tr>
    <tr><td>GET</td><td>/{run_id}</td><td>Fetch a single training run</td><td>200 <code>TrainingRun</code> | 404</td></tr>
    <tr><td>GET</td><td>/{run_id}/metrics</td><td>List training metrics for a run</td><td>200 <code>list[TrainingMetric]</code> | 404</td></tr>
  </tbody>
</table>

<h4>TrainingRunCreate body</h4>
<pre>
{
  "model_version": "string",       // e.g. "v1.2"
  "episodes":      integer,         // number of training episodes
  "config":        object           // optional hyperparameter overrides
}
</pre>

<h3>Backtest — <code>/api/v1/workflow/backtest</code></h3>
<table>
  <thead><tr><th>Method</th><th>Path</th><th>Description</th><th>Response</th></tr></thead>
  <tbody>
    <tr><td>POST</td><td>/</td><td>Submit a new backtest job. Returns <code>status=pending</code>.</td><td>202 <code>BacktestRun</code></td></tr>
    <tr><td>GET</td><td>/</td><td>List all backtest runs</td><td>200 <code>list[BacktestRun]</code></td></tr>
    <tr><td>GET</td><td>/{run_id}</td><td>Fetch a single backtest run</td><td>200 <code>BacktestRun</code> | 404</td></tr>
  </tbody>
</table>

<h3>Evaluate — <code>/api/v1/workflow/evaluate</code></h3>
<table>
  <thead><tr><th>Method</th><th>Path</th><th>Description</th><th>Response</th></tr></thead>
  <tbody>
    <tr><td>POST</td><td>/</td><td>Submit a model evaluation job. Returns <code>status=pending</code>.</td><td>202 <code>EvaluationRun</code></td></tr>
    <tr><td>GET</td><td>/</td><td>List all evaluation runs</td><td>200 <code>list[EvaluationRun]</code></td></tr>
    <tr><td>GET</td><td>/{run_id}</td><td>Fetch a single evaluation run</td><td>200 <code>EvaluationRun</code> | 404</td></tr>
  </tbody>
</table>

<hr />

<h2>Tier 3 — Experience Layer (BFF)</h2>

<p>
  Read-only aggregation endpoints. One GET call returns everything the UI needs for
  a given view, eliminating waterfall requests from the browser. No writes, no side
  effects (ADR-001, Tier 3 rules).
</p>

<h3>Dashboard — <code>/api/experience/dashboard</code></h3>
<table>
  <thead><tr><th>Method</th><th>Path</th><th>Description</th><th>Response</th></tr></thead>
  <tbody>
    <tr>
      <td>GET</td><td>/</td>
      <td>
        Aggregated RITA trading dashboard payload.<br/>
        Query param: <code>alert_limit</code> (int, 1–200, default 20).
      </td>
      <td>200 <code>DashboardPayload</code></td>
    </tr>
  </tbody>
</table>

<h4>DashboardPayload schema</h4>
<pre>
{
  "positions":            list[Position],
  "latest_training_run":  TrainingRun | null,
  "recent_alerts":        list[Alert]   // sorted desc by timestamp, capped at alert_limit
}
</pre>

<h3>FnO — <code>/api/experience/fno</code></h3>
<table>
  <thead><tr><th>Method</th><th>Path</th><th>Description</th><th>Response</th></tr></thead>
  <tbody>
    <tr>
      <td>GET</td><td>/</td>
      <td>Aggregated FnO portfolio payload: latest snapshot + open positions + recent orders.</td>
      <td>200 <code>FnoPayload</code></td>
    </tr>
  </tbody>
</table>

<h4>FnoPayload schema</h4>
<pre>
{
  "latest_snapshot":  Snapshot | null,
  "positions":        list[Position],
  "recent_orders":    list[Order]
}
</pre>

<h3>Ops — <code>/api/experience/ops</code></h3>
<table>
  <thead><tr><th>Method</th><th>Path</th><th>Description</th><th>Response</th></tr></thead>
  <tbody>
    <tr>
      <td>GET</td><td>/</td>
      <td>Aggregated Ops payload: latest training run + latest backtest run + recent audit entries.</td>
      <td>200 <code>OpsPayload</code></td>
    </tr>
  </tbody>
</table>

<h4>OpsPayload schema</h4>
<pre>
{
  "latest_training_run":  TrainingRun | null,
  "latest_backtest_run":  BacktestRun | null,
  "recent_audit_entries": list[AuditEntry]
}
</pre>

<hr />

<h2>Common Patterns</h2>

<h3>Trace IDs</h3>
<p>
  Every request is assigned a UUID trace ID. It is returned in the
  <code>X-Request-ID</code> response header and included in all error response bodies:
</p>
<pre>
HTTP/1.1 404 Not Found
X-Request-ID: 3f2a1b9c-...

{"detail": "Position 'XYZ' not found", "trace_id": "3f2a1b9c-..."}
</pre>

<h3>Error Responses</h3>
<table>
  <thead><tr><th>Status</th><th>Trigger</th></tr></thead>
  <tbody>
    <tr><td>400</td><td>Request body fails Pydantic validation (<code>RequestValidationError</code>)</td></tr>
    <tr><td>404</td><td>Resource not found (returned by route handlers explicitly)</td></tr>
    <tr><td>422</td><td>Repository-level schema validation failure (<code>RepositoryValidationError</code>)</td></tr>
    <tr><td>500</td><td>Unhandled exception — details suppressed, trace ID included</td></tr>
  </tbody>
</table>

<h3>Authentication</h3>
<p>
  JWT authentication is configured in <code>config.yaml</code> (see
  <a href="Sprint 1: Security — JWT &amp; Secret Handling">Security Guide</a>).
  Sprint 2 routes are wired but token enforcement is enabled in Sprint 5
  (Security hardening day).
</p>
"""


if __name__ == "__main__":
    client = ConfluenceClient()

    if PAGE_ID:
        pid, url = client.update_page(PAGE_ID, PAGE_TITLE, PAGE_BODY)
        print(f"Updated: {PAGE_TITLE}")
    else:
        pid, url = client.create_page(PAGE_TITLE, PAGE_BODY, parent_id=SECTION["engineering"])
        print(f"Created: {PAGE_TITLE}")
        print(f'  PAGE_ID = "{pid}"')

    print(f"  URL: {url}")
