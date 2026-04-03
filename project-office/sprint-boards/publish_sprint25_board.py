"""
Publishes (or updates) the Sprint 2.5 board page under Sprint Boards in Confluence.
Run at end of each Sprint 2.5 day to reflect progress.

First run:  PAGE_ID = None  → creates the page, prints the ID → paste it below
Subsequent: PAGE_ID = "..."  → updates the existing page in-place
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from confluence.publish import ConfluenceClient, SECTION

TITLE = "Sprint 2.5 — Database Layer"

# After first run, paste the returned page ID here so subsequent runs update in-place.
PAGE_ID = "66977794"

BODY = """
<h1>Sprint 2.5 &mdash; Database Layer</h1>
<p><strong>Duration:</strong> Days 15&ndash;18 &nbsp;|&nbsp; <strong>Theme:</strong> Replace CSV backend with SQLite via SQLAlchemy 2.x ORM &mdash; zero changes to routers, services, or schemas</p>

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
      <td>Day 15</td>
      <td>Engineer D</td>
      <td>SQLAlchemy setup: database.py, 15 ORM models, DatabaseSettings, ADR-003</td>
      <td><strong style="color:#1a6b3c">&#10003; Done</strong></td>
      <td>pyproject.toml: sqlalchemy&gt;=2.0, alembic&gt;=1.13. database.py: engine, SessionLocal, Base (DeclarativeBase), get_db() FastAPI dependency. 15 model files (17 classes — backtest + training have 2 tables each). DatabaseSettings added to config.py. ADR-003 published to Confluence [66650129].</td>
    </tr>
    <tr>
      <td>Day 16</td>
      <td>Engineer D</td>
      <td>Repository migration: rewrite base.py (SqlRepository), update all 15 concrete repos, update main.py lifespan</td>
      <td><strong style="color:#1a6b3c">&#10003; Done</strong></td>
      <td>SqlRepository[T,M] added to base.py (CsvRepository retained for Day 18 cleanup). 16 concrete repos migrated (incl. new risk.py). WorkflowService + BacktestService now accept db: Session. All 14 routers (8 system + 3 workflow + 3 experience) inject get_db(). main.py lifespan calls Base.metadata.create_all(engine). 78/78 API contract tests pass.</td>
    </tr>
    <tr>
      <td>Day 17</td>
      <td>Ops</td>
      <td>Alembic setup + CI update</td>
      <td><strong style="color:#1a6b3c">&#10003; Done</strong></td>
      <td>alembic init. env.py imports Base + all 17 ORM models; resolves sqlite:///./rita_output/rita.db to absolute path so upgrade works from any CWD. Migration file: 16 CREATE TABLE statements. alembic upgrade head + downgrade base verified. CI: alembic upgrade head step added before pytest. Dockerfile: runtime stage copies alembic/; CMD runs migrations before uvicorn.</td>
    </tr>
    <tr>
      <td>Day 18</td>
      <td>QA</td>
      <td>Test suite migration</td>
      <td><strong style="color:#b45309">&#9711; Planned</strong></td>
      <td>conftest.py: sqlite:///:memory: engine + session fixture + DI override; fix repo tests; verify 78 API contract tests still pass.</td>
    </tr>
  </tbody>
</table>

<h2>Day 15 Deliverables &mdash; SQLAlchemy Foundation</h2>

<h3>Decision (ADR-003)</h3>
<p>Replace the CSV-backed repository layer with SQLite via SQLAlchemy 2.x ORM.
Zero changes to routers, services, or Pydantic schemas &mdash; the repository interface is preserved.
PostgreSQL upgrade path in v2: change one <code>database_url</code> config value.</p>

