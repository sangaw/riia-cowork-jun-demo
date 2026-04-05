"""
Publishes (or updates) the Sprint 3 board page under Sprint Boards in Confluence.
Run at end of each Sprint 3 day to reflect progress.

First run:  PAGE_ID = None  → creates the page, prints the ID → paste it below
Subsequent: PAGE_ID = "..."  → updates the existing page in-place
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from confluence.publish import ConfluenceClient, SECTION

TITLE = "Sprint 3 — Service Layer & Observability"

# After first run, paste the returned page ID here so subsequent runs update in-place.
PAGE_ID = "67862529"

BODY = """
<h1>Sprint 3 &mdash; Service Layer &amp; Observability</h1>
<p><strong>Duration:</strong> Days 19&ndash;24 &nbsp;|&nbsp; <strong>Theme:</strong> Complete business-logic service layer, structured JSON logging, Prometheus metrics, probe endpoints, and full QA coverage</p>

<table>
  <thead>
    <tr>
      <th>Day</th>
      <th>Role</th>
      <th>Task</th>
      <th>Status</th>
      <th>Notes</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Day 19</td>
      <td>Engineer D</td>
      <td>WorkflowService, BacktestService (real ML dispatch stubs)</td>
      <td><strong style="color:#1a6b3c">&#10003; Done</strong></td>
      <td>core/ml_dispatch.py + core/backtest_dispatch.py. Daemon threads via SessionLocal; pending&rarr;running&rarr;complete/failed transitions. Episode metrics + daily backtest results persisted. 96/97 tests pass.</td>
    </tr>
    <tr>
      <td>Day 20</td>
      <td>Engineer D</td>
      <td>ManoeuvreService, PortfolioService</td>
      <td><strong style="color:#1a6b3c">&#10003; Done</strong></td>
      <td>ManoeuvreService (record/list_all/list_recent/list_by_date) + PortfolioService (record/list_all/get_by_date/get_latest). FnO experience router updated to inject services via Depends &mdash; ADR-001 compliance restored. 96/97 tests pass.</td>
    </tr>
    <tr>
      <td>Day 21</td>
      <td>Engineer E</td>
      <td>structlog JSON logging throughout</td>
      <td><strong style="color:#1a6b3c">&#10003; Done</strong></td>
      <td>logging_config.py created. TraceIDMiddleware binds trace_id. Exception handlers log errors. WorkflowService + BacktestService log job transitions. 96/97 tests pass.</td>
    </tr>
    <tr>
      <td>Day 22</td>
      <td>Engineer E</td>
      <td>Prometheus metrics, /health, /readyz</td>
      <td><strong style="color:#1a6b3c">&#10003; Done</strong></td>
      <td>prometheus-fastapi-instrumentator&gt;=6.1 added. metrics.py: instrument_app() wires Instrumentator, exposes GET /metrics, excludes /metrics+/health+/readyz from tracking. /health: liveness probe (no DB check). /readyz: readiness probe (SELECT 1 via SQLAlchemy engine; HTTP 503 + structlog warning on failure). 11 pre-existing ruff F401 warnings fixed. 96/97 tests pass.</td>
    </tr>
    <tr>
      <td>Day 23</td>
      <td>QA</td>
      <td>Greeks tests, manoeuvre tests, workflow integration</td>
      <td><strong style="color:#92480a">&#9679; Planned</strong></td>
      <td></td>
    </tr>
    <tr>
      <td>Day 24</td>
      <td>TechWriter</td>
      <td>Confluence: Observability &amp; Runbook</td>
      <td><strong style="color:#92480a">&#9679; Planned</strong></td>
      <td></td>
    </tr>
  </tbody>
</table>

<h2>Day 22 Deliverables &mdash; Prometheus Metrics &amp; Health Probes</h2>

<h3>New Files</h3>
<table>
  <thead><tr><th>File</th><th>Purpose</th></tr></thead>
  <tbody>
    <tr><td><code>src/rita/metrics.py</code></td><td>instrument_app(app: FastAPI) &mdash; wires prometheus-fastapi-instrumentator; exposes GET /metrics; excludes probe paths from tracking</td></tr>
  </tbody>
</table>

