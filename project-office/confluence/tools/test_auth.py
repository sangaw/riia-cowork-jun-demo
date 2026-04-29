import sys, urllib.request, urllib.error, base64
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from confluence.publish import _load_token, EMAIL, BASE_URL

token = _load_token()
print(f"Email: {EMAIL}")
print(f"Token length: {len(token)}")
print(f"Token prefix: {token[:8]}...")

creds = base64.b64encode(f"{EMAIL}:{token}".encode()).decode()
req = urllib.request.Request(
    f"{BASE_URL}/space",
    headers={"Authorization": f"Basic {creds}", "Content-Type": "application/json"}
)
try:
    with urllib.request.urlopen(req) as r:
        print(f"Status: {r.status} — auth OK")
except urllib.error.HTTPError as e:
    body = e.read().decode()[:400]
    print(f"HTTP {e.code}: {body}")
