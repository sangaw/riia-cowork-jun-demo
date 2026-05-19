import sys
sys.path.insert(0, '.')
from project_office.confluence.publish import ConfluenceClient, SECTION

client = ConfluenceClient()
page = client.get_page(SECTION['engineering_current'], expand='version,body.storage')
print('Page title:', page['title'])
print('Version:', page['version']['number'])
print('Body length:', len(page['body']['storage']['value']))
print()
print(page['body']['storage']['value'])
