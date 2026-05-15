"""Quick diagnostic — test Confluence API auth and report full error."""
import urllib.request, urllib.error, json, base64
from pathlib import Path

key_file = Path(__file__).parent.parent.parent / "confluence-api-key.txt"
lines = [l.strip() for l in key_file.read_text().splitlines() if l.strip()]
token = lines[0]
email = lines[1] if len(lines) >= 2 else ""

print(f"Email:        {email}")
print(f"Token length: {len(token)} chars")
print(f"Token prefix: {token[:20]}...")

creds = base64.b64encode(f"{email}:{token}".encode()).decode()
headers = {"Authorization": f"Basic {creds}", "Accept": "application/json"}

# Test 1: space lookup (read-only)
print("\n--- Test 1: GET space ---")
req = urllib.request.Request(
    "https://ravionics.atlassian.net/wiki/rest/api/space/RIIAProjec", headers=headers
)
try:
    with urllib.request.urlopen(req) as r:
        data = json.loads(r.read())
        print(f"SUCCESS — space key: {data.get('key')}, name: {data.get('name')}")
except urllib.error.HTTPError as e:
    body = e.read().decode()
    print(f"HTTP {e.code}: {body[:800]}")

# Test 2: current user
print("\n--- Test 2: GET current user ---")
req2 = urllib.request.Request(
    "https://ravionics.atlassian.net/wiki/rest/api/user/current", headers=headers
)
try:
    with urllib.request.urlopen(req2) as r:
        data = json.loads(r.read())
        print(f"SUCCESS — account: {data.get('accountId')}, email: {data.get('email')}")
except urllib.error.HTTPError as e:
    body = e.read().decode()
    print(f"HTTP {e.code}: {body[:800]}")
