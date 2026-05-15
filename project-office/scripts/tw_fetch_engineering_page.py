"""Fetch current Engineering Confluence page for TechWriter review."""
import sys, importlib.util
spec = importlib.util.spec_from_file_location(
    "publish",
    "C:/Users/Sandeep/Documents/Work/code/riia-cowork-jun/project-office/confluence/publish.py"
)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
ConfluenceClient = mod.ConfluenceClient
SECTION = mod.SECTION

client = ConfluenceClient()
page = client.get_page(SECTION["engineering_current"], expand="version,body.storage")
print("Title:", page["title"])
print("Version:", page["version"]["number"])
body = page["body"]["storage"]["value"]
print("Body length:", len(body))
print("---BODY---")
print(body)
