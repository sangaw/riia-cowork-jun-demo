"""
Update the Engineering Confluence page (76611602) after Feature 28 Phase 1 —
Portfolio Builder UI for FnO dashboard (task-brief-20260531-2042).

Changes:
  - Append a "Feature 28 Phase 1" section documenting:
    - portfolio-builder.js new ES module (490 lines)
    - page-portfolio-builder section in fno.html
    - 3 view tabs: buckets / scatter map / table
    - sticky basket panel + Build Portfolio CTA
    - Reuses GET /api/v1/experience/rita/geography-overview
    - 34 unit tests in tests/unit/test_f28_portfolio_builder.py (all passing)

Run from project root:
    python project-office/confluence/_update_engineering_feature28_portfolio_builder.py
"""
import urllib.request, urllib.error, json, base64
from pathlib import Path

PAGE_ID = "76611602"
BASE    = "https://ravionics.atlassian.net/wiki/rest/api"

MARKER = "feature28-portfolio-builder-2026-05-31"

FEATURE28_SECTION = (
    f"\n<!-- {MARKER} -->\n"
    "<h2>Feature 28 Phase 1 &mdash; Portfolio Builder UI <small>2026-05-31</small></h2>\n"
    "<p>New FnO dashboard section that lets users browse available instruments grouped by "
    "geography region, select instruments into a basket, visualise risk vs. return on a "
    "scatter map, sort by any column in a table view, apply guided goal presets "
    "(Growth / Income / Balanced / Defensive), and submit a portfolio build request. "
    "Phase 1 is frontend-only; it reuses the existing geography-overview Experience tier "
    "endpoint and adds a placeholder POST to <code>/api/v1/user-portfolio/</code> (Phase 2). "
    "Engineer commit: <strong>6633251</strong> on branch "
    "<em>worktree-agent-a3249b76815a90cf5</em>.</p>\n"

    "<h3>API Endpoints Used</h3>\n"
    "<table>\n"
    "  <thead><tr><th>Method</th><th>Path</th><th>Tier</th><th>Auth</th><th>Notes</th></tr></thead>\n"
    "  <tbody>\n"
    "  <tr>\n"
    "    <td><code>GET</code></td>\n"
    "    <td><code>/api/v1/experience/rita/geography-overview</code></td>\n"
    "    <td>Experience</td>\n"
    "    <td>No</td>\n"
    "    <td>Primary data source. Returns <code>{ regions: GeoRegion[] }</code> with instruments "
    "per region (id, name, flag, close, daily_return_pct, signal). Pre-existing endpoint; "
    "reused by portfolio-builder.js.</td>\n"
    "  </tr>\n"
    "  <tr>\n"
    "    <td><code>GET</code></td>\n"
    "    <td><code>/api/v1/experience/user-portfolio</code></td>\n"
    "    <td>Experience</td>\n"
    "    <td>JWT</td>\n"
    "    <td>Pre-fill existing basket from saved portfolio. Silent 404 if no portfolio exists.</td>\n"
    "  </tr>\n"
    "  <tr>\n"
    "    <td><code>POST</code></td>\n"
    "    <td><code>/api/v1/user-portfolio/</code></td>\n"
    "    <td>System (Phase 2 placeholder)</td>\n"
    "    <td>JWT</td>\n"
    "    <td>Not yet implemented. Stub gracefully surfaces failure via "
    "<code>pb-status-msg</code> banner. Phase 2 will implement this endpoint.</td>\n"
    "  </tr>\n"
    "  </tbody>\n"
    "</table>\n"

    "<h3>Frontend Module &mdash; portfolio-builder.js</h3>\n"
    "<table>\n"
    "  <thead><tr><th>Item</th><th>Value</th></tr></thead>\n"
    "  <tbody>\n"
    "  <tr><td>File</td><td><code>dashboard/js/fno/portfolio-builder.js</code></td></tr>\n"
    "  <tr><td>Size</td><td>490 lines — new ES module</td></tr>\n"
    "  <tr><td>Entry function</td><td><code>loadPortfolioBuilder()</code></td></tr>\n"
    "  <tr><td>Section ID</td><td><code>page-portfolio-builder</code></td></tr>\n"
    "  <tr><td>Nav data-page</td><td><code>portfolio-builder</code></td></tr>\n"
    "  <tr><td>Basket state</td><td>Module-level <code>const _basket = new Set()</code> "
    "&mdash; persists across tab switches within a page load</td></tr>\n"
    "  </tbody>\n"
    "</table>\n"

    "<h3>UI Structure</h3>\n"
    "<table>\n"
    "  <thead><tr><th>View / Panel</th><th>Description</th></tr></thead>\n"
    "  <tbody>\n"
    "  <tr>\n"
    "    <td>Buckets view (<code>pb-tab-buckets</code>)</td>\n"
    "    <td>Instruments grouped by region (India / US / Europe / Other). Each card shows "
    "name, flag, close price, daily return %, and signal badge. Checkbox toggle adds/removes "
    "instrument from basket. Select-all / Clear-all per region.</td>\n"
    "  </tr>\n"
    "  <tr>\n"
    "    <td>Scatter map view (<code>pb-tab-map</code>)</td>\n"
    "    <td>Canvas scatter plot of all instruments — X axis: estimated risk (1&ndash;5 scale "
    "derived from <code>abs(daily_return_pct)</code>), Y axis: estimated return "
    "(<code>daily_return_pct</code>). Selected basket instruments highlighted. "
    "Values labeled &ldquo;(est.)&rdquo; to distinguish from authoritative signals.</td>\n"
    "  </tr>\n"
    "  <tr>\n"
    "    <td>Table view (<code>pb-tab-table</code>)</td>\n"
    "    <td>Sortable table of all instruments. Columns: instrument, region, close, "
    "daily return %, signal, est. risk, action. Click column header to sort ascending/descending.</td>\n"
    "  </tr>\n"
    "  <tr>\n"
    "    <td>Guided goal presets (<code>pb-guided-wrap</code>)</td>\n"
    "    <td>Four goal buttons: Growth, Income, Balanced, Defensive. Each preset applies a "
    "filter rule to populate a draft instrument list. "
    "<code>pbAddFromDraft()</code> adds draft to basket.</td>\n"
    "  </tr>\n"
    "  <tr>\n"
    "    <td>Sticky basket panel (<code>pb-basket-wrap</code>)</td>\n"
    "    <td>Shows count of selected instruments, basket list with remove buttons, "
    "portfolio name input, Build Portfolio CTA (<code>pb-basket-build-btn</code>), "
    "and Clear All button. Sticky positioned so it stays visible while scrolling buckets.</td>\n"
    "  </tr>\n"
    "  </tbody>\n"
    "</table>\n"

    "<h3>Window Bindings (registered in main.js)</h3>\n"
    "<p><code>loadPortfolioBuilder</code>, <code>pbToggleInstrument</code>, "
    "<code>pbSelectAllRegion</code>, <code>pbClearAllRegion</code>, "
    "<code>pbSortTable</code>, <code>pbApplyGoalPreset</code>, "
    "<code>pbAddFromDraft</code>, <code>pbClearBasket</code>, "
    "<code>pbBuildPortfolio</code>, <code>pbSwitchTab</code> "
    "&mdash; 10 bindings total.</p>\n"

    "<h3>Files Changed</h3>\n"
    "<table>\n"
    "  <thead><tr><th>File</th><th>Action</th></tr></thead>\n"
    "  <tbody>\n"
    "  <tr><td><code>dashboard/js/fno/portfolio-builder.js</code></td>"
    "<td>Created &mdash; new 490-line ES module</td></tr>\n"
    "  <tr><td><code>dashboard/js/fno/main.js</code></td>"
    "<td>Modified &mdash; import + 10 window bindings</td></tr>\n"
    "  <tr><td><code>dashboard/js/fno/nav.js</code></td>"
    "<td>Modified &mdash; portfolio-builder nav handler</td></tr>\n"
    "  <tr><td><code>dashboard/fno.html</code></td>"
    "<td>Modified &mdash; nav item + full section HTML (~130 lines)</td></tr>\n"
    "  <tr><td><code>project-office/specs/Spec_RITA_App.md</code></td>"
    "<td>Modified &mdash; geography-overview row updated with portfolio-builder reuse note</td></tr>\n"
    "  <tr><td><code>project-office/specs/Spec_JS_Code.md</code></td>"
    "<td>Modified &mdash; portfolio-builder.js row added to Section 3</td></tr>\n"
    "  </tbody>\n"
    "</table>\n"

    "<h3>QA Coverage</h3>\n"
    "<p>34 unit tests in <code>tests/unit/test_f28_portfolio_builder.py</code> &mdash; "
    "all 34 passed. Coverage across 3 test classes: "
    "<code>TestGeographyOverviewSchema</code>, <code>TestGeographyOverviewEndpoint</code>, "
    "<code>TestPortfolioBuilderEdgeCases</code>. "
    "Edge cases include empty instrument list, all-null price cache, single cache row, "
    "bullish/bearish/neutral signal thresholds, absent-from-cache graceful degradation, "
    "cache repository exception (no 500), and POST body allocation totalling 100%.</p>\n"

    "<h3>Spec Updates</h3>\n"
    "<ul>\n"
    "  <li><code>Spec_RITA_App.md</code> line 99 &mdash; "
    "<code>GET /api/v1/experience/rita/geography-overview</code> row updated: "
    "added reuse note for <code>portfolio-builder.js</code> (Feature 28 Phase 1).</li>\n"
    "  <li><code>Spec_JS_Code.md</code> line 72 &mdash; "
    "<code>portfolio-builder.js</code> module row added to Section 3.</li>\n"
    "</ul>\n"

    "<h3>Known Follow-up Items</h3>\n"
    "<ul>\n"
    "  <li>Reviewer Finding #1 (advisory): null <code>daily_return_pct</code> renders green color "
    "due to JS <code>null &gt;= 0</code> coercion (line 97 of portfolio-builder.js). "
    "Cosmetic only; fix scheduled for Phase 1 follow-up pass "
    "(<code>(inst.daily_return_pct ?? 0) &gt;= 0</code>).</li>\n"
    "  <li>Phase 2: implement <code>POST /api/v1/user-portfolio/</code> endpoint so "
    "Build Portfolio CTA succeeds at runtime.</li>\n"
    "</ul>\n"
)


