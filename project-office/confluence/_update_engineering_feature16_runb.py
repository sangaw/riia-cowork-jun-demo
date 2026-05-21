"""
Update the Engineering Confluence page (76611602) after Feature 16 Run B —
Spec + Documentation update (task-brief-20260521-0942).

Changes:
  - Append a "Feature 16 Run B" section documenting:
    - Spec_Data.md edits: _yf.csv companion rows, manual CSV retired as primary feed,
      Section 6 automated workflow prose, Section 9 rule 5 directive updated
    - Spec_Python_Code.md edits: load_instrument_data() 3-phase merge docstring,
      new data_refresh.py (Feature 16) subsection with all 5 function signatures
    - Spec_RITA_App.md: confirmed present at line 119 — no edit needed
    - Scope note: no new code in Run B

Run from project root:
    python project-office/confluence/_update_engineering_feature16_runb.py
"""
import urllib.request, urllib.error, json, base64
from pathlib import Path

PAGE_ID = "76611602"
BASE    = "https://ravionics.atlassian.net/wiki/rest/api"

MARKER = "feature16-runb-2026-05-21"

RUNB_SECTION = (
    f"\n<!-- {MARKER} -->\n"
    "<h2>Feature 16 Run B &mdash; Spec + Documentation <small>2026-05-21</small></h2>\n"
    "<p>Documentation-only run. No new backend code. All source files referenced below were "
    "shipped in Run A (commit e920177, merged to master 2026-05-20). Run B updates the spec "
    "files to reflect the as-built state and retires the legacy manual CSV workflow description.</p>\n"

    "<h3>Spec_Data.md Updates</h3>\n"
    "<table>\n"
    "  <thead><tr><th>Section</th><th>Change</th></tr></thead>\n"
    "  <tbody>\n"
    "  <tr>\n"
    "    <td>Section 2 &mdash; NIFTY file table</td>\n"
    "    <td>Added companion file row: <code>data/raw/NIFTY/nifty_yf.csv</code> "
    "(varies rows, 2009-09-01 &rarr; present) &mdash; written by data_refresh service "
    "(Feature 16); merged into training data by <code>load_instrument_data()</code>.</td>\n"
    "  </tr>\n"
    "  <tr>\n"
    "    <td>Section 2 &mdash; BANKNIFTY file table</td>\n"
    "    <td>Added companion file row: <code>data/raw/BANKNIFTY/banknifty_yf.csv</code> "
    "(same pattern as NIFTY).</td>\n"
    "  </tr>\n"
    "  <tr>\n"
    "    <td>Section 3 &mdash; Daily FnO Records table</td>\n"
    "    <td>Updated <code>nifty_manual.csv</code> and <code>banknifty_manual.csv</code> "
    "descriptions to &ldquo;manual supplement; still merged by "
    "<code>load_instrument_data()</code>, but automated refresh via Feature 16 is now "
    "the primary live feed.&rdquo;</td>\n"
    "  </tr>\n"
    "  <tr>\n"
    "    <td>Section 6 &mdash; Adding New Daily Data</td>\n"
    "    <td>Replaced legacy &ldquo;append to nifty_manual.csv manually&rdquo; prose with "
    "automated workflow description: use <code>POST /api/v1/instrument/refresh-all</code> "
    "or <code>/refresh-all-instruments-data</code> slash command. Manual files retained as "
    "supplement.</td>\n"
    "  </tr>\n"
    "  <tr>\n"
    "    <td>Section 9 &mdash; AI Agent Directives (rule 5)</td>\n"
    "    <td>Updated directive from &ldquo;nifty_manual.csv is the live feed&rdquo; to "
    "&ldquo;Automated refresh via <code>POST /api/v1/instrument/refresh-all</code> is the "
    "primary live feed. nifty_manual.csv is a manual supplement.&rdquo;</td>\n"
    "  </tr>\n"
    "  </tbody>\n"
    "</table>\n"

    "<h3>Spec_Python_Code.md Updates</h3>\n"
    "<table>\n"
    "  <thead><tr><th>Location</th><th>Change</th></tr></thead>\n"
    "  <tbody>\n"
    "  <tr>\n"
    "    <td><code>load_instrument_data()</code> docstring</td>\n"
    "    <td>Expanded to describe the three-phase merge: (1) primary CSV via "
    "<code>find_instrument_csv()</code>, (2) manual supplement "
    "<code>data/input/DAILY-DATA/{lower}_manual.csv</code> if exists, "
    "(3) yfinance companion <code>data/raw/{INSTRUMENT}/{lower}_yf.csv</code> if exists "
    "(Feature 16). Deduplicates with <code>keep=&#39;last&#39;</code> at each step.</td>\n"
    "  </tr>\n"
    "  <tr>\n"
    "    <td>New subsection after <code>instrument_onboard.py (Feature 09)</code></td>\n"
    "    <td>Added <strong><code>data_refresh.py</code> (Feature 16)</strong> subsection with "
    "constants (<code>YF_TICKER_MAP</code>, <code>COMPANION_FILE_INSTRUMENTS</code>, "
    "<code>SKIP_INSTRUMENTS</code>) and all 5 function signatures: <code>check_gap()</code>, "
    "<code>fetch_and_write_raw()</code>, <code>rebuild_input()</code>, "
    "<code>upsert_cache_delta()</code>, <code>refresh_all()</code>. Also notes endpoint, "
    "slash command, and standalone script.</td>\n"
    "  </tr>\n"
    "  </tbody>\n"
    "</table>\n"

    "<h3>Spec_RITA_App.md</h3>\n"
    "<p>Verified: <code>POST /api/v1/instrument/refresh-all</code> already present at line 119 "
    "(added in Run A). No edit required.</p>\n"

    "<h3>Companion File Pattern (NIFTY / BANKNIFTY)</h3>\n"
    "<p>NIFTY and BANKNIFTY use a full-overwrite strategy: the data_refresh service writes "
    "the entire yfinance history to <code>_yf.csv</code> on each run. Other instruments "
    "append delta rows to their existing <code>_daily.csv</code>. "
    "<code>load_instrument_data()</code> merges all three sources at load time, "
    "deduplicating with <code>keep=&#39;last&#39;</code> (so yfinance data wins on overlap "
    "with manual entries).</p>\n"

    "<h3>Scope Note</h3>\n"
    "<p>Run B is documentation-only. No new Python code, no migrations, no JS, no HTML changes. "
    "All source code (service, endpoint, slash command, Alembic migration, unit tests) was "
    "delivered in Run A at commit e920177.</p>\n"
    "<p><strong>Commit (Run B):</strong> to be filled by Engineer Agent &mdash; Branch: master</p>\n"
)


