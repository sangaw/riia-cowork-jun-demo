"""Fetch current Engineering page content."""
import sys
import os
# Add parent directory so project_office package is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from project_office.confluence.publish import ConfluenceClient, SECTION

client = ConfluenceClient()
page = client.get_page(SECTION['engineering_current'], expand='version,body.storage')
print('Page title:', page['title'])
print('Current version:', page['version']['number'])
body = page['body']['storage']['value']
print('Body length:', len(body))
print('--- LAST 1000 chars ---')
print(body[-1000:])
