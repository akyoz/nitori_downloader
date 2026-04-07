import os
import json
import requests
import re
import time
from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv()

def get_browser_headers():
    """
    HARファイルから認証情報を含むヘッダーを抽出します。
    """
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
        except Exception as e:
            print(f"HARファイルの解析中にエラーが発生しました: {e}")
    else:
        print("s-nitori.com.har が見つかりません。")
        
    return headers

def fetch_all_albums_via_api():
    """
    GraphQL APIを巡回して全アルバム情報を取得します。
    """
    print("アルバム情報を取得しています...")
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
            
            if 'errors' in data:
                print(f"APIエラー: {data['errors'][0]['message']}")
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
            
            print(f"現在合計画 {len(all_albums)} 件のアルバムを捕捉済み。")
            
            has_next = data.get('data', {}).get('galleriesV2', {}).get('pageInfo', {}).get('hasNextPage', False)
            if not has_next:
                print("全情報の取得が完了しました。")
                break
                
            offset += limit
            time.sleep(0.5) # サーバー負荷低減のための待機
            
        except Exception as e:
            print(f"通信エラーが発生しました: {e}")
            break
            
    return all_albums

def download_images(album, base_path):
    """
    指定されたアルバムの画像をローカルに保存します。
    """
    folder_name = f"{album['id']} - {album['title']}"
    album_dir = os.path.join(base_path, folder_name)
    
    if not os.path.exists(album_dir):
        os.makedirs(album_dir)

    urls = album['image_urls']
    if not urls:
        print(f"アルバム『{album['title']}』に画像URLが含まれていません。")
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

            print(f"  ダウンロード中: {filename}...", end='\r')
            res = requests.get(url, stream=True, timeout=15)
            res.raise_for_status()
            with open(file_path, 'wb') as f:
                for chunk in res.iter_content(8192):
                    f.write(chunk)
            time.sleep(0.3)
        except Exception as e:
            print(f"\n  ダウンロード失敗: {filename}, エラー: {e}")
            
    print(f"『{album['title']}』ダウンロード完了")

if __name__ == '__main__':
    print("Nitori Gallery ダウンローダーを開始します。")

    save_path = os.getenv("DOWNLOAD_DIR", "downloads")
    if not os.path.exists(save_path):
        os.makedirs(save_path)

    all_albums = fetch_all_albums_via_api()
    
    if not all_albums:
        print("アルバム情報が取得できませんでした。HARファイルの状態を確認してください。")
    else:
        total = len(all_albums)
        for i, album in enumerate(all_albums):
            print(f"\n--- アルバム {i+1}/{total} ---")
            download_images(album, save_path)
        
        print("\n" + "="*40)
        print("すべての処理が完了しました。")
        print("="*40)
