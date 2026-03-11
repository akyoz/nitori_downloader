import os
import requests
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import json
import re
import time
from urllib.parse import urljoin

def login():
    """Logs in to the service using credentials from .env file and returns an ID token."""
    load_dotenv()
    email = os.getenv("NITORI_USERNAME")
    password = os.getenv("NITORI_PASSWORD")

    if not email or not password:
        print("ご主人様、.envファイルが見つからないか、設定が不完全です。\n(.env.sampleをコピーして.envファイルを作成・編集することもできます)")
        choice = input("今すぐ初期設定を行いますか？ (y/n): ").lower()
        if choice == 'y':
            email = input("NITORIのメールアドレスを入力してください: ")
            password = input("NITORIのパスワードを入力してください: ")
            download_dir = input("ダウンロード先のフォルダパスを入力してください (デフォルトは 'downloads'): ")
            if not download_dir:
                download_dir = "downloads"

            with open('.env', 'w', encoding='utf-8') as f:
                f.write(f'NITORI_USERNAME="{email}"\n')
                f.write(f'NITORI_PASSWORD="{password}"\n')
                f.write(f'DOWNLOAD_DIR="{download_dir}"\n')

            print(".envファイルを作成し、設定を保存しました。ログインを続けます。")
            # .envファイルが作成されたので、再度読み込む
            load_dotenv()
        else:
            print("設定がキャンセルされました。またね、ご主人様！")
            return None

    api_key = "AIzaSyDcipyBAbP8FkkMGKYFT80CmlIVzuJTINU"
    auth_endpoint = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}"

    payload = {
        "email": email, "password": password, "returnSecureToken": True,
        "clientType": "CLIENT_TYPE_WEB",
        "recaptchaEnforcementState": [{"provider": "EMAIL_PASSWORD_PROVIDER", "enforcementState": "AUDIT"}]
    }

    try:
        response = requests.post(auth_endpoint, json=payload, headers={'Content-Type': 'application/json'})
        response.raise_for_status()
        data = response.json()
        if 'idToken' in data:
            print("ログイン成功！ さすがご主人様！")
            return data['idToken']
        else:
            print(f"ログイン失敗。レスポンスがおかしいみたい。\n{data}")
            return None
    except requests.exceptions.HTTPError as e:
        print(f"ログイン失敗したみたい… status: {e.response.status_code}")
        try:
            print(f"エラー内容: {e.response.json().get('error', {}).get('message', '不明なエラー')}")
        except json.JSONDecodeError:
            print(f"エラー内容: {e.response.text}")
    except requests.exceptions.RequestException as e:
        print(f"うぅ、リクエスト中にエラーが…: {e}")
    return None

def get_authed_soup(url, id_token):
    """Fetches a page with authorization and returns a BeautifulSoup object."""
    headers = {"Authorization": f"Bearer {id_token}"}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return BeautifulSoup(response.text, 'lxml')
    except requests.exceptions.RequestException as e:
        print(f"ページの取得に失敗しちゃった: {url}, エラー: {e}")
        return None

def get_all_album_urls(id_token):
    """Iterates through gallery pages to find all album URLs."""
    print("アルバムURLの収集を開始しますっ！")
    base_url = "https://s-nitori.com/"
    gallery_url_template = "https://s-nitori.com/gallery/pictures?page={}"
    album_urls = set()
    page = 1
    while True:
        print(f"{page}ページ目をチェック中...")
        soup = get_authed_soup(gallery_url_template.format(page), id_token)
        if not soup:
            break

        # アルバムへのリンクは '/gallery/pictures/ランダムな文字列' の形式
        links = soup.find_all('a', href=re.compile(r'^/gallery/pictures/[a-zA-Z0-9]{20}$'))
        
        if not links:
            print(f"{page}ページにはアルバムが見つかりませんでした。収集を終わります。")
            break

        found_new = False
        for link in links:
            full_url = urljoin(base_url, link['href'])
            if full_url not in album_urls:
                album_urls.add(full_url)
                found_new = True
        
        print(f"見つけたアルバム数: {len(links)}")
        page += 1
        time.sleep(1) # サーバーに優しくするために少し待つ

    print(f"合計 {len(album_urls)} 件のユニークなアルバムを見つけました！")
    return sorted(list(album_urls))

def get_album_data(album_url, id_token):
    """Extracts image URLs and album name from a single album page."""
    print(f"アルバムページを解析中: {album_url}")
    soup = get_authed_soup(album_url, id_token)
    if not soup:
        return None, None

    # URLの末尾をアルバム名（フォルダ名）として使う
    album_name = album_url.strip('/').split('/')[-1]

    script_tag = soup.find('script', string=re.compile(r'window\.__NUXT__'))
    if not script_tag:
        print("Nuxt.jsのデータスクリプトが見つかりませんでした。")
        return album_name, []

    script_content = script_tag.string.replace('\\u002F', '/')
    urls = re.findall(r'"(https://fam-fansite\.imgix\.net/shared_file/.*?)"', script_content)
    
    image_urls = sorted(list(set(url for url in urls if url.split('?')[0].endswith(('.png', '.jpg', '.jpeg', '.gif')))))
    
    print(f"アルバム '{album_name}' で {len(image_urls)} 枚のユニークな画像URLを見つけました。")
    return album_name, image_urls

def download_album_images(album_name, image_urls, base_save_path):
    """Downloads images for a specific album into its own folder."""
    album_dir = os.path.join(base_save_path, album_name)
    if not os.path.exists(album_dir):
        os.makedirs(album_dir)
        print(f"作成したフォルダ: {album_dir}")

    for url in image_urls:
        try:
            image_name = url.split('?')[0].split('/')[-1]
            file_path = os.path.join(album_dir, image_name)

            if os.path.exists(file_path):
                print(f"スキップ: {image_name} はもう存在します。")
                continue

            print(f"ダウンロード中: {image_name}...")
            response = requests.get(url, stream=True)
            response.raise_for_status()
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(8192):
                    f.write(chunk)
        except requests.exceptions.RequestException as e:
            print(f"ダウンロードエラー: {url}, エラー: {e}")
        time.sleep(0.5) # サーバーに優しく

if __name__ == '__main__':
    id_token = login()
    if id_token:
        load_dotenv()
        save_path = os.getenv("DOWNLOAD_DIR", "downloads")
        
        # 絶対パスに変換して表示
        abs_save_path = os.path.abspath(save_path)
        print(f"画像は '{abs_save_path}' に保存されます。")
        print("変更したい場合は、.envファイルで 'DOWNLOAD_DIR' を設定してくださいね。")

        if not os.path.exists(abs_save_path):
            os.makedirs(abs_save_path)

        album_urls = get_all_album_urls(id_token)

        if not album_urls:
            print("ダウンロード対象のアルバムが見つかりませんでした。しょぼん。")
        else:
            total_albums = len(album_urls)
            for i, album_url in enumerate(album_urls):
                print(f"\n--- アルバム {i+1}/{total_albums} の処理を開始 ---")
                album_name, image_urls = get_album_data(album_url, id_token)
                if album_name and image_urls:
                    download_album_images(album_name, image_urls, save_path)
                else:
                    print(f"アルバム {album_url} から画像を取得できませんでした。")
            
            print("\n----------------------------")
            print("すべてのダウンロード処理が完了しました！ お疲れ様でした、ご主人様！")
