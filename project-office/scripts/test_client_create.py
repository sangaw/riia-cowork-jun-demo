"""Test ConfluenceClient.create_page with full error output."""
import sys, os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))  # inserts project-office/

if not os.environ.get("CONFLUENCE_EMAIL"):
    os.environ["CONFLUENCE_EMAIL"] = "contact@ravionics.nl"

if not os.environ.get("CONFLUENCE_API_TOKEN"):
    for ancestor in Path(__file__).resolve().parents:
        candidate = ancestor / "confluence-api-key.txt"
        if candidate.exists():
            os.environ["CONFLUENCE_API_TOKEN"] = candidate.read_text().strip()
            break

from confluence.publish import ConfluenceClient, SECTION, EMAIL
import urllib.request, urllib.error, json

print(f"EMAIL resolved to: '{EMAIL}'")
print(f"Token length: {len(os.environ.get('CONFLUENCE_API_TOKEN',''))} chars")

client = ConfluenceClient()

# Try a minimal create under engineering
payload = {
    "type": "page",
    "title": "DIAGNOSTIC — delete me",
    "space": {"key": "RIIAProjec"},
    "ancestors": [{"id": SECTION["engineering"]}],
    "body": {"storage": {"value": "<p>test</p>", "representation": "storage"}},
}

import urllib.request, urllib.error, json
data_bytes = json.dumps(payload).encode()
req = urllib.request.Request(
    "https://ravionics.atlassian.net/wiki/rest/api/content",
    data=data_bytes,
    headers=client.headers,
    method="POST",
)
try:
    with urllib.request.urlopen(req) as r:
        data = json.loads(r.read())
        pid = data.get("id")
        print(f"SUCCESS — page id: {pid}")
        # delete it
        urllib.request.urlopen(urllib.request.Request(
            f"https://ravionics.atlassian.net/wiki/rest/api/content/{pid}",
            headers=client.headers, method="DELETE"
        ))
        print("Cleaned up.")
except urllib.error.HTTPError as e:
    body = e.read().decode()
    print(f"HTTP {e.code}")
    print(f"Full response: {body[:1000]}")
    print(f"Auth header: {client.headers['Authorization'][:40]}...")
