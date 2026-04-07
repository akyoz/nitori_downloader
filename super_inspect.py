import json
import requests
import re

def super_inspect():
    with open('session.json', 'r') as f:
        token = json.load(f)['id_token']
    
    url = "https://s-nitori.com/gallery/pictures?page=1"
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"URL: {url}")
    response = requests.get(url, headers=headers)
    text = response.text
    
    print(f"Total Source Length: {len(text)} characters")
    
    # 1. '/gallery/pictures/' という文字列がどこかにないか、前後100文字も含めて探すよ
    pattern = re.compile(r'.{0,100}/gallery/pictures/.{0,100}')
    matches = pattern.findall(text)
    
    print(f"\n'/gallery/pictures/' を含む箇所の数: {len(matches)}")
    with open('inspect_result.txt', 'w', encoding='utf-8') as f:
        f.write("--- '/gallery/pictures/' matches ---\n")
        for m in matches:
            f.write(f"MATCH: {m}\n")
            
        # 2. 22文字の英数字IDっぽい塊が、何かのデータの隣にないか探す
        # ID例: m6xre5S3eCJjUzAdWQhRrG (22文字)
        id_pattern = re.compile(r'[a-zA-Z0-9_-]{22}')
        ids = id_pattern.findall(text)
        f.write(f"\n\n--- Possible 22-char IDs found: {len(ids)} ---\n")
        # 多すぎるかもしれないから、ユニークなものをいくつか
        for i in list(set(ids))[:50]:
            f.write(f"ID?: {i}\n")

    print("\n詳細な調査結果を inspect_result.txt に保存したよ！✨")

super_inspect()
