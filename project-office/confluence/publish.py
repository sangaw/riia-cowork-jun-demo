"""
Core Confluence publisher utility.
Used by all Technical Writer agent scripts in this project.

Usage:
    from project_office.confluence.publish import ConfluenceClient
    client = ConfluenceClient()
    page_id, url = client.create_page("Title", "<h1>HTML</h1>", parent_id="65110332")
    client.update_page(page_id, "New Title", "<h1>Updated</h1>")
    client.move_page(page_id, new_parent_id)
"""
import urllib.request, urllib.error, json, base64, os
from pathlib import Path

# ── Credentials ──────────────────────────────────────────────────────────────
def _load_token() -> str:
    # 1. Environment variable (Sprint 1+ preferred)
    if os.environ.get("CONFLUENCE_API_TOKEN"):
        return os.environ["CONFLUENCE_API_TOKEN"]
    # 2. Local key file (Sprint 0 only — move to env var in Sprint 1)
    key_file = Path(__file__).parent.parent.parent / "confluence-api-key.txt"
    if key_file.exists():
        return key_file.read_text().splitlines()[0].strip()
    raise RuntimeError(
        "Confluence API token not found. Set CONFLUENCE_API_TOKEN env var "
        "or place token in project root confluence-api-key.txt"
    )

def _load_email() -> str:
    if os.environ.get("CONFLUENCE_EMAIL"):
        return os.environ["CONFLUENCE_EMAIL"]
    key_file = Path(__file__).parent.parent.parent / "confluence-api-key.txt"
    if key_file.exists():
        lines = [l.strip() for l in key_file.read_text().splitlines() if l.strip()]
        if len(lines) >= 2:
            return lines[1]
    return ""

EMAIL     = _load_email()
BASE_URL  = os.environ.get("CONFLUENCE_BASE_URL", "https://ravionics.atlassian.net/wiki/rest/api")
SPACE_KEY = os.environ.get("CONFLUENCE_SPACE_KEY", "RIIAProjec")
HOMEPAGE_ID = "65110332"

# ── Page IDs (section parents — populated after hierarchy setup) ─────────────
SECTION = {
    "project_management": "65273887",
    "how_we_work":        "65241125",
    "architecture":       "65339419",
    "engineering":        "65404944",
    "quality_testing":    "65404959",
    "operations":         "65339434",
    "release_notes":      "65208341",
    "sprint_boards":      "65077274",
}


class ConfluenceClient:
    def __init__(self):
        token = _load_token()
        creds = base64.b64encode(f"{EMAIL}:{token}".encode()).decode()
        self.headers = {
            "Authorization": f"Basic {creds}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _request(self, method: str, path: str, body: dict = None):
        data = json.dumps(body).encode() if body else None
        req = urllib.request.Request(
            f"{BASE_URL}{path}", data=data, headers=self.headers, method=method
        )
        try:
            with urllib.request.urlopen(req) as r:
                return json.load(r), r.status
        except urllib.error.HTTPError as e:
            return json.loads(e.read().decode()), e.code

    def get_page(self, page_id: str, expand: str = "version,body.storage,ancestors"):
        result, status = self._request("GET", f"/content/{page_id}?expand={expand}")
        if status != 200:
            raise RuntimeError(f"GET page {page_id} failed: HTTP {status} — {result}")
        return result

    def create_page(self, title: str, body_html: str, parent_id: str = HOMEPAGE_ID):
        """Create a new page. Returns (page_id, url)."""
        payload = {
            "type": "page",
            "title": title,
            "space": {"key": SPACE_KEY},
            "ancestors": [{"id": parent_id}],
            "body": {"storage": {"value": body_html, "representation": "storage"}},
        }
        result, status = self._request("POST", "/content", payload)
        if status in (200, 201):
            url = f"https://ravionics.atlassian.net/wiki{result['_links']['webui']}"
            return result["id"], url
        raise RuntimeError(f"Create '{title}' failed: HTTP {status} — {result.get('message','')[:120]}")

    def update_page(self, page_id: str, title: str, body_html: str):
        """Update page content. Increments version automatically."""
        page = self.get_page(page_id, expand="version")
        new_version = page["version"]["number"] + 1
        payload = {
            "version": {"number": new_version},
            "title": title,
            "type": "page",
            "body": {"storage": {"value": body_html, "representation": "storage"}},
        }
        result, status = self._request("PUT", f"/content/{page_id}", payload)
        if status == 200:
            url = f"https://ravionics.atlassian.net/wiki{result['_links']['webui']}"
            return result["id"], url
        raise RuntimeError(f"Update page {page_id} failed: HTTP {status} — {result.get('message','')[:120]}")

    def move_page(self, page_id: str, new_parent_id: str):
        """Move page to a new parent. Preserves content."""
        page = self.get_page(page_id, expand="version,body.storage,ancestors")
        new_version = page["version"]["number"] + 1
        payload = {
            "version": {"number": new_version},
            "title": page["title"],
            "type": "page",
            "ancestors": [{"id": new_parent_id}],
            "body": {"storage": {
                "value": page["body"]["storage"]["value"],
                "representation": "storage",
            }},
        }
        result, status = self._request("PUT", f"/content/{page_id}", payload)
        if status == 200:
            url = f"https://ravionics.atlassian.net/wiki{result['_links']['webui']}"
            print(f"  MOVED [{page_id}] '{page['title']}' -> parent {new_parent_id}")
            return url
        raise RuntimeError(f"Move page {page_id} failed: HTTP {status} — {result.get('message','')[:120]}")

    def list_pages(self, limit: int = 50):
        result, status = self._request(
            "GET", f"/content?spaceKey={SPACE_KEY}&limit={limit}&expand=ancestors"
        )
        if status != 200:
            raise RuntimeError(f"List pages failed: HTTP {status}")
        return result.get("results", [])
