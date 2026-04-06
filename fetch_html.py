import json
import requests
from bs4 import BeautifulSoup

def fetch(url, token):
    headers = {"Authorization": f"Bearer {token}"}
    return requests.get(url, headers=headers).text

with open('session.json', 'r') as f:
    token = json.load(f)['id_token']

html = fetch("https://s-nitori.com/gallery/pictures?page=1", token)
with open('list.html', 'w', encoding='utf-8') as f:
    f.write(html)

html_album = fetch("https://s-nitori.com/gallery/pictures/edt97dYHxntHzfdmrxUKUm", token)
with open('album.html', 'w', encoding='utf-8') as f:
    f.write(html_album)
print("Done")
