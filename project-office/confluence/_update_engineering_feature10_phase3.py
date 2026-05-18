# One-off: append Feature 10 Phase 3 completion note to Engineering page (76611602).
# Run from project root: riia-cowork-jun/
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from confluence.publish import ConfluenceClient, SECTION

PAGE_ID = SECTION["engineering_current"]   # 76611602

APPEND_HTML = """
<h2>JS Architecture — Shared Layer: Phase 3 Complete (2026-05-18)</h2>
<p>Feature 10 Phase 3 split the <code>fno/api.js</code> god module into two lean modules,
completing the FnO JS layer migration to the canonical <code>shared/</code> layer.
This is a pure JS refactoring — no API endpoint changes, no Python changes, no HTML changes.</p>
<table>
  <thead>
    <tr><th>Item</th><th>Change</th><th>Date</th></tr>
  </thead>
  <tbody>
    <tr>
      <td>Feature 10 Phase 3 complete</td>
      <td>FnO god module (<code>fno/api.js</code>) split into thin re-export + app-init module</td>
      <td>2026-05-18</td>
    </tr>
    <tr>
      <td><code>dashboard/js/fno/api.js</code></td>
      <td>REWRITTEN — thin re-export wrapper (9 lines): re-exports <code>apiBase</code>, <code>api</code>, <code>apiFetch</code> from <code>../shared/api.js</code>; declares <code>RITA_API_KEY</code> locally</td>
      <td>2026-05-18</td>
    </tr>
    <tr>
      <td><code>dashboard/js/fno/app-init.js</code></td>
      <td>CREATED — holds <code>fetchPositions()</code>, <code>initApp()</code>, <code>checkStatus()</code> extracted from old <code>fno/api.js</code> god module; imports <code>apiBase</code> and <code>RITA_API_KEY</code> from <code>./api.js</code></td>
      <td>2026-05-18</td>
    </tr>
    <tr>
      <td><code>dashboard/js/fno/main.js</code></td>
      <td>MODIFIED — import source for <code>initApp</code>, <code>checkStatus</code>, <code>fetchPositions</code> changed from <code>./api.js</code> to <code>./app-init.js</code>; all 15 window bindings preserved</td>
      <td>2026-05-18</td>
    </tr>
    <tr>
      <td><code>project-office/specs/Spec_JS_Code.md</code></td>
      <td>UPDATED — FnO module table: <code>app-init.js</code> row added; <code>api.js</code> row updated to "Thin re-export wrapper"; <code>utils.js</code> row updated to describe 3 fno-specific formatters</td>
      <td>2026-05-18</td>
    </tr>
  </tbody>
</table>
<p><strong>Status:</strong> Code complete (commit 198348b, merged cb79df2).
Browser verification (fno.html zero console errors) passed by user 2026-05-18.
Spec_JS_Code.md updated in same commit. 42/42 import contract checks passed.</p>
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
