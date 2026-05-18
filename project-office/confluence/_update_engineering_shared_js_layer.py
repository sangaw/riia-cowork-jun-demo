"""
Update the Engineering Confluence page (76611602) after Feature 10 Phase 1 —
Shared JS Layer (task-brief-20260518-1057).

Changes:
  1. Update the Source Layout pre-block to mention js/shared/ directory
  2. Add a "Frontend Architecture — Shared JS Layer (Feature 10 Phase 1)"
     subsection under Source Layout
  3. Date is already 2026-05-18 — no bump needed

Run from project root:
    python project-office/confluence/_update_engineering_shared_js_layer.py
"""
import urllib.request, json, base64
from pathlib import Path

PAGE_ID = "76611602"
EMAIL   = Path("confluence-api-key.txt").read_text().splitlines()[1].strip()
TOKEN   = Path("confluence-api-key.txt").read_text().splitlines()[0].strip()
BASE    = "https://ravionics.atlassian.net/wiki/rest/api"

creds   = base64.b64encode(f"{EMAIL}:{TOKEN}".encode()).decode()
HEADERS = {"Authorization": f"Basic {creds}", "Content-Type": "application/json"}


def get(path):
    req = urllib.request.Request(f"{BASE}/{path}", headers=HEADERS)
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())


def put(path, payload):
    data = json.dumps(payload).encode()
    req  = urllib.request.Request(f"{BASE}/{path}", data=data, headers=HEADERS, method="PUT")
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())


# ── 1. Fetch current page ────────────────────────────────────────────────────
page    = get(f"content/{PAGE_ID}?expand=body.storage,version")
title   = page["title"]
version = page["version"]["number"]
body    = page["body"]["storage"]["value"]

print(f"Fetched: '{title}' v{version}, {len(body)} chars")
body_updated = body

MARKER = "shared-js-layer-2026-05-18"

if MARKER in body_updated:
    print("NOTE: Shared JS Layer section already present — skipping")
