"""Check Engineering page current state."""
import urllib.request, json, base64
from pathlib import Path

PAGE_ID = "76611602"
EMAIL   = Path("confluence-api-key.txt").read_text().splitlines()[1].strip()
TOKEN   = Path("confluence-api-key.txt").read_text().splitlines()[0].strip()
BASE    = "https://ravionics.atlassian.net/wiki/rest/api"

creds   = base64.b64encode(f"{EMAIL}:{TOKEN}".encode()).decode()
HEADERS = {"Authorization": f"Basic {creds}", "Content-Type": "application/json"}

req = urllib.request.Request(
    f"{BASE}/content/{PAGE_ID}?expand=body.storage,version", headers=HEADERS
)
with urllib.request.urlopen(req) as r:
    page = json.loads(r.read())

title   = page["title"]
version = page["version"]["number"]
body    = page["body"]["storage"]["value"]
print(f"TITLE: {title}")
print(f"VERSION: {version}")
print(f"BODY_LEN: {len(body)}")
print(f"Run A marker present: {'instrument-onboard-2026-05-18' in body}")
print(f"Run B marker present: {'instrument-onboard-runb-2026-05-18' in body}")
print("--- LAST 2000 chars ---")
print(body[-2000:])
