"""Utility: look up a page ID by title."""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from confluence.publish import ConfluenceClient, SPACE_KEY

client = ConfluenceClient()
title = sys.argv[1] if len(sys.argv) > 1 else "RITA Production Refactor -- Master Plan"
result, status = client._request(
    "GET", f"/content?spaceKey={SPACE_KEY}&title={title.replace(' ', '+')}&expand=version"
)
for p in result.get("results", []):
    print(f"ID: {p['id']}  Title: {p['title']}  Version: {p['version']['number']}")
if not result.get("results"):
    print("No results found")
    print(json.dumps(result, indent=2))