else:
    # ── 2. Update Source Layout to mention js/shared/ ─────────────────────────
    OLD_JS_LINES = (
        "    js/rita/           &larr; 21 ES modules for RITA dashboard\n"
        "    js/fno/            &larr; 14 ES modules for FnO dashboard\n"
        "    js/ops/            &larr; 14 ES modules for Ops dashboard"
    )
    NEW_JS_LINES = (
        "    js/rita/           &larr; 21 ES modules for RITA dashboard\n"
        "    js/fno/            &larr; 14 ES modules for FnO dashboard\n"
        "    js/ops/            &larr; 14 ES modules for Ops dashboard\n"
        "    js/shared/         &larr; 4 canonical shared modules (Feature 10 Phase 1)"
    )

    if OLD_JS_LINES in body_updated:
        body_updated = body_updated.replace(OLD_JS_LINES, NEW_JS_LINES, 1)
        print("OK: Source Layout updated with js/shared/ entry")
    else:
        print("WARNING: Source Layout JS block not found — skipping that change")

    # ── 3. Insert Shared JS Layer subsection after Source Layout <hr /> ───────
    SHARED_JS_SECTION = f"""<!-- {MARKER} -->
<h2>Frontend Architecture &mdash; Shared JS Layer (Feature 10 Phase 1)</h2>
<p>Feature 10 Phase 1 introduces four canonical shared JavaScript modules under
<code>dashboard/js/shared/</code>. These modules establish a single source of truth for
cross-app utilities without modifying any existing import paths or runtime behaviour.
All changes are purely additive; no existing module was deleted or re-wired.</p>

<table>
  <thead><tr><th>File</th><th>Responsibility</th><th>Key Exports</th></tr></thead>
  <tbody>
    <tr>
      <td><code>shared/api.js</code></td>
      <td>Canonical HTTP client (shared by all apps). Reads <code>window.RITA_API_BASE</code>
      and <code>window.SESSION_TRACE_ID</code> at call time (not import time).</td>
      <td><code>apiBase() &rarr; string</code>,
          <code>api(path, method?, body?) &rarr; Promise&lt;any&gt;</code> (throws on non-2xx),
          <code>apiFetch(url, options?) &rarr; Promise&lt;any|null&gt;</code> (returns null on error,
          adds <code>X-Request-ID</code> header)</td>
    </tr>
    <tr>
      <td><code>shared/utils.js</code></td>
      <td>Canonical DOM helpers and number formatters (shared by all apps).
      <code>badge()</code> uses <code>String(status || '')</code> coercion (EC-5).
      <code>fmt()</code> returns <code>&mdash;</code> on null/undefined/empty string.</td>
      <td><code>fmt(v, d?)</code>, <code>fmtPct(v)</code>, <code>fmtMs(v)</code>,
          <code>setEl(id, html)</code>, <code>appendResult(containerId, html)</code>,
          <code>badge(status)</code></td>
    </tr>
    <tr>
      <td><code>shared/charts.js</code></td>
      <td>Chart.js registry moved from <code>rita/charts.js</code> (shared by all apps).
      Internal import updated to <code>../rita/chart-modal.js</code>.
      <code>rita/charts.js</code> is now a one-line re-export shim:
      <code>export * from '../shared/charts.js';</code></td>
      <td><code>destroyChart(id)</code>, <code>mkChart(id, config)</code>,
          <code>chartOpts(label, tickCb, labels)</code>, <code>C</code> (colour palette)</td>
    </tr>
    <tr>
      <td><code>shared/nav-base.js</code></td>
      <td>Lazy-loader registry factory. <code>load(key)</code> silently no-ops for
      unregistered keys (EC-6).</td>
      <td><code>createNavRegistry() &rarr; &#123; register(key, fn), load(key), reset(key), loaders &#125;</code></td>
    </tr>
  </tbody>
</table>

<p><strong>Commit:</strong> <code>2d9d92e</code> &mdash; branch <code>worktree-agent-a68efb4104278d4a2</code> (2026-05-18)</p>
<p><strong>No API changes, no HTML changes, no backend changes.</strong> Phase 2 (ops utils merge)
and Phase 3 (FnO god-module split) are planned as future enhancements.</p>

"""

    # Insert after the Source Layout section's closing <hr />
    SOURCE_LAYOUT_HR = "<hr />\n\n\n<h2>API Inventory</h2>"
    SOURCE_LAYOUT_HR_ALT = "<hr />\n\n<h2>API Inventory</h2>"

    if SOURCE_LAYOUT_HR in body_updated:
        body_updated = body_updated.replace(
            SOURCE_LAYOUT_HR,
            SHARED_JS_SECTION + "<hr />\n\n\n<h2>API Inventory</h2>",
            1
        )
        print("OK: Shared JS Layer section inserted (variant 1)")
    elif SOURCE_LAYOUT_HR_ALT in body_updated:
        body_updated = body_updated.replace(
            SOURCE_LAYOUT_HR_ALT,
            SHARED_JS_SECTION + "<hr />\n\n<h2>API Inventory</h2>",
            1
        )
        print("OK: Shared JS Layer section inserted (variant 2)")
    else:
        # Fallback: insert before API Inventory heading
        API_H2 = "<h2>API Inventory</h2>"
        if API_H2 in body_updated:
            body_updated = body_updated.replace(
                API_H2,
                SHARED_JS_SECTION + API_H2,
                1
            )
            print("OK: Shared JS Layer section inserted (fallback — before API Inventory)")
        else:
            print("ERROR: Could not find insertion anchor — aborting")
            import sys; sys.exit(1)

# ── 4. Push update ───────────────────────────────────────────────────────────
if body_updated == body:
    print("No changes made — page not updated")
else:
    payload = {
        "version": {"number": version + 1},
        "title":   title,
        "type":    "page",
        "body":    {"storage": {"value": body_updated, "representation": "storage"}},
    }
    result  = put(f"content/{PAGE_ID}", payload)
    new_ver = result["version"]["number"]
    url     = f"https://ravionics.atlassian.net/wiki{result['_links']['webui']}"
    print(f"OK: Page updated to v{new_ver}")
    print(f"URL: {url}")