<h3>Modified Files</h3>
<table>
  <thead><tr><th>File</th><th>Change</th></tr></thead>
  <tbody>
    <tr><td><code>pyproject.toml</code></td><td>Added <code>prometheus-fastapi-instrumentator&gt;=6.1</code></td></tr>
    <tr><td><code>src/rita/main.py</code></td><td>Imported instrument_app; replaced bare /health with liveness probe; added /readyz readiness probe (SELECT 1, HTTP 503 on failure); instrument_app(app) called after all routers</td></tr>
  </tbody>
</table>

<h3>Endpoint Behaviour</h3>
<ul>
  <li><strong>GET /metrics</strong> &mdash; Prometheus scrape endpoint; exposes standard HTTP request histogram (method, path, status, duration). Excluded from its own tracking.</li>
  <li><strong>GET /health</strong> &mdash; Liveness probe. Returns HTTP 200 <code>{"status": "ok", "version": "..."}</code> as long as the process is alive. No DB check &mdash; liveness must not fail due to storage issues.</li>
  <li><strong>GET /readyz</strong> &mdash; Readiness probe. Executes <code>SELECT 1</code> via SQLAlchemy engine. Returns HTTP 200 <code>{"status": "ready"}</code> on success or HTTP 503 <code>{"status": "unavailable", "detail": "..."}</code> on DB failure; logs a warning via structlog.</li>
</ul>

<h2>Day 21 Deliverables &mdash; structlog JSON Logging</h2>

<h3>New Files</h3>
<table>
  <thead><tr><th>File</th><th>Purpose</th></tr></thead>
  <tbody>
    <tr><td><code>src/rita/logging_config.py</code></td><td>configure_logging() &mdash; sets up structlog with JSON renderer for production, ConsoleRenderer for dev; called in main.py lifespan</td></tr>
  </tbody>
</table>

<h3>Logging Integration Points</h3>
<ul>
  <li><strong>Middleware:</strong> TraceIDMiddleware binds <code>trace_id</code> to every log line via structlog contextvars</li>
  <li><strong>Exception handlers:</strong> All 4 handlers (HTTP, validation, repository, unhandled) log with structlog</li>
  <li><strong>WorkflowService:</strong> Logs job state transitions (pending&rarr;running&rarr;complete/failed)</li>
  <li><strong>BacktestService:</strong> Logs job state transitions and episode metrics</li>
</ul>

<h2>Day 20 Deliverables &mdash; ManoeuvreService &amp; PortfolioService</h2>
<ul>
  <li><strong>ManoeuvreService:</strong> record(db, data), list_all(db), list_recent(db, n), list_by_date(db, date)</li>
  <li><strong>PortfolioService:</strong> record(db, data), list_all(db), get_by_date(db, date), get_latest(db)</li>
  <li><strong>FnO router fixed:</strong> Depends() injection of ManoeuvreService + PortfolioService &mdash; ADR-001 three-tier compliance restored</li>
</ul>

<h2>Day 19 Deliverables &mdash; ML Dispatch Stubs</h2>
<ul>
  <li><strong>core/ml_dispatch.py:</strong> _run_training_job(run_id) &mdash; daemon thread; opens own SessionLocal; transitions pending&rarr;running&rarr;complete/failed</li>
  <li><strong>core/backtest_dispatch.py:</strong> _run_backtest_job(run_id) &mdash; same pattern; persists daily backtest results</li>
  <li><strong>WorkflowService + BacktestService:</strong> updated to dispatch to real stubs</li>
</ul>

<h2>Sprint 3 Definition of Done</h2>
<ul>
  <li>&#10003; WorkflowService + BacktestService with ML dispatch (Day 19)</li>
  <li>&#10003; ManoeuvreService + PortfolioService (Day 20)</li>
  <li>&#10003; structlog JSON logging throughout (Day 21)</li>
  <li>&#10003; Prometheus /metrics + /health + /readyz (Day 22)</li>
  <li>&#9675; Greeks reference tests + manoeuvre + workflow integration tests (Day 23)</li>
  <li>&#9675; Confluence Observability &amp; Runbook page (Day 24)</li>
</ul>
"""


if __name__ == "__main__":
    client = ConfluenceClient()

    if PAGE_ID:
        page_id, url = client.update_page(PAGE_ID, TITLE, BODY)
        print(f"Sprint 3 board updated: {url}")
    else:
        page_id, url = client.create_page(TITLE, BODY, parent_id=SECTION["sprint_boards"])
        print(f"Sprint 3 board created: {url}")
        print(f"Page ID: {page_id}")
        print(f"\nPaste this into PAGE_ID at the top of this script for future updates:")
        print(f'PAGE_ID = "{page_id}"')
