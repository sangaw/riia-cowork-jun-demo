"""
Publishes the System Architecture Overview page to the Architecture section.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from confluence.publish import ConfluenceClient, SECTION

TITLE = "System Architecture Overview"
PAGE_ID = "68911105"

BODY = """
<h2>1. Purpose</h2>
<p>
  This page describes the high-level component structure of RITA. It is intended for engineers
  and reviewers who need to understand how the system is organised without reading source code.
  For language-level detail, follow the links to component pages in the Engineering section.
</p>

<h2>2. Component Layers</h2>
<p>RITA is structured as five distinct layers. Each layer has a single responsibility and communicates
only with the layer directly below it.</p>

<table>
  <thead>
    <tr>
      <th>#</th>
      <th>Layer</th>
      <th>Responsibility</th>
      <th>Key Components</th>
      <th>Code Location</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>1</td>
      <td><strong>Dashboard UI</strong></td>
      <td>Browser-based operator interface. Three dashboards: RITA (model monitoring), FnO (portfolio), Ops (system health). Reads from the Experience Layer via fetch.</td>
      <td>rita.html, fno.html, ops.html &mdash; each backed by ~12&ndash;21 ES modules</td>
      <td><code>dashboard/js/{rita,fno,ops}/</code></td>
    </tr>
    <tr>
      <td>2</td>
      <td><strong>Experience Layer</strong> (BFF)</td>
      <td>Aggregates data from multiple System CRUD endpoints into a single UI-shaped payload per dashboard. Read-only. No business logic.</td>
      <td>DashboardRouter, FnoRouter, OpsRouter</td>
      <td><code>src/rita/api/experience/</code></td>
    </tr>
    <tr>
      <td>3</td>
      <td><strong>Workflow Layer</strong></td>
      <td>Business process endpoints. Accepts job submissions (train, backtest, evaluate). Writes a pending record, dispatches background work, returns immediately. Protected by JWT auth.</td>
      <td>TrainRouter, BacktestRouter, EvaluateRouter</td>
      <td><code>src/rita/api/v1/workflow/</code></td>
    </tr>
    <tr>
      <td>4</td>
      <td><strong>System CRUD Layer</strong></td>
      <td>Pure CRUD routers. One router per data table. No business logic &mdash; delegates immediately to the repository layer.</td>
      <td>PositionsRouter, OrdersRouter, SnapshotsRouter, TradesRouter, AlertsRouter, AuditRouter, MarketDataRouter, ConfigOverridesRouter</td>
      <td><code>src/rita/api/v1/system/</code></td>
    </tr>
    <tr>
      <td>5</td>
      <td><strong>Repository &amp; Database Layer</strong></td>
      <td>All data access. One repository class per ORM model. SQLAlchemy 2.x ORM over SQLite (v1) / PostgreSQL (v2). Schema validation on every read and write.</td>
      <td>SqlRepository (base), 15 concrete repositories, 15 ORM models, Alembic migrations</td>
      <td><code>src/rita/repositories/</code>, <code>src/rita/models/</code></td>
    </tr>
  </tbody>
</table>

<h2>3. Cross-Cutting Components</h2>
<p>These components serve all five layers.</p>

<table>
  <thead>
    <tr>
      <th>Component</th>
      <th>Responsibility</th>
      <th>Code File</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>Configuration</strong></td>
      <td>Pydantic Settings loaded from YAML hierarchy (base &rarr; environment) with env-var overrides. Single cached singleton. Covers app, server, data paths, security, database, instruments.</td>
      <td><code>src/rita/config.py</code></td>
    </tr>
    <tr>
      <td><strong>Security</strong></td>
      <td>JWT authentication (python-jose, HS256). CORS via CORSMiddleware. Rate limiting via slowapi (60/min global, 10/min on auth endpoint). Field-level input validation via Pydantic constraints.</td>
      <td><code>src/rita/auth.py</code>, <code>src/rita/limiter.py</code>, <code>src/rita/api/v1/auth.py</code></td>
    </tr>
    <tr>
      <td><strong>Observability</strong></td>
      <td>Structured JSON logging (structlog). Prometheus metrics at <code>GET /metrics</code>. Liveness probe at <code>GET /health</code>. Readiness probe at <code>GET /readyz</code> (SELECT 1).</td>
      <td><code>src/rita/logging_config.py</code>, <code>src/rita/metrics.py</code></td>
    </tr>
    <tr>
      <td><strong>Request Tracing</strong></td>
      <td>Every request gets a <code>X-Request-ID</code> trace ID injected by middleware. Trace ID is bound to every log line for the duration of the request.</td>
      <td><code>src/rita/middleware.py</code></td>
    </tr>
    <tr>
      <td><strong>Exception Handling</strong></td>
      <td>Consistent JSON error shape <code>{detail, trace_id}</code> across all error types: HTTP exceptions, request validation errors, repository validation errors, unhandled exceptions (500).</td>
      <td><code>src/rita/exception_handlers.py</code></td>
    </tr>
    <tr>
      <td><strong>Schemas</strong></td>
      <td>Pydantic data contracts. One schema file per table. Enforces types, field constraints, and business rules at the API boundary. Decoupled from ORM models.</td>
      <td><code>src/rita/schemas/</code> (15 files)</td>
    </tr>
  </tbody>
