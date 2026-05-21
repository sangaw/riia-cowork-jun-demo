"""
Update the Engineering Confluence page (76611602) for Feature 16 Run A —
All Instruments Data Refresh Command.

Changes:
  - Append a Feature 16 section documenting:
    - POST /api/v1/instrument/refresh-all endpoint
    - data_refresh.py service (5 functions)
    - yf_ticker DB column + Alembic migration
    - Slash command and standalone script

Run from project root:
    python project-office/confluence/_update_engineering_feature16_runa.py
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


FEATURE16_HTML = """
<h2>Feature 16 &#8212; All Instruments Data Refresh Command (Run A, 2026-05-20)</h2>
<p>Adds an automated delta-refresh pipeline for all 11 instruments. Operators can refresh
all instrument price data from yfinance with a single endpoint call, slash command, or
standalone script &#8212; no manual CSV edits required.</p>

<h3>New API Endpoint</h3>
<table>
  <thead>
    <tr><th>Method</th><th>Path</th><th>Tier</th><th>Auth</th><th>Response</th><th>Description</th></tr>
  </thead>
  <tbody>
    <tr>
      <td><code>POST</code></td>
      <td><code>/api/v1/instrument/refresh-all</code></td>
      <td>Workflow (Tier 2)</td>
      <td>None</td>
      <td><code>RefreshAllResponse</code></td>
      <td>Fetches delta OHLCV data from yfinance for all 11 instruments (ATHER skipped),
          rebuilds input CSVs, and upserts new rows into <code>market_data_cache</code>.
          Returns per-instrument results with status <em>ok</em>, <em>current</em>, or
          <em>error</em>. Per-instrument errors do not abort the full loop.</td>
    </tr>
  </tbody>
</table>

<h3>Response Schema</h3>
<p><strong>RefreshAllResponse</strong> (<code>src/rita/schemas/data_refresh.py</code>):</p>
<ul>
  <li><code>refreshed</code> (int) &#8212; count where status == &#34;ok&#34;</li>
  <li><code>already_current</code> (int) &#8212; count where status == &#34;current&#34;</li>
  <li><code>results</code> (list of <code>InstrumentRefreshResult</code>) &#8212; one entry per instrument</li>
</ul>
<p><strong>InstrumentRefreshResult</strong> fields: <code>instrument</code>, <code>gap_days</code>,
<code>raw_rows_added</code>, <code>db_rows_inserted</code>, <code>status</code>, <code>error</code> (optional).</p>

<h3>New Service: data_refresh.py</h3>
<p>File: <code>src/rita/services/data_refresh.py</code></p>
<ul>
  <li><strong>check_gap(instrument, db)</strong> &#8212; queries <code>market_data_cache</code> for the
      most-recent date; returns gap in days to today.</li>
  <li><strong>fetch_and_write_raw(instrument, yf_ticker, gap_days)</strong> &#8212; calls yfinance for
      delta rows; for NIFTY/BANKNIFTY writes to companion <code>_yf.csv</code>; for all others
      appends to existing <code>_daily.csv</code>. Handles yfinance MultiIndex column flattening.</li>
  <li><strong>rebuild_input(instrument)</strong> &#8212; re-merges source CSV + companion file into
      the model input CSV; deduplicates with <code>keep=&#34;last&#34;</code> (yfinance wins on overlap).</li>
  <li><strong>upsert_cache_delta(instrument, rows, db)</strong> &#8212; inserts only new
      <code>(instrument, date)</code> pairs via <code>db.add_all()</code> with explicit
      date-existence check. No <code>db.merge()</code>, no DELETE.</li>
  <li><strong>refresh_all(db)</strong> &#8212; orchestrates the full pipeline for all instruments;
      returns list of per-instrument result dicts matching <code>InstrumentRefreshResult</code>.</li>
</ul>

<h3>Database Change</h3>
<ul>
  <li><strong>Migration:</strong> <code>riia-jun-release/alembic/versions/20260520_add_yf_ticker_to_instruments.py</code></li>
  <li>Adds <code>yf_ticker</code> VARCHAR nullable column to the <code>instruments</code> table.</li>
  <li>Backfilled for NIFTY (<code>^NSEI</code>) and BANKNIFTY (<code>^NSEBANK</code>) via updated
      <code>seed_new_instruments.py</code>. All 11 instruments have a yf_ticker value after seeding.</li>
</ul>

<h3>Operator Interface</h3>
<ul>
  <li><strong>Slash command:</strong> <code>/refresh-all-instruments-data</code> &#8212; invocable from
      Claude Code; calls the endpoint and prints a per-instrument gap report.</li>
  <li><strong>Standalone script:</strong> <code>project-office/scripts/run_data_refresh.py</code> &#8212;
      calls <code>POST /api/v1/instrument/refresh-all</code> and prints results; no Claude Code
      dependency.</li>
</ul>

<h3>Data File Patterns</h3>
<ul>
  <li>NIFTY: <code>data/raw/NIFTY/nifty_yf.csv</code> (companion file, written by refresh service)</li>
  <li>BANKNIFTY: <code>data/raw/BANKNIFTY/banknifty_yf.csv</code> (companion file)</li>
  <li>All other instruments: appended to existing <code>_daily.csv</code> in their <code>data/raw/</code>
      subdirectory.</li>
  <li>The legacy <code>nifty_manual.csv</code> / <code>banknifty_manual.csv</code> workflow is
      superseded &#8212; files retained but not required.</li>
</ul>

<h3>Test Coverage</h3>
<ul>
  <li>Test file: <code>riia-jun-release/tests/unit/test_data_refresh.py</code> &#8212; 8 tests, all passing.</li>
  <li>Edge cases covered: no-gap short-circuit (EC-1), yfinance error handling with loop continuation
      (EC-2), duplicate-insert prevention (EC-3).</li>
  <li>Coverage delta: ~+5% (data_refresh service + endpoint handler branch).</li>
</ul>

<h3>Scope Notes</h3>
<ul>
  <li>No ops.html UI panel and no JS module added in Run A. UI trigger panel may be added in a future
      run.</li>
  <li>Rita, FnO, and DS dashboards are unaffected &#8212; no experience-tier endpoint changes.</li>
</ul>
"""


def main():
    print(f"Fetching Engineering page {PAGE_ID}...")
    page = get(f"content/{PAGE_ID}?expand=version,body.storage")
    title   = page["title"]
    version = page["version"]["number"]
    print(f"  Title: {title}  (version {version})")

    current_body = page["body"]["storage"]["value"]
    new_body = current_body + FEATURE16_HTML

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
