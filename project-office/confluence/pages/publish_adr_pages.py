"""
Day 3 — Publish ADR-001 and ADR-002 to Confluence Architecture section.
"""
import sys, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from confluence.publish import ConfluenceClient, SECTION

ADR001_TITLE = "ADR-001: Three-Tier API Design (Experience Layer / Business Process / System)"
ADR001_BODY = """
<h1>ADR-001: Three-Tier API Design</h1>
<p><strong>Sub-title:</strong> Experience Layer / Business Process / System</p>
<table><tbody>
  <tr><td><strong>Status</strong></td><td>Accepted</td></tr>
  <tr><td><strong>Date</strong></td><td>2026-03-30</td></tr>
  <tr><td><strong>Sprint</strong></td><td>0</td></tr>
</tbody></table>

<h2>Context</h2>
<p>The POC had a single monolithic <code>rest_api.py</code> (1,533 lines) mixing three concerns:</p>
<ul>
  <li>CRUD operations on individual CSV tables (positions, orders, snapshots)</li>
  <li>Business process logic for long-running jobs (train, backtest, evaluate)</li>
  <li>Aggregation of multiple data sources into UI-ready payloads</li>
</ul>
<p>This violates SRP, makes unit testing impossible without loading the entire app, and causes merge conflicts whenever more than one engineer touches the API layer.</p>

<h2>Decision</h2>
<p>Split all API routes into three tiers with strict rules about what each tier may do.</p>

<h3>Tier 1 &mdash; System (<code>api/v1/system/</code>)</h3>
<p>Pure CRUD for individual CSV table resources. No business logic. Direct repository calls only.</p>
<table><thead><tr><th>Router</th><th>Prefix</th><th>Responsibility</th></tr></thead><tbody>
  <tr><td>PositionsRouter</td><td>/api/v1/system/positions/</td><td>CRUD on position records</td></tr>
  <tr><td>OrdersRouter</td><td>/api/v1/system/orders/</td><td>CRUD on order records</td></tr>
  <tr><td>SnapshotsRouter</td><td>/api/v1/system/snapshots/</td><td>CRUD on snapshot records</td></tr>
</tbody></table>
<p><strong>Rule:</strong> A System router may call one repository only. Never a service or another router.</p>

<h3>Tier 2 &mdash; Business Process (<code>api/v1/workflow/</code>)</h3>
<p>Stateful workflows that orchestrate multiple services. Returns job status and results.</p>
<table><thead><tr><th>Router</th><th>Prefix</th><th>Responsibility</th></tr></thead><tbody>
  <tr><td>TrainRouter</td><td>/api/v1/workflow/train/</td><td>DQN model training runs</td></tr>
  <tr><td>BacktestRouter</td><td>/api/v1/workflow/backtest/</td><td>Backtest execution and results</td></tr>
  <tr><td>EvaluateRouter</td><td>/api/v1/workflow/evaluate/</td><td>Model evaluation against live or historical data</td></tr>
</tbody></table>
<p><strong>Rule:</strong> A Workflow router calls services only &mdash; never repositories directly, never Experience Layer routers.</p>

<h3>Tier 3 &mdash; Experience Layer (<code>api/experience/</code>)</h3>
<p>Composes data from System and Business Process tiers into a single UI-optimised payload per view. Shaped around what a specific screen needs, not the data model. No business logic, no writes.</p>
<table><thead><tr><th>Router</th><th>Prefix</th><th>Responsibility</th></tr></thead><tbody>
  <tr><td>DashboardExperience</td><td>/api/experience/dashboard/</td><td>Trading dashboard: positions + model state + alerts</td></tr>
  <tr><td>FnoExperience</td><td>/api/experience/fno/</td><td>FnO portfolio view: manoeuvres + Greeks + P&amp;L</td></tr>
  <tr><td>OpsExperience</td><td>/api/experience/ops/</td><td>Ops view: run history + metrics + health</td></tr>
</tbody></table>
<p><strong>Rule:</strong> An Experience Layer router calls System routers or services to compose responses. It must never write data or trigger side effects.</p>

<h2>Consequences</h2>
<p><strong>Positive:</strong></p>
<ul>
  <li>Single responsibility per tier &mdash; engineers work independently without conflicts.</li>
  <li>Clean unit tests: repositories and services testable in isolation.</li>
  <li>Experience Layer absorbs all N+1 query risk &mdash; one API call per UI view.</li>
  <li>Workflow tier replaceable with task queue (Celery/ARQ) in v2 without touching Experience Layer or System.</li>
  <li>Name communicates purpose: these routes serve a specific user experience.</li>
</ul>
<p><strong>Negative:</strong></p>
<ul>
  <li>More files than the POC monolith.</li>
  <li>Small features require touching multiple layers.</li>
</ul>

<h2>Alternatives Considered</h2>
<table><thead><tr><th>Option</th><th>Reason Rejected</th></tr></thead><tbody>
  <tr><td>Keep single rest_api.py</td><td>Same monolith problem &mdash; untestable, merge-conflict prone</td></tr>
  <tr><td>GraphQL</td><td>Team unfamiliar; overkill for v1</td></tr>
  <tr><td>Microservices</td><td>Premature for v1 CSV-backed system</td></tr>
  <tr><td>Name tier 3 "BFF"</td><td>Jargon; "Experience Layer" communicates purpose directly</td></tr>
</tbody></table>
"""

