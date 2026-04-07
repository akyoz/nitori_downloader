import os
import json
import requests
import re
import time
from dotenv import load_dotenv

# .envファイルを読み込むよ
load_dotenv()

def get_browser_headers():
    """HARファイルから魔法のヘッダー（Cookieなど）を盗み出すよ！✨🎭"""
    har_path = 's-nitori.com.har'
    headers = {
        "accept": "*/*",
        "content-type": "application/json",
        "origin": "https://s-nitori.com",
        "referer": "https://s-nitori.com/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
        "x-referer": "https://s-nitori.com"
    }

    if os.path.exists(har_path):
        try:
            with open(har_path, 'r', encoding='utf-8') as f:
                har = json.load(f)
            # galleriesV2のリクエストを探してヘッダーをコピー
            for entry in har['log']['entries']:
                if 'galleriesV2' in entry['request'].get('postData', {}).get('text', ''):
                    for h in entry['request']['headers']:
                        if not h['name'].startswith(':'):
                            headers[h['name'].lower()] = h['value']
                    return headers
        except:
            print("HARの解析に失敗しちゃった...デフォルトのヘッダーを使うね！")
    else:
        print("s-nitori.com.har が見つからないよ！手動ログインが必要かも？💦")
        
    return headers

def fetch_all_albums_via_api():
    """APIを自動でページングして、全アルバム情報を根こそぎ取ってくるよ！🚀💎"""
    print("APIを自動巡回してアルバム情報を収集中...🔍")
    api_url = "https://api.thefam.jp/graphql"
    headers = get_browser_headers()
    
    all_albums = []
    offset = 0
    limit = 12
    
    while True:
        payload = {
            "operationName": "galleriesV2",
            "variables": {
                "paginationOptions": {"type": "OFFSET", "offsetOptions": {"offset": offset, "limit": limit}},
                "filterOptions": {"galleryGroupSlug": "pictures"},
                "sortKey": "PUBLICATION_START_AT"
            },
            "query": """query galleriesV2($paginationOptions: PaginationOptionsInput!, $filterOptions: GalleryFilterOptionsInput, $sortKey: GallerySortKey) {
  galleriesV2(paginationOptions: $paginationOptions, filterOptions: $filterOptions, sortKey: $sortKey) {
    pageInfo { hasNextPage }
    edges {
      node {
        id
        name
        contents {
          contentFile { url }
        }
      }
    }
  }
}"""
        }
        
        try:
            response = requests.post(api_url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            # エラーチェック
            if 'errors' in data:
                print(f"APIエラーが発生しちゃった...😭: {data['errors'][0]['message']}")
                break
                
            nodes = data.get('data', {}).get('galleriesV2', {}).get('edges', [])
            if not nodes:
                break
                
            for edge in nodes:
                node = edge['node']
                album_info = {
                    "id": node['id'],
                    "title": re.sub(r'[\\/:*?"<>|]', '_', node['name']),
                    "image_urls": [c['contentFile']['url'] for c in node.get('contents', []) if c.get('contentFile')]
                }
                all_albums.append(album_info)
            
            print(f"通算 {len(all_albums)} 件のアルバムを捕捉！🎯")
            
            has_next = data.get('data', {}).get('galleriesV2', {}).get('pageInfo', {}).get('hasNextPage', False)
            if not has_next:
                print("最後まで読み切ったよ！終了！✨")
                break
                
            offset += limit
            time.sleep(0.5) # サーバーをいたわる心
            
        except Exception as e:
            print(f"巡回中にトラブル発生！😭: {e}")
            break
            
    return all_albums

def download_images(album, base_path):
    """一アルバム分をフォルダに保存するね！📁📷"""
    folder_name = f"{album['id']} - {album['title']}"
    album_dir = os.path.join(base_path, folder_name)
    
    if not os.path.exists(album_dir):
        os.makedirs(album_dir)
        print(f"フォルダ作成: {folder_name}")

    urls = album['image_urls']
    if not urls:
        print(f"『{album['title']}』は空っぽみたい...？")
        return

    for i, url in enumerate(urls):
        try:
            ext = ".jpg"
            if ".png" in url.lower(): ext = ".png"
            elif ".gif" in url.lower(): ext = ".gif"
            
            filename = f"{i+1:03d}{ext}"
            file_path = os.path.join(album_dir, filename)

            if os.path.exists(file_path):
                continue

            print(f"  DL中: {filename}...", end='\r')
            res = requests.get(url, stream=True, timeout=15)
            res.raise_for_status()
            with open(file_path, 'wb') as f:
                for chunk in res.iter_content(8192):
                    f.write(chunk)
            time.sleep(0.3)
        except Exception as e:
            print(f"\n  失敗: {filename}, エラー: {e}")
            
    print(f"\n『{album['title']}』ダウンロード完了！✨")

if __name__ == '__main__':
    print("\n" + "💎"*20)
    print("✨ NITORI 真・全自動ダウンローダー ✨")
    print("💎"*20 + "\n")

    # 保存先の決定
    save_path = os.getenv("DOWNLOAD_DIR", "downloads")
    if not os.path.exists(save_path):
        os.makedirs(save_path)

    # 1. APIを使って全アルバム情報を一気に取得！
    albums = fetch_all_albums_via_api()
    
    if not albums:
        print("うぅ、アルバムが一件も取れなかったよ...😭 HARファイルが最新か確認してね！")
    else:
        # 2. 全画像をダウンロード！
        total = len(albums)
        for i, album in enumerate(albums):
            print(f"\n--- 任務 {i+1}/{total} 開始 ---")
            download_images(album, save_path)
        
        print("\n" + "="*40)
        print("ミッション完全コンプリート！ご主人様、お宝ざっくざくだよ！！💕💰💎✨")
        print("="*40)
