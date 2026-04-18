import os
import json
import requests
import re
import time
import yt_dlp
import logging
from datetime import datetime
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

# 環境変数の読み込み
load_dotenv()

# パス設定
SESSION_FILE = 'session.json'
DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR", "downloads")
COOKIE_FILE = 'cookies.txt'
LOG_FILE = 'downloader.log'

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def save_session(page, cookies, headers):
    try:
        access_token = page.evaluate("() => localStorage.getItem('accessToken')")
    except:
        access_token = None
    session_data = {"cookies": cookies, "headers": headers, "access_token": access_token}
    with open(SESSION_FILE, 'w', encoding='utf-8') as f:
        json.dump(session_data, f, indent=2, ensure_ascii=False)
    logger.info("セッションを保存しました。")
    
    try:
        with open(COOKIE_FILE, "w", encoding="utf-8") as f:
            f.write("# Netscape HTTP Cookie File\n\n")
            for cookie in cookies:
                domain = cookie.get('domain', 's-nitori.com')
                if not domain.startswith('.'): domain = f".{domain}"
                s = "TRUE" if cookie.get('secure', False) else "FALSE"
                e = int(cookie.get('expires', -1))
                if e == -1: e = 2147483647
                f.write(f"{domain}\tTRUE\t{cookie.get('path', '/')}\t{s}\t{e}\t{cookie['name']}\t{cookie['value']}\n")
    except Exception as e:
        logger.error(f"クッキー保存エラー: {e}")