<h3>New Files</h3>
<table>
  <thead><tr><th>File</th><th>Purpose</th></tr></thead>
  <tbody>
    <tr><td><code>src/rita/database.py</code></td><td>SQLAlchemy engine, SessionLocal factory, Base (DeclarativeBase), get_db() FastAPI dependency</td></tr>
    <tr><td><code>src/rita/models/__init__.py</code></td><td>Re-exports all 17 model classes; imports ensure tables register with Base.metadata</td></tr>
    <tr><td><code>src/rita/models/positions.py</code></td><td>Position ORM model</td></tr>
    <tr><td><code>src/rita/models/orders.py</code></td><td>Order ORM model</td></tr>
    <tr><td><code>src/rita/models/snapshots.py</code></td><td>PortfolioSnapshot ORM model</td></tr>
    <tr><td><code>src/rita/models/trades.py</code></td><td>Trade ORM model</td></tr>
    <tr><td><code>src/rita/models/alerts.py</code></td><td>Alert ORM model</td></tr>
    <tr><td><code>src/rita/models/audit.py</code></td><td>AuditLog ORM model</td></tr>
    <tr><td><code>src/rita/models/market_data.py</code></td><td>MarketDataCache ORM model</td></tr>
    <tr><td><code>src/rita/models/config_overrides.py</code></td><td>ConfigOverride ORM model</td></tr>
    <tr><td><code>src/rita/models/training.py</code></td><td>TrainingRun + TrainingMetrics ORM models (2 tables)</td></tr>
    <tr><td><code>src/rita/models/backtest.py</code></td><td>BacktestRun + BacktestDailyResult ORM models (2 tables)</td></tr>
    <tr><td><code>src/rita/models/manoeuvres.py</code></td><td>Manoeuvre ORM model</td></tr>
    <tr><td><code>src/rita/models/portfolio.py</code></td><td>PortfolioState ORM model</td></tr>
    <tr><td><code>src/rita/models/risk.py</code></td><td>RiskMetrics ORM model</td></tr>
    <tr><td><code>src/rita/models/model_registry.py</code></td><td>ModelRegistry ORM model</td></tr>
  </tbody>
</table>

<h3>Modified Files</h3>
<table>
  <thead><tr><th>File</th><th>Change</th></tr></thead>
  <tbody>
    <tr><td><code>pyproject.toml</code></td><td>Added <code>sqlalchemy&gt;=2.0</code> and <code>alembic&gt;=1.13</code> to dependencies</td></tr>
    <tr><td><code>src/rita/config.py</code></td><td>Added <code>DatabaseSettings</code> with <code>database_url</code> defaulting to <code>sqlite:///./rita.db</code></td></tr>
  </tbody>
</table>

<h3>Architecture Pattern (database.py)</h3>
<ul>
  <li><strong>Engine:</strong> <code>create_engine(settings.database_url)</code> &mdash; swap SQLite for PostgreSQL by changing one env var</li>
  <li><strong>SessionLocal:</strong> <code>sessionmaker(autocommit=False, autoflush=False)</code></li>
  <li><strong>Base:</strong> SQLAlchemy 2.x <code>DeclarativeBase</code> &mdash; all 17 models inherit from this</li>
  <li><strong>get_db():</strong> FastAPI dependency that yields a session and ensures <code>session.close()</code> on teardown</li>
</ul>

<h3>Model Count</h3>
<p>17 ORM model classes across 15 files. Two files contain 2 models each (parent + child tables):</p>
<ul>
  <li><code>training.py</code> &mdash; TrainingRun (job record) + TrainingMetrics (per-epoch stats)</li>
  <li><code>backtest.py</code> &mdash; BacktestRun (job record) + BacktestDailyResult (per-day P&amp;L)</li>
</ul>

<h2>Sprint 2.5 Definition of Done</h2>
<ul>
  <li>&#10003; SQLAlchemy engine, session, Base, get_db() in database.py (Day 15)</li>
  <li>&#10003; 17 ORM models mapping all 15 CSV tables (Day 15)</li>
  <li>&#10003; DatabaseSettings in config.py; sqlalchemy + alembic in pyproject.toml (Day 15)</li>
  <li>&#10003; ADR-003 published to Confluence (Day 15)</li>
  <li>&#10003; SqlRepository[T,M] base class added to base.py (Day 16)</li>
  <li>&#10003; 16 concrete repos migrated to SQLAlchemy sessions; services + 14 routers wired (Day 16)</li>
  <li>&#10003; Alembic init + 16-table migration; CI + Dockerfile updated (Day 17)</li>
  <li>&#9711; 78 API contract tests pass against in-memory SQLite (Day 18)</li>
</ul>
"""


if __name__ == "__main__":
    client = ConfluenceClient()

    if PAGE_ID:
        page_id, url = client.update_page(PAGE_ID, TITLE, BODY)
        print(f"Sprint 2.5 board updated: {url}")
    else:
        page_id, url = client.create_page(TITLE, BODY, parent_id=SECTION["sprint_boards"])
        print(f"Sprint 2.5 board created: {url}")
        print(f"Page ID: {page_id}")
        print(f"\nPaste this into PAGE_ID at the top of this script for future updates:")
        print(f'PAGE_ID = "{page_id}"')
