import json
import requests
import re
import os

def try_real_api():
    # HARからCookieを盗み出すよ！✨
    har_path = 's-nitori.com.har'
    headers = {
        "accept": "*/*",
        "content-type": "application/json",
        "origin": "https://s-nitori.com",
        "referer": "https://s-nitori.com/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
        "x-referer": "https://s-nitori.com"
    }

    if not os.path.exists(har_path):
        print("HARファイルがないよ！💦")
        return

    with open(har_path, 'r', encoding='utf-8') as f:
        har = json.load(f)
        
    # 'galleriesV2' の通信を探してヘッダーを丸ごとコピー
    for entry in har['log']['entries']:
        if 'galleriesV2' in entry['request'].get('postData', {}).get('text', ''):
            for h in entry['request']['headers']:
                # : で始まる特殊ヘッダー以外を全部コピー
                if not h['name'].startswith(':'):
                    headers[h['name'].lower()] = h['value']

    api_url = "https://api.thefam.jp/graphql"
    payload = {
        "operationName": "galleriesV2",
        "variables": {
            "paginationOptions": {"type": "OFFSET", "offsetOptions": {"offset": 0, "limit": 12}},
            "filterOptions": {"galleryGroupSlug": "pictures"},
            "sortKey": "PUBLICATION_START_AT"
        },
        "query": """query galleriesV2($paginationOptions: PaginationOptionsInput!, $filterOptions: GalleryFilterOptionsInput, $sortKey: GallerySortKey) {
  galleriesV2(paginationOptions: $paginationOptions, filterOptions: $filterOptions, sortKey: $sortKey) {
    pageInfo { hasNextPage }
    edges { node { id name } }
  }
}"""
    }

    print("ブラウザになりすましてAPIを叩くよ...なりすましLv.100！🚀")
    response = requests.post(api_url, json=payload, headers=headers)
    
    if response.status_code == 200 and '"data":' in response.text and '"galleriesV2":' in response.text:
        print("✨ 大勝利！！APIへの侵入に成功したよ、ご主人様！！ ✨")
        print(response.text[:500] + "...")
        with open('api_success_headers.json', 'w', encoding='utf-8') as f:
            json.dump(headers, f, indent=2)
    else:
        print(f"失敗... status: {response.status_code}")
        print(response.text)

try_real_api()