def load_session():
    if os.path.exists(SESSION_FILE):
        try:
            with open(SESSION_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except: pass
    return None

def ensure_logged_in():
    session = load_session()
    if session and session.get('access_token'):
        return session
    logger.info("ログインが必要です。")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        auth_header = None
        def handle_request(request):
            nonlocal auth_header
            if "api.thefam.jp/graphql" in request.url:
                h = request.headers
                if "authorization" in h: auth_header = h["authorization"]
        page.on("request", handle_request)
        page.goto("https://s-nitori.com/login")
        logger.info("ログイン完了をお待ちしています...")
        start_time = time.time()
        while time.time() - start_time < 300:
            try:
                token = page.evaluate("() => localStorage.getItem('accessToken')")
                if auth_header and token:
                    logger.info("ログイン成功を確認。")
                    page.wait_for_timeout(2000)
                    break
            except: pass
            page.wait_for_timeout(1000)
        if not auth_header: return None
        save_session(page, context.cookies(), {"authorization": auth_header})
        browser.close()
        return load_session()

def get_browser_headers():
    session = load_session()
    h = {"accept": "*/*", "content-type": "application/json", "origin": "https://s-nitori.com", "referer": "https://s-nitori.com/", "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/146.0.0.0"}
    if session and "headers" in session: h.update(session["headers"])
    return h

def fetch_all_albums_via_api():
    logger.info("アルバム取得中...")
    api_url = "https://api.thefam.jp/graphql"
    headers = get_browser_headers()
    all_albums = []
    offset = 0
    while True:
        payload = {"operationName": "galleriesV2", "variables": {"paginationOptions": {"type": "OFFSET", "offsetOptions": {"offset": offset, "limit": 12}}, "filterOptions": {"galleryGroupSlug": "pictures"}, "sortKey": "PUBLICATION_START_AT"}, "query": "query galleriesV2($paginationOptions: PaginationOptionsInput!, $filterOptions: GalleryFilterOptionsInput, $sortKey: GallerySortKey) { galleriesV2(paginationOptions: $paginationOptions, filterOptions: $filterOptions, sortKey: $sortKey) { pageInfo { hasNextPage } edges { node { id name contents { contentFile { url } } } } } }"}
        try:
            res = requests.post(api_url, json=payload, headers=headers)
            data = res.json()
            nodes = data.get('data', {}).get('galleriesV2', {}).get('edges', [])
            if not nodes: break
            for edge in nodes:
                node = edge['node']
                all_albums.append({"id": node['id'], "title": re.sub(r'[\\/:*?"<>|]', '_', node['name']), "image_urls": [c['contentFile']['url'] for c in node.get('contents', []) if c.get('contentFile')]})
            if not data.get('data', {}).get('galleriesV2', {}).get('pageInfo', {}).get('hasNextPage', False): break
            offset += 12
        except: break
    return all_albums

def fetch_all_movies_via_api():
    logger.info("動画取得中...")
    api_url = "https://api.thefam.jp/graphql"
    headers = get_browser_headers()
    all_movies = []
    offset = 0
    while True:
        payload = {"operationName": "moviesV2", "variables": {"paginationOptions": {"type": "OFFSET", "offsetOptions": {"offset": offset, "limit": 12}}, "filterOptions": {"categoryId": ""}, "sortKey": "PUBLICATION_START_AT"}, "query": "query moviesV2($paginationOptions: PaginationOptionsInput!, $filterOptions: MovieFilterOptionsInput, $sortKey: MovieSortKey) { moviesV2(paginationOptions: $paginationOptions, filterOptions: $filterOptions, sortKey: $sortKey) { pageInfo { hasNextPage } edges { node { id name } } } }"}
        try:
            res = requests.post(api_url, json=payload, headers=headers)
            data = res.json()
            nodes = data.get('data', {}).get('moviesV2', {}).get('edges', [])
            if not nodes: break
            for edge in nodes:
                node = edge['node']
                all_movies.append({"id": node['id'], "title": re.sub(r'[\\/:*?"<>|]', '_', node['name'])})
            if not data.get('data', {}).get('moviesV2', {}).get('pageInfo', {}).get('hasNextPage', False): break
            offset += 12
        except: break
    return all_movies

def download_images(album, base_path):
    album_dir = os.path.join(base_path, f"{album['id']} - {album['title']}")
    if not os.path.exists(album_dir): os.makedirs(album_dir)
    for i, url in enumerate(album['image_urls']):
        try:
            filename = f"{i+1:03d}{'.png' if '.png' in url.lower() else '.jpg'}"
            file_path = os.path.join(album_dir, filename)
            if os.path.exists(file_path): continue
            res = requests.get(url, stream=True, timeout=15)
            with open(file_path, 'wb') as f:
                for chunk in res.iter_content(8192): f.write(chunk)
            time.sleep(0.1)
        except: pass

def get_video_url_via_browser(browser_context, movie_id, access_token, retry=0):
    page = browser_context.new_page()
    video_url_info = {"url": None, "headers": {}}
    
    def handle_request(request):
        url = request.url
        if (".m3u8" in url or ".mp4" in url) and not video_url_info["url"]:
            if any(k in url for k in ["master", "index", "m3u8"]):
                video_url_info["url"] = url
                video_url_info["headers"] = request.headers
                logger.info(f"URLキャプチャ: {url[:60]}...")

    page.on("request", handle_request)
    
    try:
        url = f"https://s-nitori.com/movie/{movie_id}"
        logger.info(f"解析試行 {retry+1}: {movie_id}")
        
        # トークン注入用
        page.add_init_script(f"() => {{ localStorage.setItem('accessToken', '{access_token}'); }}")
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        page.evaluate(f"() => {{ localStorage.setItem('accessToken', '{access_token}'); }}")
        
        # プレイヤー要素が出るまで待機
        page.wait_for_timeout(3000)
        
        # プレイヤー候補を探す
        player_selectors = ["video", ".vjs-big-play-button", ".vjs-tech", ".video-js", "canvas"]
        found_selector = None
        for sel in player_selectors:
            if page.is_visible(sel):
                found_selector = sel
                break
        
        if found_selector:
            logger.info(f"プレイヤー発見: {found_selector}")
            # 要素までスクロールして中央へ
            el = page.query_selector(found_selector)
            el.scroll_into_view_if_needed()
            page.wait_for_timeout(1000)
            
            # 要素の中心を確実にクリック
            box = el.bounding_box()
            if box:
                center_x = box['x'] + box['width'] / 2
                center_y = box['y'] + box['height'] / 2
                logger.info(f"座標クリック実行: ({center_x}, {center_y})")
                page.mouse.click(center_x, center_y)
            else:
                el.click()
        
        # JSでの強制再生試行
        page.evaluate("() => { const v = document.querySelector('video'); if(v) { v.muted = true; v.play(); } }")
        
        # URLキャプチャ待ち
        for _ in range(30):
            if video_url_info["url"]: break
            page.wait_for_timeout(500)
            
    except Exception as e:
        logger.warning(f"解析エラー: {e}")
    finally:
        page.close()

    if not video_url_info["url"] and retry < 1:
        logger.info("再試行します...")
        return get_video_url_via_browser(browser_context, movie_id, access_token, retry+1)
        
    return video_url_info

def download_video_with_ytdlp(movie, base_path, cookie_file, browser_context, access_token):
    save_dir = os.path.join(base_path, "movies")
    if not os.path.exists(save_dir): os.makedirs(save_dir)
    
    base_name = f"{movie['id']}_{movie['title']}"
    if any(f.startswith(base_name) for f in os.listdir(save_dir)):
        logger.info(f"スキップ: {movie['title']}")
        return

    logger.info(f"--- 処理: {movie['title']} ---")
    v_info = get_video_url_via_browser(browser_context, movie['id'], access_token)
    if not v_info["url"]:
        logger.error(f"URL取得失敗: {movie['title']}")
        return

    ydl_opts = {
        'format': 'best',
        'outtmpl': os.path.join(save_dir, f"{movie['id']}_{movie['title']}.%(ext)s"),
        'cookiefile': cookie_file,
        'http_headers': {
            'User-Agent': v_info["headers"].get('user-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/146.0.0.0'),
            'Referer': f"https://s-nitori.com/movie/{movie['id']}",
            'Origin': 'https://s-nitori.com',
        },
        'nocheckcertificate': True,
        'hls_prefer_native': True,
        'quiet': True
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            ydl.download([v_info["url"]])
            logger.info(f"成功: {movie['title']}")
        except Exception as e:
            logger.error(f"yt-dlpエラー: {e}")

if __name__ == '__main__':
    if not os.path.exists(DOWNLOAD_DIR): os.makedirs(DOWNLOAD_DIR)
    session = ensure_logged_in()
    if not session: exit(1)
    
    all_albums = fetch_all_albums_via_api()
    for album in all_albums: download_images(album, DOWNLOAD_DIR)

    all_movies = fetch_all_movies_via_api()
    if all_movies:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            if session.get('cookies'): context.add_cookies(session['cookies'])
            token = session.get('access_token')
            for movie in all_movies:
                download_video_with_ytdlp(movie, DOWNLOAD_DIR, COOKIE_FILE, context, token)
                time.sleep(2)
            browser.close()
