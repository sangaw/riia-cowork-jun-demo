"""Test create_page against engineering parent — full error body."""
import urllib.request, urllib.error, json, base64
from pathlib import Path

key_file = Path(__file__).parent.parent.parent / "confluence-api-key.txt"
lines = [l.strip() for l in key_file.read_text().splitlines() if l.strip()]
token = lines[0]
email = lines[1] if len(lines) >= 2 else ""

creds = base64.b64encode(f"{email}:{token}".encode()).decode()
headers = {
    "Authorization": f"Basic {creds}",
    "Content-Type": "application/json",
    "Accept": "application/json",
}

PARENT_ID = "65404944"  # engineering section

# Test 1: can we read the parent page?
print("--- Test: GET parent page ---")
req = urllib.request.Request(
    f"https://ravionics.atlassian.net/wiki/rest/api/content/{PARENT_ID}?expand=version",
    headers=headers,
)
try:
    with urllib.request.urlopen(req) as r:
        data = json.loads(r.read())
        print(f"SUCCESS — title: {data.get('title')}, id: {data.get('id')}")
except urllib.error.HTTPError as e:
    print(f"HTTP {e.code}: {e.read().decode()[:500]}")

# Test 2: try creating a minimal test page
print("\n--- Test: POST create page (minimal) ---")
payload = {
    "type": "page",
    "title": "DIAGNOSTIC TEST — delete me",
    "space": {"key": "RIIAProjec"},
    "ancestors": [{"id": PARENT_ID}],
    "body": {"storage": {"value": "<p>test</p>", "representation": "storage"}},
}
data_bytes = json.dumps(payload).encode()
req2 = urllib.request.Request(
    "https://ravionics.atlassian.net/wiki/rest/api/content",
    data=data_bytes,
    headers=headers,
    method="POST",
)
try:
    with urllib.request.urlopen(req2) as r:
        data = json.loads(r.read())
        print(f"SUCCESS — created page id: {data.get('id')}, title: {data.get('title')}")
        # Clean up immediately
        del_req = urllib.request.Request(
            f"https://ravionics.atlassian.net/wiki/rest/api/content/{data['id']}",
            headers=headers,
            method="DELETE",
        )
        try:
            with urllib.request.urlopen(del_req) as r2:
                print("Cleaned up (deleted test page)")
        except Exception as e:
            print(f"Cleanup failed: {e}")
except urllib.error.HTTPError as e:
    print(f"HTTP {e.code}: {e.read().decode()[:800]}")
