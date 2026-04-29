import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from confluence.publish import ConfluenceClient

client = ConfluenceClient()

# Check trashed state of test stub page
r, s = client._request("GET", "/content/74612756?status=trashed")
print(f"Trashed GET 74612756: HTTP {s}")
if isinstance(r, dict):
    print(json.dumps(r, indent=2)[:400])

# Permanently delete (status=trashed required for second DELETE)
r2, s2 = client._request("DELETE", "/content/74612756?status=trashed")
print(f"\nPermanent DELETE: HTTP {s2}")
