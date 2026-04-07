"""
Publishes the Repository & Database Layer architecture page to the Architecture section.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from confluence.publish import ConfluenceClient, SECTION

TITLE = "Repository & Database Layer"
PAGE_ID = "68911121"

BODY = """
<h2>1. Purpose</h2>
<p>
  The Repository &amp; Database Layer is the only place in RITA where data is read from or
  written to the database. No router, service, or core module accesses the database directly.
  This enforces ADR-002 (Repository Pattern) and makes the storage backend swappable without
  changing any application logic.
</p>

<h2>2. Component Map</h2>
<table>
  <thead>
    <tr>
      <th>Component</th>
      <th>Role</th>
      <th>Code File</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>SqlRepository (base)</strong></td>
      <td>Generic typed base class. Implements <code>get</code>, <code>list_all</code>, <code>upsert</code>, <code>delete</code>. All concrete repositories inherit from it. Requires a SQLAlchemy <code>Session</code> at construction.</td>
      <td><code>src/rita/repositories/base.py</code></td>
    </tr>
    <tr>
      <td><strong>Concrete Repositories (15)</strong></td>
      <td>One class per domain table. Each binds the generic base to a specific ORM model and Pydantic schema. No custom logic unless the domain requires it.</td>
      <td><code>src/rita/repositories/{positions, orders, snapshots, trades, alerts, audit, market_data, config_overrides, training, backtest, manoeuvres, portfolio, risk, model_registry}.py</code></td>
    </tr>
    <tr>
      <td><strong>ORM Models (15)</strong></td>
      <td>SQLAlchemy 2.x declarative models. Map Python classes to database tables. Registered with <code>Base.metadata</code> so Alembic can auto-generate migrations.</td>
      <td><code>src/rita/models/{same names}.py</code></td>
    </tr>
    <tr>
      <td><strong>Database Setup</strong></td>
      <td>Creates the SQLAlchemy engine, <code>SessionLocal</code> factory, and declarative <code>Base</code>. Exposes <code>get_db()</code> as a FastAPI dependency for request-scoped sessions.</td>
      <td><code>src/rita/database.py</code></td>
    </tr>
    <tr>
      <td><strong>Alembic Migrations</strong></td>
      <td>Version-controlled schema migrations. <code>env.py</code> imports all 15 ORM models so Alembic can diff and generate <code>CREATE TABLE</code> / <code>ALTER TABLE</code> scripts automatically.</td>
      <td><code>alembic/</code>, <code>alembic/versions/</code></td>
    </tr>
  </tbody>
</table>

