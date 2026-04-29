"""Diagnose the 403 — compare what test_create.py did vs the main scripts."""
import sys, json, base64, urllib.request, urllib.error
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from confluence.publish import _load_token, EMAIL, BASE_URL, SPACE_KEY, SECTION

token = _load_token()
print(f"=== Auth check ===")
print(f"EMAIL loaded by publish.py : '{EMAIL}'")
print(f"Token length               : {len(token)}")

def make_headers(email):
    creds = base64.b64encode(f"{email}:{token}".encode()).decode()
    return {"Authorization": f"Basic {creds}", "Content-Type": "application/json", "Accept": "application/json"}

def try_create(label, email, body_html):
    headers = make_headers(email)
    payload = json.dumps({
        "type": "page",
        "title": f"__DIAGNOSE_TEST__ {label}",
        "space": {"key": SPACE_KEY},
        "ancestors": [{"id": SECTION["architecture"]}],
        "body": {"storage": {"value": body_html, "representation": "storage"}},
    }).encode()
    req = urllib.request.Request(f"{BASE_URL}/content", data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as r:
            result = json.loads(r.read())
            print(f"[{label}] HTTP 200/201 — page_id={result['id']}")
            # clean up
            del_req = urllib.request.Request(f"{BASE_URL}/content/{result['id']}", headers=headers, method="DELETE")
            try: urllib.request.urlopen(del_req)
            except: pass
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"[{label}] HTTP {e.code} — {body[:200]}")

# Test 1: no email (what test_create.py does implicitly when EMAIL='')
try_create("no-email, small body", "", "<p>test</p>")

# Test 2: with email, small body
try_create("with-email, small body", EMAIL, "<p>test</p>")

# Test 3: no email, large body (like main script)
large = "<h1>Test</h1>" + "<p>Some content with code: <code>def foo(): pass</code></p>" * 20
try_create("no-email, large body", "", large)

# Test 4: with email, large body
try_create("with-email, large body", EMAIL, large)
