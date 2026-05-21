"""
Update the Engineering Confluence page (76611602) after Feature 18 —
User Traffic Dashboard (task-brief-20260521-1956).

Changes:
  - Append a "Feature 18" section documenting:
    - New ORM model: LoginEventModel (login_events table)
    - New repository: LoginEventRepository
    - New Pydantic schemas: UserTrafficSummary, DailyTrafficRow, UserTrafficResponse
    - New experience endpoint: GET /api/v1/experience/users/traffic
    - New frontend: dashboard/users.html + dashboard/js/users/main.js
    - Alembic migration 20260521_add_login_events applied
    - Auth gap noted (JWT not enforced on endpoint — follow-up required)

Run from project root:
    python project-office/confluence/_update_engineering_feature18_user_traffic.py
"""
import urllib.request, urllib.error, json, base64
from pathlib import Path

PAGE_ID = "76611602"
BASE    = "https://ravionics.atlassian.net/wiki/rest/api"

MARKER = "feature18-user-traffic-2026-05-21"

FEATURE18_SECTION = (
    f"\n<!-- {MARKER} -->\n"
    "<h2>Feature 18 &mdash; User Traffic Dashboard <small>2026-05-21</small></h2>\n"
    "<p>Anonymised login-event logging and a standalone KPI page showing total users, "
    "active users (today / week / month), all-time login count, and a 30-day daily "
    "breakdown bar chart. Engineer commit: <strong>8dd8796</strong> &mdash; Branch: "
    "worktree-agent-a0aa844b50ab94e25.</p>\n"

    "<h3>New API Endpoint</h3>\n"
    "<table>\n"
    "  <thead><tr><th>Method</th><th>Path</th><th>Tier</th><th>Description</th><th>Auth</th></tr></thead>\n"
    "  <tbody>\n"
    "  <tr>\n"
    "    <td><code>GET</code></td>\n"
    "    <td><code>/api/v1/experience/users/traffic</code></td>\n"
    "    <td>Experience</td>\n"
    "    <td>Returns aggregated login KPIs and 30-day daily breakdown &mdash; no PII. "
    "<code>UserTrafficResponse</code> with <code>summary</code> "
    "(total_users, active_today, active_this_week, active_this_month, total_logins_all_time) "
    "and <code>daily</code> list (date, unique_users, total_logins, new_registrations).</td>\n"
    "    <td>JWT (Bearer)</td>\n"
    "  </tr>\n"
    "  </tbody>\n"
    "</table>\n"

    "<h3>New Backend Files</h3>\n"
    "<table>\n"
    "  <thead><tr><th>File</th><th>Change</th></tr></thead>\n"
    "  <tbody>\n"
    "  <tr>\n"
    "    <td><code>src/rita/models/login_event.py</code></td>\n"
    "    <td>NEW &mdash; <code>LoginEventModel</code> ORM (login_events table: id, user_id FK, "
    "logged_at, ip_hash).</td>\n"
    "  </tr>\n"
    "  <tr>\n"
    "    <td><code>src/rita/models/__init__.py</code></td>\n"
    "    <td>Added <code>LoginEventModel</code> import and <code>__all__</code> entry.</td>\n"
    "  </tr>\n"
    "  <tr>\n"
    "    <td><code>src/rita/models/user.py</code></td>\n"
    "    <td>Added <code>first_login_date</code> column (nullable DateTime).</td>\n"
    "  </tr>\n"
    "  <tr>\n"
    "    <td><code>alembic/versions/20260521_add_login_events.py</code></td>\n"
    "    <td>NEW &mdash; migration: creates <code>login_events</code> table + adds "
    "<code>first_login_date</code> column to <code>users</code>. "
    "<strong>Applied: alembic upgrade head confirmed.</strong></td>\n"
    "  </tr>\n"
    "  <tr>\n"
    "    <td><code>src/rita/api/v1/auth.py</code></td>\n"
    "    <td>Inserts <code>LoginEventModel</code> row on every Google OAuth login; "
    "sets <code>first_login_date</code> when None (new user).</td>\n"
    "  </tr>\n"
    "  <tr>\n"
    "    <td><code>src/rita/repositories/login_event.py</code></td>\n"
    "    <td>NEW &mdash; <code>LoginEventRepository</code> with KPI aggregate queries "
    "and 30-day daily breakdown method.</td>\n"
    "  </tr>\n"
    "  <tr>\n"
    "    <td><code>src/rita/schemas/user_traffic.py</code></td>\n"
    "    <td>NEW &mdash; Pydantic schemas: <code>UserTrafficSummary</code>, "
    "<code>DailyTrafficRow</code>, <code>UserTrafficResponse</code>.</td>\n"
    "  </tr>\n"
    "  <tr>\n"
    "    <td><code>src/rita/api/experience/users.py</code></td>\n"
    "    <td>NEW &mdash; Experience router; GET <code>/api/v1/experience/users/traffic</code>. "
    "Read-only &mdash; no db.commit().</td>\n"
    "  </tr>\n"
    "  <tr>\n"
    "    <td><code>src/rita/main.py</code></td>\n"
    "    <td>Imported and registered <code>users_traffic_router</code> in Experience Layer block.</td>\n"
    "  </tr>\n"
    "  </tbody>\n"
    "</table>\n"

    "<h3>New Frontend Files</h3>\n"
    "<table>\n"
    "  <thead><tr><th>File</th><th>Description</th></tr></thead>\n"
    "  <tbody>\n"
    "  <tr>\n"
    "    <td><code>dashboard/users.html</code></td>\n"
    "    <td>Standalone User Traffic KPI page &mdash; 5 KPI tiles "
    "(total users, active today/week/month, all-time logins), a Chart.js bar chart "
    "showing 30-day daily logins, and a daily breakdown table.</td>\n"
    "  </tr>\n"
    "  <tr>\n"
    "    <td><code>dashboard/js/users/main.js</code></td>\n"
    "    <td>Standalone JS module &mdash; fetches <code>/api/v1/experience/users/traffic</code>, "
    "renders KPI DOM elements, Chart.js bar chart, daily table. "
    "JWT redirect guard on DOMContentLoaded. Uses <code>window.RITA_API_BASE || &quot;&quot;</code> "
    "for base URL.</td>\n"
    "  </tr>\n"
    "  <tr>\n"
    "    <td><code>dashboard/ops.html</code></td>\n"
    "    <td>Added User Traffic <code>&lt;a&gt;</code> nav link in Access sidebar section.</td>\n"
    "  </tr>\n"
    "  </tbody>\n"
    "</table>\n"

    "<h3>QA Coverage</h3>\n"
    "<p>24 unit tests written in <code>tests/unit/test_user_traffic.py</code> — all passed. "
    "Covers schemas, repository mock paths, experience endpoint, and auth callback. "
    "Estimated coverage delta: +8%.</p>\n"

    "<h3>Known Gap &mdash; JWT Auth</h3>\n"
    "<p><strong>Issue:</strong> The <code>users_traffic_router</code> is registered in "
    "<code>main.py</code> without <code>dependencies=[Depends(get_current_user)]</code>, "
    "making the endpoint publicly accessible. "
    "The Architect spec requires JWT auth.</p>\n"
    "<p><strong>Fix:</strong> Add <code>dependencies=[Depends(get_current_user)]</code> "
    "to the <code>include_router</code> call in <code>main.py</code> line 328. "
    "Tracked as a follow-up task.</p>\n"

    "<h3>Spec Updates</h3>\n"
    "<ul>\n"
    "  <li><code>Spec_RITA_App.md</code> &mdash; Added <code>users.py</code> router row "
    "and Users Experience Endpoints table section (verified present).</li>\n"
    "  <li><code>Spec_JS_Code.md</code> &mdash; Added Section 5: "
    "<code>dashboard/js/users/</code> module table with <code>users/main.js</code> "
    "(verified present).</li>\n"
    "</ul>\n"
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
        print(f"NOTE: Feature 18 section already present (marker: {MARKER}) — skipping")
        return

    body_updated = body + FEATURE18_SECTION

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
