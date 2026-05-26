"""
Update the Engineering Confluence page (76611602) for Feature 17 Phase 0 —
Mobile Gateway Hub (GET /mobile + mobileapp/gateway.html).

Changes:
  - Append a Feature 17 section documenting:
    - GET /mobile route (FileResponse serving gateway.html)
    - 5-card gateway hub design
    - Mobile Ready vs Desktop Only card convention

Run from project root:
    python project-office/confluence/_update_engineering_feature17_mobile_gateway.py
"""
import urllib.request, urllib.error, json, base64
from pathlib import Path

PAGE_ID = "76611602"
EMAIL   = Path("confluence-api-key.txt").read_text().splitlines()[1].strip()
TOKEN   = Path("confluence-api-key.txt").read_text().splitlines()[0].strip()
BASE    = "https://ravionics.atlassian.net/wiki/rest/api"

creds   = base64.b64encode(f"{EMAIL}:{TOKEN}".encode()).decode()
HEADERS = {
    "Authorization": f"Basic {creds}",
    "Content-Type": "application/json",
    "Accept": "application/json",
}


def get(path):
    req = urllib.request.Request(f"{BASE}/{path}", headers=HEADERS)
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())


def put(path, body):
    data = json.dumps(body).encode()
    req = urllib.request.Request(f"{BASE}/{path}", data=data, headers=HEADERS, method="PUT")
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read()), r.status
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        return (json.loads(raw) if raw.strip() else {}), e.code


FEATURE17_HTML = """
<h2>Feature 17 Phase 0 &#8212; Mobile Gateway Hub (2026-05-26)</h2>
<p>Adds a purpose-built gateway landing page served at <code>GET /mobile</code>. Mobile users
see five app cards labelled as either <em>Mobile Ready</em> or <em>Desktop Only</em> with
appropriate links. No UA detection, no redirect snippets &#8212; pure static HTML.</p>

<h3>New Route</h3>
<table>
  <thead>
    <tr><th>Method</th><th>Path</th><th>Auth</th><th>Response</th><th>Description</th></tr>
  </thead>
  <tbody>
    <tr>
      <td><code>GET</code></td>
      <td><code>/mobile</code></td>
      <td>None</td>
      <td><code>FileResponse</code></td>
      <td>Serves <code>mobileapp/gateway.html</code> &#8212; a self-contained hub page listing
          all RITA apps with Mobile Ready / Desktop Only labelling. Route registered before
          the <code>/mobileapp</code> static mount to prevent route shadowing.
          <code>include_in_schema=False</code>.</td>
    </tr>
  </tbody>
</table>

<h3>Frontend File</h3>
<p>File: <code>riia-jun-release/mobileapp/gateway.html</code> (CREATE new)</p>
<ul>
  <li>Standalone HTML &#8212; no <code>&lt;script&gt;</code> tags, all CSS inline</li>
  <li>5 app cards with required DOM IDs: <code>card-rita</code>, <code>card-invest</code>,
      <code>card-fno</code>, <code>card-ops</code>, <code>card-ds</code></li>
  <li>Footer escape-hatch: <code>footer-desktop-link</code> &#8594; <code>/dashboard</code></li>
  <li>CSS tokens shared with <code>mobileapp/index.html</code> (<code>--bg</code>,
      <code>--surface</code>, <code>--build</code>, <code>--warn</code>, etc.)</li>
</ul>

<h3>App Card Inventory</h3>
<table>
  <thead>
    <tr><th>DOM ID</th><th>Destination</th><th>Type</th><th>Colour</th></tr>
  </thead>
  <tbody>
    <tr><td><code>card-rita</code></td><td><code>/mobileapp</code></td><td>Mobile Ready</td><td>Green accent bar + filled CTA button</td></tr>
    <tr><td><code>card-invest</code></td><td><code>/onboarding</code></td><td>Mobile Ready</td><td>Green accent bar + filled CTA button</td></tr>
    <tr><td><code>card-fno</code></td><td><code>/dashboard/fno.html?desktop=1</code></td><td>Desktop Only</td><td>Amber accent bar + &#8220;Open anyway &#8599;&#8221; text link</td></tr>
    <tr><td><code>card-ops</code></td><td><code>/dashboard/ops.html?desktop=1</code></td><td>Desktop Only</td><td>Amber accent bar + &#8220;Open anyway &#8599;&#8221; text link</td></tr>
    <tr><td><code>card-ds</code></td><td><code>/dashboard/ds.html?desktop=1</code></td><td>Desktop Only</td><td>Amber accent bar + &#8220;Open anyway &#8599;&#8221; text link</td></tr>
  </tbody>
</table>

<h3>Layout</h3>
<ul>
  <li>2-column card grid at &#8805; 400 px; single column at &lt; 400 px
      (<code>@media (max-width: 399px)</code>)</li>
  <li>Page shell <code>max-width: 600px</code> centred</li>
  <li>Renders offline &#8212; no external network dependencies (Google Fonts has system fallbacks)</li>
</ul>

<h3>Files Modified</h3>
<ul>
  <li><code>riia-jun-release/mobileapp/gateway.html</code> &#8212; CREATED</li>
  <li><code>riia-jun-release/src/rita/main.py</code> &#8212; added <code>GET /mobile</code> route</li>
  <li><code>project-office/specs/Spec_Mobile_App.md</code> &#8212; added Section 7 (Gateway Hub Page)</li>
</ul>

<h3>Test Coverage</h3>
<ul>
  <li>Test file: <code>riia-jun-release/tests/unit/test_mobile_gateway.py</code> &#8212; 16 tests, all passing</li>
  <li>Edge cases covered: <code>?from=APPNAME</code> query param silently ignored, all 6 required DOM IDs
      present, Desktop Only links contain <code>?desktop=1</code>, no <code>&lt;script&gt;</code> tag,
      <code>GET /</code> still redirects to <code>/dashboard</code> (UA detection is Phase 1)</li>
</ul>

<h3>Scope Notes</h3>
<ul>
  <li>No changes to <code>rita.html</code>, <code>fno.html</code>, <code>ops.html</code>, or
      <code>mobileapp/index.html</code></li>
  <li>UA detection and automatic redirect logic are deferred to Feature 17 Phase 1</li>
  <li><code>GET /mobile</code> is a page route, not a data API &#8212; no Pydantic schema, no endpoint
      inventory row in <code>Spec_RITA_App.md</code></li>
</ul>
"""


def main():
    print(f"Fetching Engineering page {PAGE_ID}...")
    page = get(f"content/{PAGE_ID}?expand=version,body.storage")
    title   = page["title"]
    version = page["version"]["number"]
    print(f"  Title: {title}  (version {version})")

    current_body = page["body"]["storage"]["value"]
    new_body = current_body + FEATURE17_HTML

    payload = {
        "version": {"number": version + 1},
        "title": title,
        "type": "page",
        "body": {"storage": {"value": new_body, "representation": "storage"}},
    }

    result, status = put(f"content/{PAGE_ID}", payload)
    if status == 200:
        url = f"https://ravionics.atlassian.net/wiki{result['_links']['webui']}"
        print(f"  Updated successfully (version {version + 1}): {url}")
        return url
    else:
        raise RuntimeError(f"Update failed: HTTP {status} — {result.get('message','')[:200]}")


if __name__ == "__main__":
    url = main()
    print(f"\nDone. Engineering page: {url}")
