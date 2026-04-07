import json
import requests
import re

def inspect_gallery_nuxt():
    with open('session.json', 'r') as f:
        token = json.load(f)['id_token']
    
    url = "https://s-nitori.com/gallery/pictures?page=1"
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"URLにアクセスしてデータを引っこ抜くよ: {url}")
    response = requests.get(url, headers=headers)
    
    # 生のレスポンスをファイルに保存して、私が直接読むね！
    with open('raw_response.html', 'w', encoding='utf-8') as f:
        f.write(response.text)
    
    # Nuxtデータの中身を正規表現で探すよ
    # アルバムIDは 22文字前後の英数字であることが多いから、それをキーワードにするね
    # s-nitori.com/gallery/pictures/... という文字列がデータの中にないかチェック！
    
    matches = re.findall(r'/gallery/pictures/[a-zA-Z0-9_-]{15,35}', response.text)
    
    print(f"\nデータの中に隠れてたリンク候補: {len(matches)} 件")
    with open('found_hidden_links.txt', 'w', encoding='utf-8') as f:
        for m in sorted(list(set(matches))):
            f.write(f"{m}\n")
            print(f"見つけた！: {m}")

inspect_gallery_nuxt()
