"""
Update the Engineering Confluence page (76611602) for Feature 17 Phase 1 —
Mobile UA Detection + JS Snippet.

Changes:
  - Append a Feature 17 Phase 1 section documenting:
    - root() UA detection regex and server-side redirect logic
    - Inline IIFE JS snippet added to 5 dashboard HTML files
    - ?desktop=1 bypass / sessionStorage.mobileBypass escape-hatch convention

Run from project root:
    python project-office/confluence/_update_engineering_feature17_phase1.py
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


FEATURE17_PHASE1_HTML = """
<h2>Feature 17 Phase 1 &#8212; Mobile UA Detection + JS Snippet (2026-05-26)</h2>
<p>Wires up automatic mobile redirection in two layers: (1) a server-side User-Agent check in
the <code>root()</code> handler that redirects mobile visitors from <code>GET /</code> to the
<code>/mobile</code> gateway instead of <code>/dashboard</code>, and (2) a synchronous inline
IIFE JavaScript snippet inserted as the first <code>&lt;script&gt;</code> inside
<code>&lt;head&gt;</code> on all five desktop dashboard HTML files, ensuring users who arrive
directly at a dashboard URL via bookmark or link are also redirected on mobile.</p>

<h3>Server-Side Change &#8212; <code>root()</code> UA Detection</h3>
<table>
  <thead>
    <tr><th>Method</th><th>Path</th><th>Auth</th><th>Response</th><th>Description</th></tr>
  </thead>
  <tbody>
    <tr>
      <td><code>GET</code></td>
      <td><code>/</code></td>
      <td>None</td>
      <td><code>302</code> redirect</td>
      <td><strong>Modified (Phase 1).</strong> Now accepts <code>request: Request</code> and
          checks <code>User-Agent</code> header against
          <code>/Android|iPhone|iPod|BlackBerry|IEMobile|Opera Mini/i</code>. Mobile UA &#8594;
          <code>302 /mobile</code>; desktop UA (or empty UA) &#8594; <code>302 /dashboard</code>
          (no regression). Uses <code>re.IGNORECASE</code> + <code>.search()</code>.</td>
    </tr>
  </tbody>
</table>

<h3>Python Changes &#8212; <code>riia-jun-release/src/rita/main.py</code></h3>
<ul>
  <li><code>import re</code> added to standard-library imports</li>
  <li><code>Request</code> added to <code>fastapi</code> import</li>
  <li><code>_MOBILE_UA_RE</code> module-level compiled regex constant added</li>
  <li><code>root()</code> signature updated to <code>root(request: Request)</code></li>
  <li>UA branch: mobile &#8594; <code>RedirectResponse("/mobile", 302)</code>; desktop &#8594;
      <code>RedirectResponse("/dashboard", 302)</code></li>
</ul>

<h3>Frontend &#8212; Mobile-Detect IIFE Snippet</h3>
<p>An 8-line synchronous IIFE inserted as the <strong>first <code>&lt;script&gt;</code> in
<code>&lt;head&gt;</code></strong> (after the viewport <code>&lt;meta&gt;</code> tag) on each of
the five desktop dashboard files. The snippet runs before any framework or module loads.</p>

<p><strong>Detection logic:</strong></p>
<ul>
  <li>UA regex: <code>/Android|iPhone|iPod|BlackBerry|IEMobile|Opera Mini/i</code></li>
  <li>Viewport fallback: <code>innerWidth &lt; 768 &amp;&amp; (pointer:coarse)</code> &#8212; catches
      tablets and convertibles</li>
  <li>Redirect target: <code>location.replace('/mobile?from=APPNAME')</code></li>
  <li>The <code>?from=APPNAME</code> parameter is silently ignored by <code>GET /mobile</code>
      (Phase 0 behaviour unchanged)</li>
</ul>

<h3>Dashboard Files Modified</h3>
<table>
  <thead>
    <tr><th>File</th><th>APPNAME token</th><th>Change</th></tr>
  </thead>
  <tbody>
    <tr><td><code>riia-jun-release/dashboard/rita.html</code></td><td><code>rita</code></td><td>Mobile-detect IIFE inserted as first &lt;script&gt; in &lt;head&gt;</td></tr>
    <tr><td><code>riia-jun-release/dashboard/fno.html</code></td><td><code>fno</code></td><td>Same insertion</td></tr>
    <tr><td><code>riia-jun-release/dashboard/ops.html</code></td><td><code>ops</code></td><td>Same insertion</td></tr>
    <tr><td><code>riia-jun-release/dashboard/ds.html</code></td><td><code>ds</code></td><td>Same insertion</td></tr>
    <tr><td><code>riia-jun-release/dashboard/investgame.html</code></td><td><code>investgame</code></td><td>Same insertion after viewport meta</td></tr>
  </tbody>
</table>
<p>Note: <code>investgame_v2.html</code> and <code>users.html</code> are explicitly excluded.</p>

<h3><code>?desktop=1</code> / sessionStorage Escape-Hatch</h3>
<ul>
  <li>Appending <code>?desktop=1</code> to any dashboard URL sets
      <code>sessionStorage.mobileBypass = '1'</code> and skips the redirect for the session</li>
  <li>The bypass persists across tab navigation within the same browser session (sessionStorage scope)</li>
  <li>Clearing sessionStorage or opening a new tab resets the bypass</li>
  <li>The gateway page&#8217;s <em>Desktop Only</em> card links (e.g.
      <code>/dashboard/fno.html?desktop=1</code>) rely on this convention</li>
</ul>

<h3>Spec Updates</h3>
<ul>
  <li><code>project-office/specs/Spec_Mobile_App.md</code> &#8212; Section 8 added: Phase 1 UA
      detection, JS snippet pattern, APPNAME table, escape-hatch convention, agent directives.
      Phase 0 &#8220;do not add UA detection&#8221; directive struck through and lifted.</li>
  <li><code>project-office/specs/Spec_RITA_App.md</code> &#8212; <code>GET /</code> entrypoint
      bullet updated to reflect UA-based conditional redirect</li>
</ul>

<h3>Test Coverage</h3>
<ul>
  <li>Test file: <code>riia-jun-release/tests/unit/test_mobile_detection.py</code> &#8212; 6 tests, all passing</li>
  <li>Cases covered: Android UA &#8594; <code>/mobile</code>, desktop UA &#8594; <code>/dashboard</code>,
      empty UA &#8594; <code>/dashboard</code>, lowercase <code>android</code> (case-insensitive match),
      plain Opera (no false positive), iPhone UA &#8594; <code>/mobile</code></li>
  <li>Regression: <code>test_mobile_gateway.py</code> (Phase 0) &#8212; 16/16 passed</li>
</ul>

<h3>Commit</h3>
<p><code>3c92cda</code> &#8212; Feature 17 Phase 1: mobile UA detection in root() + dashboard JS redirect snippet</p>
"""


def main():
    print(f"Fetching Engineering page {PAGE_ID}...")
    page = get(f"content/{PAGE_ID}?expand=version,body.storage")
    title   = page["title"]
    version = page["version"]["number"]
    print(f"  Title: {title}  (version {version})")

    current_body = page["body"]["storage"]["value"]
    new_body = current_body + FEATURE17_PHASE1_HTML

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
