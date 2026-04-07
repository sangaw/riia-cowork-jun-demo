"""
Publishes the Service Layer & Business Logic architecture page to the Architecture section.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from confluence.publish import ConfluenceClient, SECTION

TITLE = "Service Layer & Business Logic"
PAGE_ID = "68911136"

BODY = """
<h2>1. Purpose</h2>
<p>
  The Service Layer contains all business logic that spans more than one repository or requires
  coordination between data access and background computation. Routers are kept thin &mdash; they
  validate input, call a service, and return the result. Services own the &ldquo;what happens&rdquo;.
</p>
<p>
  All service classes accept a SQLAlchemy <code>Session</code> at construction and instantiate
  their own repositories from it. They never share sessions across thread boundaries.
</p>

<h2>2. Service Components</h2>
<table>
  <thead>
    <tr>
      <th>Service</th>
      <th>Responsibility</th>
      <th>Key Operations</th>
      <th>Code File</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>WorkflowService</strong></td>
      <td>Manages the full lifecycle of a model training job. Creates a pending record, dispatches a daemon thread that runs the ML process, then transitions the record to <code>running</code> &rarr; <code>complete</code> / <code>failed</code>.</td>
      <td>submit_training_run, get_run_status</td>
      <td><code>src/rita/services/workflow_service.py</code></td>
    </tr>
    <tr>
      <td><strong>BacktestService</strong></td>
      <td>Same lifecycle pattern as WorkflowService but for backtest jobs. Dispatches a separate backtest computation thread. Results written back to BacktestRunsRepository on completion.</td>
      <td>submit_backtest, get_backtest_status</td>
      <td><code>src/rita/services/backtest_service.py</code></td>
    </tr>
    <tr>
      <td><strong>ManoeuvreService</strong></td>
      <td>Records FnO trading manoeuvres (hedges, adjustments). Provides filtered queries: all manoeuvres, recent manoeuvres, manoeuvres by date.</td>
      <td>record, list_all, list_recent, list_by_date</td>
      <td><code>src/rita/services/manoeuvre_service.py</code></td>
    </tr>
    <tr>
      <td><strong>PortfolioService</strong></td>
      <td>Records daily portfolio snapshots and retrieves them for the FnO dashboard. Provides point-in-time lookups and latest-value queries.</td>
      <td>record, list_all, get_by_date, get_latest</td>
      <td><code>src/rita/services/portfolio_service.py</code></td>
    </tr>
  </tbody>
</table>

<h2>3. Core Computation Modules</h2>
<p>
  The <code>core/</code> directory holds pure computation logic with no FastAPI or SQLAlchemy
  dependencies. These modules are stateless and testable in isolation.
</p>
<table>
  <thead>
    <tr>
      <th>Module</th>
      <th>Responsibility</th>
      <th>Code File</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>ML Dispatch</strong></td>
      <td>Stub for the Double DQN training process (stable-baselines3). Opens its own database session, transitions the training run through <code>running</code> &rarr; <code>complete/failed</code>, writes results. Runs inside a daemon thread launched by WorkflowService.</td>
      <td><code>src/rita/core/ml_dispatch.py</code></td>
    </tr>
    <tr>
      <td><strong>Backtest Dispatch</strong></td>
      <td>Stub for the backtest computation. Same thread-and-session pattern as ML Dispatch. Writes results to BacktestRunsRepository on completion.</td>
      <td><code>src/rita/core/backtest_dispatch.py</code></td>
    </tr>
  </tbody>
</table>

<h2>4. Job Lifecycle &mdash; Training &amp; Backtest Runs</h2>
<p>Both WorkflowService and BacktestService follow the same four-state lifecycle.</p>
<table>
  <thead><tr><th>State</th><th>When set</th><th>Who sets it</th></tr></thead>
  <tbody>
    <tr><td><strong>pending</strong></td><td>Immediately on job submission, before the thread starts</td><td>WorkflowService / BacktestService (request thread)</td></tr>
    <tr><td><strong>running</strong></td><td>First action inside the daemon thread</td><td>ml_dispatch / backtest_dispatch (background thread)</td></tr>
    <tr><td><strong>complete</strong></td><td>On successful completion of the computation</td><td>ml_dispatch / backtest_dispatch (background thread)</td></tr>
    <tr><td><strong>failed</strong></td><td>On any unhandled exception inside the thread</td><td>ml_dispatch / backtest_dispatch (background thread)</td></tr>
  </tbody>
</table>
<p>
  The HTTP response is returned immediately after setting <code>status=pending</code>. The caller
  polls <code>GET /api/v1/observability/step-log</code> to track progress.
</p>

<h2>5. FnO Domain: Instruments &amp; Greeks</h2>
<p>
  FnO-specific business rules are enforced in configuration, not hardcoded.
</p>
<table>
  <thead><tr><th>Rule</th><th>Value</th><th>Where configured</th></tr></thead>
  <tbody>
    <tr><td>NIFTY lot size</td><td>75 (changed from 50 in 2024)</td><td><code>config/base.yaml</code> &rarr; <code>instruments.nifty.lot_size</code></td></tr>
    <tr><td>BANKNIFTY lot size</td><td>30</td><td><code>config/base.yaml</code> &rarr; <code>instruments.banknifty.lot_size</code></td></tr>
    <tr><td>Greeks model</td><td>Black-Scholes (Delta, Gamma, Theta, Vega)</td><td>Computed in <code>core/</code>; reference tests in <code>tests/unit/test_greeks.py</code></td></tr>
  </tbody>
</table>
<p>
  <strong>Rule:</strong> Lot sizes must never be hardcoded in service or router code. Any change
  to lot sizes requires only a YAML config update, not a code change.
</p>

<h2>6. Dependency Injection Pattern</h2>
<p>
  All services are instantiated per-request via FastAPI dependency injection. This ensures each
  request gets a fresh service bound to its own database session.
</p>
<table>
  <thead><tr><th>Layer</th><th>Pattern</th></tr></thead>
  <tbody>
    <tr>
      <td>Router &rarr; Service</td>
      <td>Router defines a <code>get_&lt;service&gt;(db: Session = Depends(get_db))</code> function and passes it to the endpoint via <code>Depends()</code>.</td>
    </tr>
    <tr>
      <td>Service &rarr; Repository</td>
      <td>Service <code>__init__</code> receives <code>db: Session</code> and constructs its repositories directly: <code>self._repo = MyRepository(db)</code>.</td>
    </tr>
    <tr>
      <td>Background thread</td>
      <td>Thread function calls <code>SessionLocal()</code> to open its own session. Closes it in a <code>finally</code> block. Never receives the request session.</td>
    </tr>
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