def get_page(path, headers):
    req = urllib.request.Request(f"{BASE}/{path}", headers=headers)
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())


def put_page(path, payload, headers):
    data = json.dumps(payload).encode()
    req = urllib.request.Request(f"{BASE}/{path}", data=data, headers=headers, method="PUT")
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read()), r.status
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        return (json.loads(raw) if raw.strip() else {}), e.code


def main():
    print(f"Fetching Engineering page {PAGE_ID}...")
    page    = get_page(f"content/{PAGE_ID}?expand=version,body.storage", HEADERS)
    title   = page["title"]
    version = page["version"]["number"]
    body    = page["body"]["storage"]["value"]
    print(f"  Title: {title}  (version {version}, {len(body)} chars)")

    if MARKER in body:
        print(f"NOTE: Feature 28 section already present (marker: {MARKER}) — skipping")
        url = f"https://ravionics.atlassian.net/wiki/spaces/RIIAProjec/pages/{PAGE_ID}"
        print(f"  URL: {url}")
        return url

    body_updated = body + FEATURE28_SECTION

    # Bump version date in page header if present
    for old_date in ("2026-05-30", "2026-05-29", "2026-05-28", "2026-05-27",
                     "2026-05-26", "2026-05-25", "2026-05-24", "2026-05-23"):
        if f"<strong>Date:</strong> {old_date}" in body_updated:
            body_updated = body_updated.replace(
                f"<strong>Date:</strong> {old_date}",
                "<strong>Date:</strong> 2026-05-31",
                1,
            )
            print(f"OK: version date bumped from {old_date} to 2026-05-31")
            break
    else:
        if "<strong>Date:</strong> 2026-05-31" in body_updated:
            print("NOTE: date already at 2026-05-31")

    payload = {
        "version": {"number": version + 1},
        "title":   title,
        "type":    "page",
        "body":    {"storage": {"value": body_updated, "representation": "storage"}},
    }

    result, status = put_page(f"content/{PAGE_ID}", payload, HEADERS)
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
        print("Spec edits are complete. Re-run this script after adding the key file.")
        raise SystemExit(0)

    creds   = base64.b64encode(f"{EMAIL}:{TOKEN}".encode()).decode()
    HEADERS = {
        "Authorization": f"Basic {creds}",
        "Content-Type":  "application/json",
        "Accept":        "application/json",
    }

    url = main()
    print(f"\nDone. Engineering page: {url}")