</table>

<h2>4. Request Flow &mdash; Example: Submit a Training Job</h2>
<p>Illustrates how a training request travels through all five layers.</p>

<table>
  <thead><tr><th>Step</th><th>Layer</th><th>Component</th><th>Action</th></tr></thead>
  <tbody>
    <tr><td>1</td><td>Dashboard UI</td><td>ops.html / <code>training.js</code></td><td>Operator clicks &ldquo;Train&rdquo;. JS posts to <code>POST /api/v1/workflow/train</code> with JWT Bearer token.</td></tr>
    <tr><td>2</td><td>Security</td><td><code>get_current_user</code></td><td>FastAPI validates JWT. Rejects with 401 if missing or expired.</td></tr>
    <tr><td>3</td><td>Workflow Layer</td><td>TrainRouter &rarr; WorkflowService</td><td>Router delegates to WorkflowService. Service creates a TrainingRun record with <code>status=pending</code> via TrainingRunsRepository.</td></tr>
    <tr><td>4</td><td>Repository Layer</td><td>TrainingRunsRepository &rarr; SQLite</td><td>Repository upserts the record. Commits the transaction.</td></tr>
    <tr><td>5</td><td>Workflow Layer</td><td>WorkflowService &rarr; ml_dispatch</td><td>Service launches a daemon thread. Thread opens its own DB session. Transitions run to <code>running</code>, executes ML dispatch stub, then <code>complete</code> or <code>failed</code>.</td></tr>
    <tr><td>6</td><td>Workflow Layer</td><td>TrainRouter</td><td>Returns HTTP 202 with <code>{run_id, status: &ldquo;pending&rdquo;}</code> immediately (does not wait for thread).</td></tr>
    <tr><td>7</td><td>Dashboard UI</td><td>ops.html / <code>observability.js</code></td><td>Ops dashboard polls <code>GET /api/v1/observability/step-log</code> to display live run status.</td></tr>
  </tbody>
</table>

<h2>5. Technology Stack</h2>
<table>
  <thead><tr><th>Concern</th><th>Library / Tool</th><th>Version</th></tr></thead>
  <tbody>
    <tr><td>API framework</td><td>FastAPI</td><td>&ge;0.111</td></tr>
    <tr><td>ASGI server</td><td>Uvicorn</td><td>&ge;0.29</td></tr>
    <tr><td>Data validation</td><td>Pydantic v2 + pydantic-settings</td><td>&ge;2.7 / &ge;2.3</td></tr>
    <tr><td>ORM</td><td>SQLAlchemy 2.x</td><td>&ge;2.0</td></tr>
    <tr><td>Migrations</td><td>Alembic</td><td>&ge;1.13</td></tr>
    <tr><td>Database (v1)</td><td>SQLite (file: <code>rita_output/rita.db</code>)</td><td>&mdash;</td></tr>
    <tr><td>Database (v2)</td><td>PostgreSQL (change one <code>database_url</code> config value)</td><td>&mdash;</td></tr>
    <tr><td>Authentication</td><td>python-jose[cryptography] + slowapi</td><td>&ge;3.3 / &ge;0.1.9</td></tr>
    <tr><td>Logging</td><td>structlog (JSON output)</td><td>&ge;24.1</td></tr>
    <tr><td>Metrics</td><td>prometheus-fastapi-instrumentator</td><td>&ge;6.1</td></tr>
    <tr><td>ML model</td><td>stable-baselines3 (Double DQN, .zip format)</td><td>&ge;2.3</td></tr>
    <tr><td>Containerisation</td><td>Docker (multi-stage: builder + runtime non-root)</td><td>&mdash;</td></tr>
    <tr><td>CI</td><td>GitHub Actions (lint &rarr; test &rarr; alembic &rarr; docker-build &rarr; e2e)</td><td>&mdash;</td></tr>
  </tbody>
</table>

<h2>6. Key Design Decisions</h2>
<p>See the Architecture section for full ADR text.</p>
<table>
  <thead><tr><th>ADR</th><th>Decision</th><th>Rationale</th></tr></thead>
  <tbody>
    <tr><td>ADR-001</td><td>Three-tier API (Experience / Workflow / System)</td><td>Keeps UI-shaped aggregation separate from business logic and pure CRUD. Enables independent evolution of each tier.</td></tr>
    <tr><td>ADR-002</td><td>Repository pattern for all data access</td><td>No direct DB calls in routers or services. Enables backend swap (CSV &rarr; SQLite &rarr; PostgreSQL) without touching business logic.</td></tr>
    <tr><td>ADR-003</td><td>SQLite via SQLAlchemy 2.x ORM</td><td>Cloud-native stateless API. Single <code>database_url</code> config value separates v1 (SQLite) from v2 (PostgreSQL).</td></tr>
  </tbody>
</table>
"""

if __name__ == "__main__":
    client = ConfluenceClient()
    if PAGE_ID:
        page_id, url = client.update_page(PAGE_ID, TITLE, BODY)
        print(f"Updated: {url}")
    else:
        page_id, url = client.create_page(TITLE, BODY, parent_id=SECTION["architecture"])
        print(f"Created: {url}")
        print(f'PAGE_ID = "{page_id}"')
