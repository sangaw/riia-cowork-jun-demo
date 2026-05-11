"""Fetch Engineering page from Confluence and print body."""
import sys
sys.path.insert(0, '.')
from project_office.confluence.publish import ConfluenceClient

client = ConfluenceClient()
page = client.get_page('76611602', expand='version,body.storage')
print('TITLE:', page['title'])
print('VERSION:', page['version']['number'])
print('BODY_LEN:', len(page['body']['storage']['value']))
print('---BODY---')
print(page['body']['storage']['value'])
