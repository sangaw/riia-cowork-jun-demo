"""
Publishes (or updates) the Sprint 4 board page under Sprint Boards in Confluence.
Run at end of each Sprint 4 day to reflect progress.

First run:  PAGE_ID = None  → creates the page, prints the ID → paste it below
Subsequent: PAGE_ID = "..."  → updates the existing page in-place
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from confluence.publish import ConfluenceClient, SECTION

TITLE = "Sprint 4 — Frontend & Responsive Design"

# After first run, paste the returned page ID here so subsequent runs update in-place.
PAGE_ID = None

BODY = """
<h1>Sprint 4 &mdash; Frontend &amp; Responsive Design</h1>
<p><strong>Duration:</strong> Days 25&ndash;30 &nbsp;|&nbsp; <strong>Theme:</strong> Decompose monolithic HTML files into ES modules, add responsive CSS breakpoints, remove hardcoded URLs, and add Playwright e2e tests</p>

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
      <td>Day 25</td>
      <td>Engineer F</td>
      <td>Decompose rita.html &rarr; ES modules</td>
      <td><strong style="color:#1a6b3c">&#10003; Done</strong></td>
      <td>21 ES modules in dashboard/js/rita/. rita.html becomes entry-point only. window.* bindings for all onclick handlers. All sections preserved.</td>
    </tr>
    <tr>
      <td>Day 26</td>
      <td>Engineer F</td>
      <td>Decompose fno.html, ops.html &rarr; ES modules</td>
      <td><strong style="color:#1a6b3c">&#10003; Done</strong></td>
      <td>fno: 14 ES modules (state.js + 13 feature modules including hedge.js). ops: 12 ES modules. Both entry-point HTML files written.</td>
    </tr>
    <tr>
      <td>Day 27</td>
      <td>Engineer F</td>
      <td>Responsive CSS (480 / 768 / 1100px)</td>
      <td><strong style="color:#1a6b3c">&#10003; Done</strong></td>
      <td>dashboard/css/responsive.css created. Hamburger toggle button added to all 3 HTML files. Off-canvas sidebar at &le;768px. Progressive grid collapse at all 3 breakpoints.</td>
    </tr>
    <tr>
      <td>Day 28</td>
      <td>Engineer F</td>
      <td>Remove localhost:8000 hardcoding</td>
      <td><strong style="color:#92480a">&#9679; Planned</strong></td>
      <td></td>
    </tr>
    <tr>
      <td>Day 29</td>
      <td>QA</td>
      <td>Playwright e2e tests</td>
      <td><strong style="color:#92480a">&#9679; Planned</strong></td>
      <td></td>
    </tr>
    <tr>
      <td>Day 30</td>
      <td>TechWriter</td>
      <td>Confluence: Frontend Architecture</td>
      <td><strong style="color:#92480a">&#9679; Planned</strong></td>
      <td></td>
    </tr>
  </tbody>
</table>

<h2>Day 27 Deliverables &mdash; Responsive CSS</h2>

<h3>New Files</h3>
<table>
  <thead><tr><th>File</th><th>Purpose</th></tr></thead>
  <tbody>
    <tr><td><code>dashboard/css/responsive.css</code></td><td>Shared responsive stylesheet linked by all three HTML dashboards. Three media-query breakpoints: 1100px, 768px, 480px.</td></tr>
  </tbody>
</table>

<h3>Modified Files</h3>
<table>
  <thead><tr><th>File</th><th>Change</th></tr></thead>
  <tbody>
    <tr><td><code>dashboard/rita.html</code></td><td>Added &lt;link&gt; to responsive.css; hamburger toggle button; inline nav-toggle script.</td></tr>
    <tr><td><code>dashboard/fno.html</code></td><td>Added &lt;link&gt; to responsive.css; hamburger toggle button; inline nav-toggle script.</td></tr>
    <tr><td><code>dashboard/ops.html</code></td><td>Added &lt;link&gt; to responsive.css; hamburger toggle button; inline nav-toggle script.</td></tr>
  </tbody>
</table>

