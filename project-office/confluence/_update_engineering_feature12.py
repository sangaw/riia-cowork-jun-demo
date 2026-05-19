"""
Update the Engineering Confluence page (76611602) for Feature 12 agent-ops path migration.

Changes:
  - Append a Feature 12 section documenting the migration of agent-ops data files
    from riia-ai-org/ to riia-jun-release/data/agent-ops/ and utility scripts to
    project-office/scripts/agent-ops/.

Run from project root:
    python project-office/confluence/_update_engineering_feature12.py
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


MIGRATION_HTML = """
<h2>Feature 12 &#8212; Agent-Ops Path Migration (2026-05-19)</h2>
<p>All agent-ops operational data and utility scripts have been relocated out of the non-deployable
<code>riia-ai-org/</code> POC folder into the production repository. No API contracts or JS modules
were changed &#8212; this is an internal path fix only.</p>
<h3>Data Files</h3>
<ul>
  <li><strong>Old location:</strong> <code>riia-ai-org/agent-ops/metrics.json</code> and
      <code>riia-ai-org/agent-ops/runs/*.json</code></li>
  <li><strong>New location:</strong> <code>riia-jun-release/data/agent-ops/metrics.json</code> and
      <code>riia-jun-release/data/agent-ops/runs/*.json</code></li>
  <li>41 run JSON files relocated; <code>metrics.json</code> (all 7 KPI sections) verified present.</li>
</ul>
<h3>Utility Scripts</h3>
<ul>
  <li><strong>Old location:</strong> <code>riia-ai-org/agent-ops/aggregate_metrics.py</code>,
      <code>write_run_to_db.py</code>, <code>backfill_metrics.py</code>,
      <code>seed_agent_builds.py</code></li>
  <li><strong>New location:</strong> <code>project-office/scripts/agent-ops/</code></li>
  <li>All four scripts updated with corrected <code>parents[N]</code> path indices.</li>
</ul>
<h3>Git Tracking</h3>
<ul>
  <li><code>riia-ai-org/</code> added to <code>.gitignore</code></li>
  <li><code>git rm --cached -r riia-ai-org/</code> executed &#8212; POC folder removed from git index
      (files remain on disk)</li>
</ul>
<h3>Affected Source Files</h3>
<ul>
  <li><code>riia-jun-release/src/rita/api/experience/ops.py</code> &#8212; 2 path expressions corrected
      (<code>get_agent_builds</code> and <code>get_token_forecast</code>)</li>
  <li><code>riia-jun-release/src/rita/api/experience/invest_game.py</code> &#8212;
      <code>_AGENT_OPS_RUNS</code> path corrected</li>
  <li><code>riia-jun-release/src/rita/main.py</code> &#8212; static mount path corrected</li>
</ul>
<p><em>Endpoints unchanged externally:
GET /api/experience/ops/agent-builds and GET /api/experience/ops/token-forecast
continue to serve the same response contracts.</em></p>
"""


def main():
    print(f"Fetching Engineering page {PAGE_ID}...")
    page = get(f"content/{PAGE_ID}?expand=version,body.storage")
    title   = page["title"]
    version = page["version"]["number"]
    print(f"  Title: {title}  (version {version})")

    current_body = page["body"]["storage"]["value"]
    new_body = current_body + MIGRATION_HTML

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
