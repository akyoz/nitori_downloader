import sys
import json
import re
import requests
from bs4 import BeautifulSoup

def get_page(url, id_token):
    headers = {"Authorization": f"Bearer {id_token}"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'lxml')
    script_tag = soup.find('script', string=re.compile(r'window\.__NUXT__'))
    if not script_tag:
        print("No __NUXT__ found")
        return
        
    script_content = script_tag.string
    print(script_content[:200]) # just to see the start
    
    titles = re.findall(r'title\s*:\s*"(.*?)"', script_content)
    names = re.findall(r'name\s*?:\s*?([a-zA-Z0-9_]+|"[^"]+")', script_content)
    print("Found titles:", titles)
    print("Found names:", names[:20])
    
    # Let's save the script content to see what it is
    with open("temp_nuxt.js", "w", encoding="utf-8") as f:
        f.write(script_content)

with open(r'session.json', 'r') as f:
    token = json.load(f)['id_token']

print("--- Gallery Page ---")
get_page("https://s-nitori.com/gallery/pictures?page=1", token)

print("--- Album Page ---")
get_page("https://s-nitori.com/gallery/pictures/edt97dYHxntHzfdmrxUKUm", token)
