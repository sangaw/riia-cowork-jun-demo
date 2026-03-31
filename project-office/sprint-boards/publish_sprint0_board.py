"""
Publishes (or updates) the Sprint 0 board page under Sprint Boards in Confluence.
Run at end of each Sprint 0 day to reflect progress.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from confluence.publish import ConfluenceClient, SECTION

TITLE = "Sprint 0 — Architecture & Planning"

BODY = """
<h1>Sprint 0 &mdash; Architecture &amp; Planning</h1>
<p><strong>Duration:</strong> Days 1&ndash;3 &nbsp;|&nbsp; <strong>Theme:</strong> Design foundations before any code</p>

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
      <td>Day 1</td>
      <td>PM + Architect</td>
      <td>Target folder structure; ADR-001, ADR-002</td>
      <td><strong style="color:#1a6b3c">&#10003; Done</strong></td>
      <td>Folder structure created. ADR-001 (three-tier API) and ADR-002 (repository pattern) written to <code>docs/</code>. Config YAML hierarchy created.</td>
    </tr>
    <tr>
      <td>Day 2</td>
      <td>Architect</td>
      <td>Pydantic schemas for all 15 CSV tables</td>
      <td><strong style="color:#0056b8">&#8594; In Progress</strong></td>
      <td></td>
    </tr>
    <tr>
      <td>Day 3</td>
      <td>TechWriter</td>
      <td>Bootstrap Confluence: Architecture section, ADR pages, Sprint board</td>
      <td>Pending</td>
      <td></td>
    </tr>
  </tbody>
</table>

<h2>Day 1 Deliverables</h2>

<h3>Folder Structure</h3>
<p>Full production layout created under <code>riia-jun-release/</code>:</p>
<ul>
  <li><code>src/rita/api/v1/system/</code> &mdash; CRUD routers (positions, orders, snapshots)</li>
  <li><code>src/rita/api/v1/workflow/</code> &mdash; Business process routers (train, backtest, evaluate)</li>
  <li><code>src/rita/api/bff/</code> &mdash; BFF aggregation routers (dashboard, fno, ops)</li>
  <li><code>src/rita/services/</code> &mdash; Service layer stubs</li>
  <li><code>src/rita/repositories/</code> &mdash; Repository layer stubs</li>
  <li><code>src/rita/schemas/</code> &mdash; Pydantic schemas (Day 2)</li>
  <li><code>src/rita/core/</code> &mdash; Pure calculation/ML logic (ported Sprint 2+)</li>
  <li><code>config/{base,development,staging,production}.yaml</code> &mdash; Config hierarchy</li>
  <li><code>tests/{unit,integration,e2e}/</code> &mdash; Test directories</li>
  <li><code>dashboard/js/{rita,fno,ops}/</code> &mdash; ES module targets (Sprint 4)</li>
  <li><code>k8s/</code> &mdash; Kubernetes manifests (Sprint 5)</li>
  <li><code>docs/</code> &mdash; ADRs</li>
</ul>

<h3>ADR-001: Three-Tier API Design</h3>
<p>Decision to split the monolithic 1,533-line <code>rest_api.py</code> into three tiers:</p>
<ul>
  <li><strong>System tier</strong> (<code>/api/v1/system/</code>) &mdash; pure CRUD, one repository call per route</li>
  <li><strong>Workflow tier</strong> (<code>/api/v1/workflow/</code>) &mdash; stateful jobs (train, backtest, evaluate)</li>
  <li><strong>BFF tier</strong> (<code>/api/bff/</code>) &mdash; UI aggregation, no business logic</li>
</ul>

<h3>ADR-002: Repository Pattern</h3>
<p>All CSV I/O goes through typed repository classes with:</p>
<ul>
  <li><code>BaseRepository[T]</code> abstract interface (read_all, write_all, find_by_id, upsert, delete)</li>
  <li>Per-instance <code>threading.Lock</code> for file safety</li>
  <li>Pydantic schema validation on every read and write</li>
  <li>15 repository classes defined &mdash; one per CSV table</li>
  <li>v2 PostgreSQL migration requires only repository layer changes</li>
</ul>

<h3>Config YAML Hierarchy</h3>
<p><code>base.yaml</code> defines all defaults. Environment files override selectively. Financial constants (lot sizes) are config-driven &mdash; never hardcoded.</p>

<h2>Sprint 0 Definition of Done</h2>
<ul>
  <li>&#10003; ADR-001 and ADR-002 written and reviewed</li>
  <li>&#10003; Full folder structure in place</li>
  <li>&#9744; Pydantic schemas for all 15 CSV tables</li>
  <li>&#9744; Confluence Architecture section published</li>
  <li>&#9744; Sprint board live on Confluence</li>
</ul>
"""

if __name__ == "__main__":
    client = ConfluenceClient()
    page_id, url = client.create_page(TITLE, BODY, parent_id=SECTION["sprint_boards"])
    print(f"Sprint 0 board created: {url}")
    print(f"Page ID: {page_id}")
