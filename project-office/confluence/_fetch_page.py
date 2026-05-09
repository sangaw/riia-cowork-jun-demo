import sys, os, urllib.request, json, base64
from pathlib import Path

token = Path("confluence-api-key.txt").read_text().splitlines()[0].strip()
email = "contact@ravionics.nl"
creds = base64.b64encode(f"{email}:{token}".encode()).decode()
headers = {"Authorization": f"Basic {creds}", "Content-Type": "application/json"}

page_id = sys.argv[1] if len(sys.argv) > 1 else "76611602"
offset = int(sys.argv[2]) if len(sys.argv) > 2 else 0
url = f"https://ravionics.atlassian.net/wiki/rest/api/content/{page_id}?expand=body.storage,version"
req = urllib.request.Request(url, headers=headers)
with urllib.request.urlopen(req) as r:
    page = json.loads(r.read())

body = page["body"]["storage"]["value"]
print("Title:", page["title"])
print("Version:", page["version"]["number"])
print("Total length:", len(body))
print(f"--- BODY [{offset}:{offset+2000}] ---")
print(body[offset:offset+2000])
