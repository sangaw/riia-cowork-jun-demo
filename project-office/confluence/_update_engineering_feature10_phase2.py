# One-off: append Feature 10 Phase 2 completion note to Engineering page (76611602).
# Run from project root: riia-cowork-jun/
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from confluence.publish import ConfluenceClient, SECTION

PAGE_ID = SECTION["engineering_current"]   # 76611602

APPEND_HTML = """
<h2>JS Architecture — Shared Layer: Phase 2 Complete (2026-05-18)</h2>
<p>Feature 10 Phase 2 migrated the <code>rita/</code> and <code>ops/</code> JavaScript modules
to consume the canonical <code>shared/</code> layer created in Phase 1.
This is a pure JS refactoring — no API endpoint changes, no Python changes, no HTML changes.</p>
<table>
  <thead>
    <tr><th>Item</th><th>Change</th><th>Date</th></tr>
  </thead>
  <tbody>
    <tr>
      <td>Feature 10 Phase 2 complete</td>
      <td>RITA + Ops JS modules migrated to shared/ imports</td>
      <td>2026-05-18</td>
    </tr>
    <tr>
      <td><code>dashboard/js/rita/api.js</code></td>
      <td>Thin re-export wrapper → <code>shared/api.js</code> (<code>api</code>)</td>
      <td>2026-05-18</td>
    </tr>
    <tr>
      <td><code>dashboard/js/rita/utils.js</code></td>
      <td>Thin re-export wrapper → <code>shared/utils.js</code> (fmt, fmtPct, fmtMs, setEl, appendResult, badge)</td>
      <td>2026-05-18</td>
    </tr>
    <tr>
      <td><code>dashboard/js/ops/api.js</code></td>
      <td>Thin re-export wrapper → <code>shared/api.js</code> (apiBase, api, apiFetch)</td>
      <td>2026-05-18</td>
    </tr>
    <tr>
      <td><code>dashboard/js/ops/utils.js</code></td>
      <td>Merged: absorbed <code>ops/utilities.js</code>; re-exports fmt, setEl from shared; keeps local two-arg badge(text, cls), stepName, and all pipeline action functions</td>
      <td>2026-05-18</td>
    </tr>
    <tr>
      <td><code>dashboard/js/ops/utilities.js</code></td>
      <td>Deleted — content merged into <code>ops/utils.js</code></td>
      <td>2026-05-18</td>
    </tr>
  </tbody>
</table>
<p><strong>Status:</strong> Code complete (commit 2b7fa51, branch worktree-agent-af1025d550695762c).
Browser verification (rita.html + ops.html zero console errors) pending manual check.
Spec_JS_Code.md updated in same commit.</p>
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