<h2>3. Domain Table Map</h2>
<p>Each row is one data domain. The Repository and ORM Model share the same base name.</p>
<table>
  <thead>
    <tr>
      <th>Domain</th>
      <th>Table</th>
      <th>Repository</th>
      <th>Schema (Pydantic)</th>
      <th>Used by</th>
    </tr>
  </thead>
  <tbody>
    <tr><td>Positions</td><td>positions</td><td>PositionsRepository</td><td>Position</td><td>System CRUD router, DashboardRouter</td></tr>
    <tr><td>Orders</td><td>orders</td><td>OrdersRepository</td><td>Order</td><td>System CRUD router</td></tr>
    <tr><td>Snapshots</td><td>snapshots</td><td>SnapshotsRepository</td><td>Snapshot</td><td>System CRUD router, FnoRouter</td></tr>
    <tr><td>Trades</td><td>trades</td><td>TradesRepository</td><td>Trade</td><td>System CRUD router</td></tr>
    <tr><td>Alerts</td><td>alerts</td><td>AlertsRepository</td><td>Alert</td><td>System CRUD router, DashboardRouter</td></tr>
    <tr><td>Audit</td><td>audit</td><td>AuditRepository</td><td>AuditEntry</td><td>System CRUD router, OpsRouter</td></tr>
    <tr><td>Market Data</td><td>market_data</td><td>MarketDataRepository</td><td>MarketDataPoint</td><td>System CRUD router, DashboardRouter</td></tr>
    <tr><td>Config Overrides</td><td>config_overrides</td><td>ConfigOverridesRepository</td><td>ConfigOverride</td><td>System CRUD router</td></tr>
    <tr><td>Training Runs</td><td>training_runs</td><td>TrainingRunsRepository</td><td>TrainingRun</td><td>WorkflowService, OpsRouter</td></tr>
    <tr><td>Backtest Runs</td><td>backtest_runs</td><td>BacktestRunsRepository</td><td>BacktestRun</td><td>BacktestService, OpsRouter</td></tr>
    <tr><td>Manoeuvres</td><td>manoeuvres</td><td>ManoeuvresRepository</td><td>Manoeuvre</td><td>ManoeuvreService, FnoRouter</td></tr>
    <tr><td>Portfolio</td><td>portfolio</td><td>PortfolioRepository</td><td>PortfolioEntry</td><td>PortfolioService, FnoRouter</td></tr>
    <tr><td>Risk</td><td>risk</td><td>RiskRepository</td><td>RiskEntry</td><td>DashboardRouter</td></tr>
    <tr><td>Model Registry</td><td>model_registry</td><td>ModelRegistryRepository</td><td>ModelRegistryEntry</td><td>WorkflowService, DashboardRouter</td></tr>
  </tbody>
</table>

<h2>4. Session Lifecycle Rules</h2>
<p>
  RITA follows strict session ownership rules to keep transactions correct and avoid
  cross-thread contamination.
</p>
<table>
  <thead><tr><th>Context</th><th>How a session is obtained</th><th>Why</th></tr></thead>
  <tbody>
    <tr>
      <td><strong>HTTP request</strong></td>
      <td><code>get_db()</code> FastAPI dependency &mdash; yields a session, closes it after response.</td>
      <td>Request-scoped. One transaction per request. Automatically closed on error or response.</td>
    </tr>
    <tr>
      <td><strong>Background thread</strong></td>
      <td><code>SessionLocal()</code> called inside the thread. Closed in a <code>finally</code> block.</td>
      <td>SQLAlchemy sessions are not thread-safe. The request session must never be passed into a thread.</td>
    </tr>
    <tr>
      <td><strong>Startup (table creation)</strong></td>
      <td><code>Base.metadata.create_all(bind=engine)</code> in FastAPI lifespan handler.</td>
      <td>Ensures all tables exist before the first request. Idempotent &mdash; safe to run on every start.</td>
    </tr>
  </tbody>
</table>

<h2>5. Alembic Workflow</h2>
<table>
  <thead><tr><th>Command</th><th>Purpose</th></tr></thead>
  <tbody>
    <tr><td><code>alembic upgrade head</code></td><td>Apply all pending migrations to the database. Run automatically by Dockerfile CMD and CI pipeline before tests.</td></tr>
    <tr><td><code>alembic revision --autogenerate -m "description"</code></td><td>Generate a new migration by diffing ORM models against the current schema.</td></tr>
    <tr><td><code>alembic downgrade base</code></td><td>Roll back all migrations to empty schema (useful for local reset).</td></tr>
  </tbody>
</table>

<h2>6. PostgreSQL Upgrade Path (v2)</h2>
<p>
  Zero code changes are required to move from SQLite to PostgreSQL. The only change needed is
  the <code>database_url</code> configuration value, either in <code>config/production.yaml</code>
  or via the <code>RITA_DATABASE_URL</code> environment variable:
</p>
<p>
  <strong>v1 (SQLite):</strong> <code>sqlite:///./rita_output/rita.db</code><br/>
  <strong>v2 (PostgreSQL):</strong> <code>postgresql+psycopg2://user:password@host:5432/rita</code>
</p>
<p>
  Alembic migrations are written using SQLAlchemy-neutral constructs and will execute
  correctly against both backends.
</p>
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