<h3>Breakpoint Behaviour</h3>
<table>
  <thead><tr><th>Breakpoint</th><th>Layout changes</th></tr></thead>
  <tbody>
    <tr>
      <td>&le;1100px</td>
      <td>Sidebar slim to 200px. 5-col KPI &rarr; 3-col. 4-col KPI &rarr; 3-col. 3-col card rows &rarr; 2-col. HMC 4-col &rarr; 2-col. Greeks 4-col &rarr; 2-col. Form grid 3-col &rarr; 2-col. Market 3-panel &rarr; 2-col (third spans full width). Ops g4 &rarr; 2-col.</td>
    </tr>
    <tr>
      <td>&le;768px</td>
      <td>Hamburger button shown. Sidebar off-canvas (transforms translateX(-100%)); opens with .open class + body.nav-open backdrop. Shell grid-template-columns: 0 1fr. KPI 3-col &rarr; 2-col. Card rows &rarr; 1-col. Form grid &rarr; 1-col. Ops g3/g4 &rarr; 2-col. Tables overflow-x: auto. Page headers stack vertically.</td>
    </tr>
    <tr>
      <td>&le;480px</td>
      <td>All KPI rows &rarr; 1-col. HMC &rarr; 1-col. Ops grids all &rarr; 1-col. Market OHLC 4-col &rarr; 2-col. Scenario stats 4-col &rarr; 2-col. Step bar wraps into pairs. Topbar mid hidden. Topbar padding 10px. Sidebar full width.</td>
    </tr>
  </tbody>
</table>

<h3>Hamburger / Sidebar Toggle</h3>
<ul>
  <li>Button: <code>#nav-toggle</code> &mdash; .nav-toggle class, hidden at &gt;768px via CSS</li>
  <li>Sidebar: gets .open class via inline script; CSS drives the slide-in transform</li>
  <li>Backdrop: <code>body.nav-open::before</code> pseudo-element covers the main area; click closes sidebar</li>
  <li>No dependency on any framework or module &mdash; self-contained IIFE in each HTML file</li>
</ul>

<h2>Day 26 Deliverables &mdash; FnO &amp; Ops ES Modules</h2>
<ul>
  <li><strong>fno modules (14):</strong> state.js, api.js, nav.js, utils.js, dashboard.js, positions.js, greeks.js, payoff.js, margin.js, rr.js, stress.js, hedge.js, manoeuvre.js, main.js</li>
  <li><strong>ops modules (12):</strong> api.js, utils.js, nav.js, sidebar.js, overview.js, monitoring.js, cicd.js, deploy.js, observability.js, daily-ops.js, chat.js, main.js</li>
</ul>

<h2>Day 25 Deliverables &mdash; RITA Dashboard ES Modules</h2>
<ul>
  <li><strong>21 modules:</strong> api.js, utils.js, nav.js, health.js, charts.js, chart-modal.js, performance.js, trades.js, diagnostics.js, explainability.js, scenarios.js, pipeline.js, training.js, audit.js, market-signals.js, risk.js, observability.js, mcp.js, chat.js, export.js, main.js</li>
  <li>All onclick handlers bound via window.* in main.js for HTML compatibility</li>
</ul>

<h2>Sprint 4 Definition of Done</h2>
<ul>
  <li>&#10003; rita.html decomposed into 21 ES modules (Day 25)</li>
  <li>&#10003; fno.html &rarr; 14 ES modules, ops.html &rarr; 12 ES modules (Day 26)</li>
  <li>&#10003; Responsive CSS at 480 / 768 / 1100px with hamburger sidebar toggle (Day 27)</li>
  <li>&#9675; Remove localhost:8000 hardcoding &mdash; window.RITA_API_BASE (Day 28)</li>
  <li>&#9675; Playwright e2e tests at all 3 breakpoints (Day 29)</li>
  <li>&#9675; Confluence Frontend Architecture page (Day 30)</li>
</ul>
"""


if __name__ == "__main__":
    client = ConfluenceClient()

    if PAGE_ID:
        page_id, url = client.update_page(PAGE_ID, TITLE, BODY)
        print(f"Sprint 4 board updated: {url}")
    else:
        page_id, url = client.create_page(TITLE, BODY, parent_id=SECTION["sprint_boards"])
        print(f"Sprint 4 board created: {url}")
        print(f"Page ID: {page_id}")
        print(f"\nPaste this into PAGE_ID at the top of this script for future updates:")
        print(f'PAGE_ID = "{page_id}"')