def get_page(path):
    req = urllib.request.Request(f"{BASE}/{path}", headers=HEADERS)
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())


def put_page(path, payload):
    data = json.dumps(payload).encode()
    req = urllib.request.Request(f"{BASE}/{path}", data=data, headers=HEADERS, method="PUT")
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read()), r.status
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        return (json.loads(raw) if raw.strip() else {}), e.code


def main():
    print(f"Fetching Engineering page {PAGE_ID}...")
    page    = get_page(f"content/{PAGE_ID}?expand=version,body.storage")
    title   = page["title"]
    version = page["version"]["number"]
    body    = page["body"]["storage"]["value"]
    print(f"  Title: {title}  (version {version}, {len(body)} chars)")

    if MARKER in body:
        print(f"NOTE: Run B section already present (marker: {MARKER}) — skipping")
        return

    body_updated = body + RUNB_SECTION

    # Bump version date in page header if present
    for old_date in ("2026-05-20", "2026-05-19", "2026-05-18", "2026-05-17",
                     "2026-05-16", "2026-05-15", "2026-05-14", "2026-05-11"):
        if f"<strong>Date:</strong> {old_date}" in body_updated:
            body_updated = body_updated.replace(
                f"<strong>Date:</strong> {old_date}",
                "<strong>Date:</strong> 2026-05-21",
                1,
            )
            print(f"OK: version date bumped from {old_date} to 2026-05-21")
            break
    else:
        if "<strong>Date:</strong> 2026-05-21" in body_updated:
            print("NOTE: date already at 2026-05-21")

    payload = {
        "version": {"number": version + 1},
        "title":   title,
        "type":    "page",
        "body":    {"storage": {"value": body_updated, "representation": "storage"}},
    }

    result, status = put_page(f"content/{PAGE_ID}", payload)
    if status == 200:
        url = f"https://ravionics.atlassian.net/wiki{result['_links']['webui']}"
        print(f"OK: Page updated to v{version + 1}")
        print(f"  URL: {url}")
        return url
    else:
        raise RuntimeError(f"Update failed: HTTP {status} — {result.get('message', '')[:200]}")


if __name__ == "__main__":
    try:
        key_file = Path("confluence-api-key.txt")
        TOKEN = key_file.read_text().splitlines()[0].strip()
        EMAIL = key_file.read_text().splitlines()[1].strip()
    except FileNotFoundError:
        print("SKIP: confluence-api-key.txt not found — Confluence update skipped.")
        print("Spec edits are complete and committed. Re-run this script after adding the key file.")
        raise SystemExit(0)

    creds   = base64.b64encode(f"{EMAIL}:{TOKEN}".encode()).decode()
    HEADERS = {
        "Authorization": f"Basic {creds}",
        "Content-Type":  "application/json",
        "Accept":        "application/json",
    }

    url = main()
    print(f"\nDone. Engineering page: {url}")
