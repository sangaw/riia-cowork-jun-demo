"""
Sprint 2.5 Day 15 — Publish ADR-003 (SQLite via SQLAlchemy) to Confluence Architecture section.

Run from the project root:
    CONFLUENCE_EMAIL=you@example.com python project-office/confluence/pages/publish_adr003.py
"""
import sys, os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Set default email if not provided (not a secret — same default used in all project scripts).
if not os.environ.get("CONFLUENCE_EMAIL"):
    os.environ["CONFLUENCE_EMAIL"] = "contact@ravionics.nl"

from confluence.publish import ConfluenceClient, SECTION

# In worktree mode the key file may live in the main repo root.
# Walk up from this script looking for confluence-api-key.txt.
if not os.environ.get("CONFLUENCE_API_TOKEN"):
    _here = Path(__file__).resolve()
    for _ancestor in _here.parents:
        _candidate = _ancestor / "confluence-api-key.txt"
        if _candidate.exists():
            os.environ["CONFLUENCE_API_TOKEN"] = _candidate.read_text().strip()
            break

TITLE = "ADR-003: SQLite via SQLAlchemy ORM for v1 Data Layer"

BODY = """
<h1>ADR-003: SQLite via SQLAlchemy ORM for v1 Data Layer</h1>
<table><tbody>
  <tr><td><strong>Status</strong></td><td>Accepted</td></tr>
  <tr><td><strong>Date</strong></td><td>2026-04-02</td></tr>
  <tr><td><strong>Sprint</strong></td><td>2.5</td></tr>
</tbody></table>

<h2>Context</h2>
<p>Sprint 2 completed the three-tier API over a CSV-backed repository layer. While the repository pattern (ADR-002) successfully isolated all data access, CSV has real operational constraints for a production trading system:</p>
<ul>
  <li>No atomic multi-row transactions &mdash; partial writes on crash corrupt state</li>
  <li>No query capability &mdash; list-all + Python filter is O(n) for every request</li>
  <li>No referential integrity &mdash; orphaned rows accumulate silently</li>
  <li>Concurrent write safety requires manual file locking (implemented, but fragile under load)</li>
  <li>No audit trail at the storage layer &mdash; only at the application layer</li>
</ul>
<p>The repository interface (<code>read_all</code>, <code>find_by_id</code>, <code>upsert</code>, <code>delete</code>) was deliberately designed to be storage-agnostic. Migrating the backend from CSV to SQL requires touching <strong>only the repository layer</strong> &mdash; zero changes to routers, services, or schemas.</p>

<h2>Decision</h2>
<p>Replace the CSV backend with <strong>SQLite</strong> via <strong>SQLAlchemy 2.x ORM</strong> for v1.</p>
<ul>
  <li><strong>SQLite</strong> &mdash; zero-infra, file-based, ACID-compliant. No Docker service needed. Ships as part of Python&rsquo;s stdlib. Perfect for a single-node v1 deployment.</li>
  <li><strong>SQLAlchemy 2.x</strong> &mdash; industry-standard ORM. Declarative models, session management, connection pooling. The same code runs against PostgreSQL by changing <code>database_url</code>.</li>
  <li><strong>Alembic</strong> &mdash; schema migration tool. Tracks all DDL changes. Required for production upgrades without data loss.</li>
</ul>

<h3>v1 &rarr; v2 upgrade path</h3>
<p>Change one config value:</p>
<pre>
# v1 (SQLite)
database_url = "sqlite:///./rita_output/rita.db"

# v2 (PostgreSQL &mdash; Sprint 5 or later)
database_url = "postgresql+asyncpg://user:pass@host/rita"
</pre>
<p>No application code changes required &mdash; SQLAlchemy&rsquo;s dialect layer handles the rest.</p>

<h2>Architecture</h2>

<h3>New files</h3>
<table><thead><tr><th>File</th><th>Purpose</th></tr></thead><tbody>
  <tr><td><code>src/rita/database.py</code></td><td>Engine, SessionLocal, Base, get_db() FastAPI dependency</td></tr>
  <tr><td><code>src/rita/models/__init__.py</code></td><td>Imports all 15 ORM model classes to register with Base.metadata</td></tr>
  <tr><td><code>src/rita/models/positions.py</code></td><td>PositionModel</td></tr>
  <tr><td><code>src/rita/models/orders.py</code></td><td>OrderModel</td></tr>
  <tr><td><code>src/rita/models/snapshots.py</code></td><td>SnapshotModel</td></tr>
  <tr><td><code>src/rita/models/trades.py</code></td><td>TradeModel</td></tr>
  <tr><td><code>src/rita/models/portfolio.py</code></td><td>PortfolioModel</td></tr>
  <tr><td><code>src/rita/models/manoeuvres.py</code></td><td>ManoeuvreModel</td></tr>
  <tr><td><code>src/rita/models/backtest.py</code></td><td>BacktestRunModel, BacktestResultModel</td></tr>
  <tr><td><code>src/rita/models/training.py</code></td><td>TrainingRunModel, TrainingMetricModel</td></tr>
  <tr><td><code>src/rita/models/model_registry.py</code></td><td>ModelRegistryModel</td></tr>
  <tr><td><code>src/rita/models/alerts.py</code></td><td>AlertModel</td></tr>
  <tr><td><code>src/rita/models/audit.py</code></td><td>AuditLogModel</td></tr>
  <tr><td><code>src/rita/models/market_data.py</code></td><td>MarketDataCacheModel</td></tr>
  <tr><td><code>src/rita/models/config_overrides.py</code></td><td>ConfigOverrideModel</td></tr>
  <tr><td><code>src/rita/models/risk.py</code></td><td>RiskTimelineModel</td></tr>
</tbody></table>

<h3>Modified files</h3>
<table><thead><tr><th>File</th><th>Change</th></tr></thead><tbody>
  <tr><td><code>src/rita/config.py</code></td><td>Add DatabaseSettings (database_url)</td></tr>
  <tr><td><code>src/rita/repositories/base.py</code></td><td>Rewrite: CsvRepository &rarr; SqlRepository[T, ModelT] (Day 16)</td></tr>
  <tr><td><code>src/rita/repositories/*.py</code></td><td>15 files: update inheritance, add model_class attr (Day 16)</td></tr>
  <tr><td><code>src/rita/main.py</code></td><td>Add lifespan: run alembic upgrade head on startup (Day 16)</td></tr>
  <tr><td><code>pyproject.toml</code></td><td>Add sqlalchemy&gt;=2.0, alembic&gt;=1.13</td></tr>
</tbody></table>

<h3>Repository base interface (unchanged externally)</h3>
<pre>
class SqlRepository(Generic[SchemaT, ModelT]):
    model_class: type[ModelT]      # SQLAlchemy ORM model
    schema_class: type[SchemaT]    # Pydantic schema (unchanged)

    def read_all(self) -&gt; list[SchemaT]: ...
    def find_by_id(self, id: str) -&gt; SchemaT | None: ...
    def upsert(self, record: SchemaT) -&gt; SchemaT: ...
    def delete(self, id: str) -&gt; bool: ...
</pre>
<p>Callers (routers, services) are <strong>unaffected</strong> &mdash; same method signatures, same return types.</p>

<h3>Session injection</h3>
<pre>
# database.py
def get_db() -&gt; Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# repositories/base.py
class SqlRepository(Generic[SchemaT, ModelT]):
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db
</pre>
<p>Replaces the current <code>threading.Lock</code> per-instance approach &mdash; SQLAlchemy handles session isolation per request.</p>

<h2>Consequences</h2>

<h3>Positive</h3>
<ul>
  <li>ACID transactions &mdash; no more partial-write corruption risk</li>
  <li>Single <code>database_url</code> change upgrades to PostgreSQL</li>
  <li>SQLAlchemy sessions handle concurrency &mdash; file locking code deleted</li>
  <li>Alembic gives a full DDL audit trail</li>
  <li>Tests use <code>sqlite:///:memory:</code> &mdash; zero setup, zero teardown, fast</li>
</ul>

<h3>Negative</h3>
<ul>
  <li>Adds two new dependencies (sqlalchemy, alembic) &mdash; ~8MB</li>
  <li>ORM models are a second representation of the data (alongside Pydantic schemas) &mdash; mitigated by keeping models minimal (columns only, no business logic)</li>
  <li>SQLite does not support <code>ALTER COLUMN</code> &mdash; schema changes require workarounds. Acceptable for v1; PostgreSQL removes this constraint in v2.</li>
</ul>

<h3>Neutral</h3>
<ul>
  <li>CSV files in <code>rita_input/</code> remain read-only source data for ML &mdash; not replaced</li>
  <li><code>rita_output/</code> now stores <code>rita.db</code> instead of CSV output files</li>
  <li>Model <code>.zip</code> files (stable-baselines3) unaffected</li>
</ul>

<h2>Alternatives Rejected</h2>
<table><thead><tr><th>Option</th><th>Reason rejected</th></tr></thead><tbody>
  <tr><td>Keep CSV</td><td>No transactions, file locking fragile under concurrent load</td></tr>
  <tr><td>PostgreSQL for v1</td><td>Requires Docker service, infra setup &mdash; too heavy for v1 single node</td></tr>
  <tr><td>TinyDB / shelve</td><td>Non-standard, no migration tooling, no PostgreSQL upgrade path</td></tr>
  <tr><td>Async SQLAlchemy</td><td>Adds complexity; sync is sufficient for current load profile; can migrate in Sprint 5</td></tr>
</tbody></table>
"""


def main():
    client = ConfluenceClient()
    parent_id = SECTION["architecture"]

    # Try create; if it fails with "title already exists" error, fall through to update.
    try:
        page_id, url = client.create_page(TITLE, BODY, parent_id=parent_id)
        print(f"CREATED: {TITLE}")
        print(f"  Page ID: {page_id}")
        print(f"  URL: {url}")
        return
    except RuntimeError as exc:
        err = str(exc)
        if "title" not in err.lower() and "already" not in err.lower() and "exist" not in err.lower():
            raise

    # Page already exists — find it by listing children of the architecture section.
    result, status = client._request(
        "GET",
        f"/content/{parent_id}/child/page?limit=50&expand=version",
    )
    if status != 200:
        raise RuntimeError(f"Could not list architecture children: HTTP {status}")
    existing = next((p for p in result.get("results", []) if p["title"] == TITLE), None)
    if not existing:
        raise RuntimeError(f"Page '{TITLE}' not found under architecture section after create failed.")
    page_id = existing["id"]
    _, url = client.update_page(page_id, TITLE, BODY)
    print(f"UPDATED: {TITLE}")
    print(f"  URL: {url}")


if __name__ == "__main__":
    main()