ADR002_TITLE = "ADR-002: Repository Pattern for CSV Data Access"
ADR002_BODY = """
<h1>ADR-002: Repository Pattern for CSV Data Access</h1>
<table><tbody>
  <tr><td><strong>Status</strong></td><td>Accepted</td></tr>
  <tr><td><strong>Date</strong></td><td>2026-03-30</td></tr>
  <tr><td><strong>Sprint</strong></td><td>0</td></tr>
</tbody></table>

<h2>Context</h2>
<p>The POC scattered <code>pd.read_csv()</code> and <code>df.to_csv()</code> calls throughout <code>rest_api.py</code> with no centralised access layer, no file locking, and no schema validation. This caused:</p>
<ul>
  <li><strong>Data corruption risk</strong> &mdash; concurrent requests could write to the same CSV simultaneously.</li>
  <li><strong>No schema enforcement</strong> &mdash; malformed rows propagated silently.</li>
  <li><strong>Untestable I/O</strong> &mdash; tests required real CSV files or pandas monkey-patching.</li>
  <li><strong>Tight coupling</strong> &mdash; PostgreSQL migration in v2 would require touching every caller.</li>
</ul>

<h2>Decision</h2>
<p>Implement a repository layer (<code>repositories/</code>): one class per CSV table, all I/O through these classes only.</p>

<h3>BaseRepository Interface</h3>
<pre>class BaseRepository(ABC, Generic[T]):
    def read_all(self) -&gt; list[T]: ...
    def write_all(self, records: list[T]) -&gt; None: ...
    def find_by_id(self, id: str) -&gt; Optional[T]: ...
    def upsert(self, record: T) -&gt; T: ...
    def delete(self, id: str) -&gt; bool: ...</pre>

<h3>File Locking</h3>
<p>Each repository holds a <code>threading.Lock</code>. All reads and writes acquire the lock. Prevents corruption under FastAPI concurrent request handling.</p>

<h3>Schema Validation</h3>
<p>All records validated through Pydantic models on every read and write. Failed validation raises <code>RepositoryValidationError</code> &mdash; never passes silently.</p>

<h3>v2 Migration Path</h3>
<p>Only the repository layer changes for PostgreSQL. Services, routes, and schemas untouched. Swap implementations via dependency injection.</p>

<h2>CSV Tables in Scope (v1) &mdash; 15 Tables</h2>
<table><thead><tr><th>Repository Class</th><th>CSV File</th><th>Primary Key</th></tr></thead><tbody>
  <tr><td>PositionsRepository</td><td>positions.csv</td><td>position_id</td></tr>
  <tr><td>OrdersRepository</td><td>orders.csv</td><td>order_id</td></tr>
  <tr><td>SnapshotsRepository</td><td>snapshots.csv</td><td>snapshot_id</td></tr>
  <tr><td>TradesRepository</td><td>trades.csv</td><td>trade_id</td></tr>
  <tr><td>PortfolioRepository</td><td>portfolio.csv</td><td>portfolio_id</td></tr>
  <tr><td>ManoeuvresRepository</td><td>manoeuvres.csv</td><td>manoeuvre_id</td></tr>
  <tr><td>BacktestRunsRepository</td><td>backtest_runs.csv</td><td>run_id</td></tr>
  <tr><td>BacktestResultsRepository</td><td>backtest_results.csv</td><td>result_id</td></tr>
  <tr><td>TrainingRunsRepository</td><td>training_runs.csv</td><td>run_id</td></tr>
  <tr><td>TrainingMetricsRepository</td><td>training_metrics.csv</td><td>metric_id</td></tr>
  <tr><td>ModelRegistryRepository</td><td>model_registry.csv</td><td>model_id</td></tr>
  <tr><td>AlertsRepository</td><td>alerts.csv</td><td>alert_id</td></tr>
  <tr><td>AuditLogRepository</td><td>audit_log.csv</td><td>log_id</td></tr>
  <tr><td>MarketDataCacheRepository</td><td>market_data_cache.csv</td><td>cache_id</td></tr>
  <tr><td>ConfigOverridesRepository</td><td>config_overrides.csv</td><td>override_id</td></tr>
</tbody></table>
<p><code>rita_input/</code> is <strong>read-only</strong> source data. All writes target <code>rita_output/</code>.</p>

<h2>Consequences</h2>
<p><strong>Positive:</strong></p>
<ul>
  <li>All data access is testable &mdash; repositories can be mocked or replaced with in-memory implementations.</li>
  <li>File locking prevents CSV corruption under concurrent load.</li>
  <li>Schema validation catches data quality issues at the boundary.</li>
  <li>v2 migration is mechanical &mdash; one new implementation class per table, zero route/service changes.</li>
</ul>
<p><strong>Negative:</strong></p>
<ul>
  <li>15 repository classes is more boilerplate than direct pandas calls.</li>
  <li>File locking adds latency on high-frequency writes (acceptable for v1).</li>
</ul>

<h2>Alternatives Considered</h2>
<table><thead><tr><th>Option</th><th>Reason Rejected</th></tr></thead><tbody>
  <tr><td>SQLAlchemy ORM on CSV</td><td>No CSV dialect; wrong abstraction for flat files</td></tr>
  <tr><td>Pandas-native access</td><td>No locking, no schema enforcement, untestable</td></tr>
  <tr><td>TinyDB / SQLite</td><td>Additional dependency; CSV is the agreed v1 storage format</td></tr>
</tbody></table>
"""

if __name__ == "__main__":
    client = ConfluenceClient()
    arch = SECTION["architecture"]

    id1, url1 = client.create_page(ADR001_TITLE, ADR001_BODY, parent_id=arch)
    print(f"ADR-001: [{id1}] {url1}")

    id2, url2 = client.create_page(ADR002_TITLE, ADR002_BODY, parent_id=arch)
    print(f"ADR-002: [{id2}] {url2}")
