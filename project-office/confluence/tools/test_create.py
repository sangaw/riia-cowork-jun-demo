import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from confluence.publish import ConfluenceClient, SECTION

client = ConfluenceClient()
arch_id = SECTION["architecture"]

# Check parent page accessible
result, status = client._request("GET", f"/content/{arch_id}?expand=version")
print(f"Architecture parent GET: HTTP {status}")
if status == 200:
    print(f"  Title: {result['title']}")

# Check for existing chat pages
result2, status2 = client._request("GET", f"/content/{arch_id}/child/page?limit=50")
print(f"\nChildren of architecture: HTTP {status2}")
if status2 == 200:
    for p in result2.get("results", []):
        print(f"  [{p['id']}] {p['title']}")

# Try a minimal create and print the full error
payload = {
    "type": "page",
    "title": "RITA Chat Feature — Architecture & Design",
    "space": {"key": "RIIAProjec"},
    "ancestors": [{"id": arch_id}],
    "body": {"storage": {"value": "<p>test</p>", "representation": "storage"}},
}
result3, status3 = client._request("POST", "/content", payload)
print(f"\nCreate attempt: HTTP {status3}")
print(json.dumps(result3, indent=2)[:600])
