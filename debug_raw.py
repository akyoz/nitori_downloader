import json
import requests

def debug_raw_data():
    with open('session.json', 'r') as f:
        token = json.load(f)['id_token']
    
    url = "https://s-nitori.com/gallery/pictures?page=1"
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"URL: {url}")
    response = requests.get(url, headers=headers)
    
    print(f"Status: {response.status_code}")
    print("\n--- 生レスポンスの先頭500文字をチェック！ ---")
    print(response.text[:500])
    
    if "window.__NUXT__" in response.text:
        print("\n--- Nuxtデータ部分を発見！ ---")
        start = response.text.find("window.__NUXT__")
        print(response.text[start:start+500])
    else:
        print("\nNuxtデータが見当たらないよ...マジで何が起きてるの！？😭")

debug_raw_data()
