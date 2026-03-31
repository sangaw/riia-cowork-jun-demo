"""
Publishes (or updates) the Sprint 2 board page under Sprint Boards in Confluence.
Run at end of each Sprint 2 day to reflect progress.

First run:  PAGE_ID = None  → creates the page, prints the ID → paste it below
Subsequent: PAGE_ID = "..."  → updates the existing page in-place
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from confluence.publish import ConfluenceClient, SECTION

TITLE = "Sprint 2 — API Decomposition"

# After first run, paste the returned page ID here so subsequent runs update in-place.
PAGE_ID = "65863715"

BODY = """
<h1>Sprint 2 &mdash; API Decomposition</h1>
<p><strong>Duration:</strong> Days 9&ndash;14 &nbsp;|&nbsp; <strong>Theme:</strong> Three-tier API fully wired — System CRUD, Business Process, Experience Layer, exception handling</p>

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
      <td>Day 9</td>
      <td>Engineer C</td>
      <td>System APIs (CRUD routers)</td>
      <td><strong style="color:#1a6b3c">&#10003; Done</strong></td>
      <td>8 CRUD routers under <code>api/v1/system/</code>: positions, orders, snapshots, trades, alerts, audit, market_data, config_overrides. Each router calls one repository only via <code>Depends()</code>. All wired into <code>main.py</code>.</td>
    </tr>
    <tr>
      <td>Day 10</td>
      <td>Engineer C</td>
      <td>Business Process API routers</td>
      <td>Pending</td>
      <td></td>
    </tr>
    <tr>
      <td>Day 11</td>
      <td>Engineer C</td>
      <td>BFF layer</td>
      <td>Pending</td>
      <td></td>
    </tr>
    <tr>
      <td>Day 12</td>
      <td>Engineer C</td>
      <td>Global exception handler, trace IDs</td>
      <td>Pending</td>
      <td></td>
    </tr>
    <tr>
      <td>Day 13</td>
      <td>QA</td>
      <td>API contract tests</td>
      <td>Pending</td>
      <td></td>
    </tr>
    <tr>
      <td>Day 14</td>
      <td>TechWriter</td>
      <td>Confluence: API Reference</td>
      <td>Pending</td>
      <td></td>
    </tr>
  </tbody>
</table>

<h2>Day 9 Deliverables &mdash; System CRUD Routers</h2>

<h3>Architecture (ADR-001 compliance)</h3>
<p>All eight routers live under <code>api/v1/system/</code> &mdash; the System tier per ADR-001.
Each router is restricted to calling <strong>one repository only</strong>; no service calls or cross-router calls are permitted at this tier.</p>

<h3>Routers Created</h3>
<table>
  <thead><tr><th>Router file</th><th>Prefix</th><th>ID field</th><th>Repository</th></tr></thead>
  <tbody>
    <tr><td><code>positions.py</code></td><td>/api/v1/system/positions</td><td>position_id</td><td>PositionsRepository</td></tr>
    <tr><td><code>orders.py</code></td><td>/api/v1/system/orders</td><td>order_id</td><td>OrdersRepository</td></tr>
    <tr><td><code>snapshots.py</code></td><td>/api/v1/system/snapshots</td><td>snapshot_id</td><td>SnapshotsRepository</td></tr>
    <tr><td><code>trades.py</code></td><td>/api/v1/system/trades</td><td>trade_id</td><td>TradesRepository</td></tr>
    <tr><td><code>alerts.py</code></td><td>/api/v1/system/alerts</td><td>alert_id</td><td>AlertsRepository</td></tr>
    <tr><td><code>audit.py</code></td><td>/api/v1/system/audit</td><td>log_id</td><td>AuditLogRepository</td></tr>
    <tr><td><code>market_data.py</code></td><td>/api/v1/system/market_data</td><td>cache_id</td><td>MarketDataCacheRepository</td></tr>
    <tr><td><code>config_overrides.py</code></td><td>/api/v1/system/config_overrides</td><td>override_id</td><td>ConfigOverridesRepository</td></tr>
  </tbody>
</table>

<h3>Endpoint Pattern (each router)</h3>
<ul>
  <li><code>GET  /api/v1/system/{table}/</code> &mdash; list all records</li>
  <li><code>GET  /api/v1/system/{table}/{id}</code> &mdash; get one record (404 if not found)</li>
  <li><code>PUT  /api/v1/system/{table}/{id}</code> &mdash; upsert record</li>
  <li><code>DELETE /api/v1/system/{table}/{id}</code> &mdash; delete record (404 if not found)</li>
</ul>
<p>Repository injected via FastAPI <code>Depends()</code> &mdash; never instantiated inline.</p>

<h2>Sprint 2 Definition of Done</h2>
<ul>
  <li>&#10003; 8 System CRUD routers wired and responding (Day 9)</li>
  <li>&#9744; Business Process routers for train, backtest, evaluate, manoeuvre (Day 10)</li>
  <li>&#9744; Experience Layer aggregation endpoints (Day 11)</li>
  <li>&#9744; Global exception handler + request trace IDs (Day 12)</li>
  <li>&#9744; API contract tests via FastAPI TestClient (Day 13)</li>
  <li>&#9744; Confluence API Reference published (Day 14)</li>
</ul>
"""


if __name__ == "__main__":
    client = ConfluenceClient()

    if PAGE_ID:
        page_id, url = client.update_page(PAGE_ID, TITLE, BODY)
        print(f"Sprint 2 board updated: {url}")
    else:
        page_id, url = client.create_page(TITLE, BODY, parent_id=SECTION["sprint_boards"])
        print(f"Sprint 2 board created: {url}")
        print(f"Page ID: {page_id}")
        print(f"\nPaste this into PAGE_ID at the top of this script for future updates:")
        print(f'PAGE_ID = "{page_id}"')
