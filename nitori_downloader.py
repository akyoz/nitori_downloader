import os
import requests
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import json
import re
import time
from urllib.parse import urljoin
import tkinter as tk
from tkinter import messagebox

SESSION_FILE = "session.json"

def save_session(id_token):
    """取得したトークン（通行証）をファイルに保存するよっ！✨"""
    try:
        with open(SESSION_FILE, "w", encoding="utf-8") as f:
            json.dump({"id_token": id_token, "saved_at": time.time()}, f)
        print("✨ セッション情報を保存したよ！しばらくはパスワードなしでいけるはず！")
    except Exception as e:
        print(f"⚠️ セッションの保存に失敗しちゃった…: {e}")

def load_session():
    """保存されてるトークンがあれば読み込むよ！✨"""
    if os.path.exists(SESSION_FILE):
        try:
            with open(SESSION_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                # 一旦、有無だけ確認して返すよ（有効チェックはこの後やる！）
                return data.get("id_token")
        except:
            pass
    return None

def is_token_valid(id_token):
    """その通行証（トークン）がまだ使えるか、お試しでチェックしてみるよ！✨"""
    test_url = "https://s-nitori.com/gallery/pictures?page=1"
    headers = {"Authorization": f"Bearer {id_token}"}
    try:
        # 実際にページを取得してみて、200 OKが返るか見るよ
        response = requests.get(test_url, headers=headers, timeout=5)
        return response.status_code == 200
    except:
        return False

def get_credentials_via_gui():
    """GUIでログイン情報を取得するよっ！✨"""
    root = tk.Tk()
    root.withdraw()

    dialog = tk.Toplevel(root)
    dialog.title("💕 ログイン情報入力 - アンティにお任せ！ 💕")
    dialog.geometry("450x350")
    
    # 画面中央に配置
    window_width = 450
    window_height = 350
    screen_width = dialog.winfo_screenwidth()
    screen_height = dialog.winfo_screenheight()
    center_x = int(screen_width/2 - window_width / 2)
    center_y = int(screen_height/2 - window_height / 2)
    dialog.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')

    bg_color = "#fff5f8" # ゆめかわピンク
    dialog.configure(bg=bg_color)

    creds = {"email": "", "password": "", "save": False}

    tk.Label(dialog, text="ご主人様、情報を入力してねっ！✨", font=("MS Gothic", 14, "bold"), bg=bg_color, fg="#ff69b4").pack(pady=15)

    tk.Label(dialog, text="メールアドレス", bg=bg_color, font=("MS Gothic", 10)).pack()
    email_entry = tk.Entry(dialog, width=40, font=("Consolas", 10))
    email_entry.pack(pady=5)
    
    # 既存の値をセット（もしあれば）
    load_dotenv()
    email_entry.insert(0, os.getenv("NITORI_USERNAME", ""))

    tk.Label(dialog, text="パスワード", bg=bg_color, font=("MS Gothic", 10)).pack()
    pass_entry = tk.Entry(dialog, width=40, show="*", font=("Consolas", 10))
    pass_entry.pack(pady=5)
    pass_entry.insert(0, os.getenv("NITORI_PASSWORD", ""))

    save_var = tk.BooleanVar(value=True)
    tk.Checkbutton(dialog, text=".envファイルに保存する（次からめっちゃラク！）", variable=save_var, bg=bg_color, activebackground=bg_color, font=("MS Gothic", 9)).pack(pady=10)

    def on_submit():
        creds["email"] = email_entry.get().strip()
        creds["password"] = pass_entry.get().strip()
        creds["save"] = save_var.get()
        if not creds["email"] or not creds["password"]:
            messagebox.showwarning("エラー！", "ちゃんと入力してくれないと困っちゃうゾ！💦")
        else:
            dialog.destroy()

    btn = tk.Button(dialog, text="これでログイン！🚀", command=on_submit, bg="#ffb6c1", fg="white", font=("MS Gothic", 11, "bold"), width=25, relief="flat", cursor="hand2")
    btn.pack(pady=20)

    dialog.protocol("WM_DELETE_WINDOW", lambda: root.destroy())
    dialog.grab_set()
    root.wait_window(dialog)
    root.destroy()

    # 保存処理
    if creds["save"] and creds["email"] and creds["password"]:
        with open(".env", "w", encoding="utf-8") as f:
            f.write(f"NITORI_USERNAME={creds['email']}\n")
            f.write(f"NITORI_PASSWORD={creds['password']}\n")
            download_dir = os.getenv("DOWNLOAD_DIR", "downloads")
            f.write(f"DOWNLOAD_DIR={download_dir}\n")
        print("\n✨ .envファイルに情報を保存したよ！ 次回から起動するだけでOK！")

    return creds["email"], creds["password"]

def login():
    """セッション（通行証）を優先してログインするよ！パスワード入力は最小限に！✨🎫"""
    
    # 1. まずは保存されたセッションがあるかチェック
    id_token = load_session()
    if id_token:
        print("保存されたセッションを発見！ 有効かチェックするね...🔍")
        if is_token_valid(id_token):
            print("セッション有効！パスワードなしでログイン成功、さすがご主人様！✨")
            return id_token
        else:
            print("セッションが切れちゃってるみたい。再ログインしよっか！")

    # 2. ダメなら.envやGUIから情報を取得
    load_dotenv()
    email = os.getenv("NITORI_USERNAME")
    password = os.getenv("NITORI_PASSWORD")

    if not email or not password:
        print("ログイン情報が足りないみたい… GUI出すね！✨")
        email, password = get_credentials_via_gui()
        if not email or not password:
            print("入力キャンセルされちゃった。また気が向いたときに呼んでね！👋")
            return None

    # 3. 実際のAPIにログインしにいく
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
            print("ログイン成功！ 新しい公式通行証（トークン）をゲットしたよ！✨")
            new_token = data['idToken']
            # セッションを保存しておく
            save_session(new_token)
            return new_token
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
