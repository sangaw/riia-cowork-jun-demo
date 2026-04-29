import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from confluence.publish import ConfluenceClient

client = ConfluenceClient()
result, status = client._request("DELETE", "/content/74612756")
print(f"Delete stub page: HTTP {status}")
