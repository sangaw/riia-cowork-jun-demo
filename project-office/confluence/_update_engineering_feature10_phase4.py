# One-off: append Feature 10 Phase 4 completion note to Engineering page (76611602).
# Run from project root: riia-cowork-jun/
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from confluence.publish import ConfluenceClient, SECTION

PAGE_ID = SECTION["engineering_current"]   # 76611602

APPEND_HTML = """
<h2>JS Architecture — Shared Layer: Phase 4 Complete (2026-05-18)</h2>
<p>Feature 10 Phase 4 extracted all inline JavaScript from <code>ds.html</code> into an ES module
tree rooted at <code>dashboard/js/ds/</code>. This is a pure JS refactoring — no new API endpoints,
no Python changes. All 19 sections are now served as discrete ES modules; the single large inline
<code>&lt;script&gt;</code> block (~2,500 lines) has been replaced with a single
<code>&lt;script type="module" src="js/ds/main.js"&gt;</code> tag.</p>
<table>
  <thead>
    <tr><th>Item</th><th>Change</th><th>Date</th></tr>
  </thead>
  <tbody>
    <tr>
      <td>Feature 10 Phase 4 complete</td>
      <td><code>dashboard/js/ds/</code> directory created with 24 ES modules;
          <code>ds.html</code> now loads via <code>&lt;script type="module" src="js/ds/main.js"&gt;</code></td>
      <td>2026-05-18</td>
    </tr>
    <tr>
      <td><code>ds/api.js</code></td>
      <td>CREATED — thin re-export: <code>apiBase</code>, <code>api</code>, <code>apiFetch</code>
          from <code>../shared/api.js</code>; exports <code>DS_API_KEY = ''</code></td>
      <td>2026-05-18</td>
    </tr>
    <tr>
      <td><code>ds/utils.js</code></td>
      <td>CREATED — ds-specific helpers: <code>mkTbl</code>, <code>fmtPctRaw</code>,
          <code>openChartModal</code>, <code>closeChartModal</code>,
          <code>DS_C</code> (extended color palette with ds-specific keys)</td>
      <td>2026-05-18</td>
    </tr>
    <tr>
      <td><code>ds/state.js</code></td>
      <td>CREATED — cross-section shared mutable state:
          <code>export const state = { activeInst: null }</code>;
          written by <code>pipeline.js</code>, read by <code>performance.js</code>,
          <code>trades.js</code>, <code>experiment-results.js</code></td>
      <td>2026-05-18</td>
    </tr>
    <tr>
      <td><code>ds/nav.js</code></td>
      <td>CREATED — <code>createShow(loaders)</code> factory returning <code>show(sId, el)</code>
          function; handles DOM section switching + nav highlight</td>
      <td>2026-05-18</td>
    </tr>
    <tr>
      <td><code>ds/main.js</code></td>
      <td>CREATED — entry point: imports all 19 section loaders + <code>createShow</code>;
          assigns all 17 <code>window.*</code> bindings at module scope (before addEventListener);
          calls <code>init()</code> on DOMContentLoaded</td>
      <td>2026-05-18</td>
    </tr>
    <tr>
      <td>19 section modules</td>
      <td>CREATED — <code>understand.js</code>, <code>dashboard.js</code>, <code>pipeline.js</code>,
          <code>performance.js</code>, <code>risk.js</code>, <code>trades.js</code>,
          <code>explain.js</code>, <code>scenarios.js</code>, <code>training.js</code>,
          <code>changelog.js</code>, <code>observability.js</code>, <code>mcp.js</code>,
          <code>export.js</code>, <code>experiment-results.js</code>,
          <code>trade-diagnostics.js</code>, <code>model-train-progress.js</code>,
          <code>model-observability.js</code>, <code>model-mcp.js</code>,
          <code>model-audit.js</code></td>
      <td>2026-05-18</td>
    </tr>
    <tr>
      <td><code>dashboard/ds.html</code></td>
      <td>MODIFIED — removed ~2,500-line inline <code>&lt;script&gt;</code> block;
          CDN scripts (Chart.js + annotation plugin) kept; nav-collapse IIFE kept as plain
          <code>&lt;script&gt;</code>; added
          <code>&lt;script type="module" src="js/ds/main.js"&gt;</code> before
          <code>&lt;/body&gt;</code></td>
      <td>2026-05-18</td>
    </tr>
    <tr>
      <td><code>project-office/specs/Spec_JS_Code.md</code></td>
      <td>UPDATED — Section 5 replaced with 24-file ds/ module table; all 19 sections
          marked Extracted (pending merge to master from worktree
          <code>agent-aa2807d8bb1942976</code>)</td>
      <td>2026-05-18</td>
    </tr>
  </tbody>
</table>
<p><strong>QA fixes applied (commit 993be51):</strong> 12 system-tier API paths replaced with
experience-tier paths across 9 files (<code>/api/v1/training-history</code> →
<code>/api/v1/experience/rita/training-history</code>, etc.);
<code>api()</code> POST signature corrected in <code>pipeline.js</code> and
<code>scenarios.js</code> to positional form <code>api(path, 'POST', body)</code>.</p>
<p><strong>Status:</strong> Code complete (Engineer commits 763b465 + 993be51, branch
<code>worktree-agent-aa2807d8bb1942976</code>). QA: 8/8 checks passed.
Browser verify (ds.html zero console errors) pending user sign-off.
<code>Spec_JS_Code.md</code> Section 5 updated in worktree — pending merge to master.</p>
"""

def main():
    try:
        client = ConfluenceClient()
        page = client.get_page(PAGE_ID, expand="version,body.storage")
        title = page["title"]
        print(f"Fetched page: '{title}' (ID {PAGE_ID}, version {page['version']['number']})")
        _, url = client.append_to_page(PAGE_ID, title, APPEND_HTML)
        print(f"SUCCESS — page updated: {url}")
        return url
    except Exception as e:
        print(f"n/a — Confluence unreachable: {e}")
        return None

if __name__ == "__main__":
    main()
