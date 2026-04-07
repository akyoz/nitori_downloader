import json
import os

def analyze_har(har_file):
    print(f"HARファイルを解析中...🔍: {har_file}")
    with open(har_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    entries = data['log']['entries']
    print(f"見つかった通信数: {len(entries)} 件")
    
    gql_requests = []
    
    for entry in entries:
        req = entry['request']
        res = entry['response']
        url = req['url']
        
        # GraphQLの通信（特に入覧・取得系）を探すよ
        if 'graphql' in url.lower() or 'api' in url.lower():
            post_data = req.get('postData', {}).get('text', '')
            if post_data:
                try:
                    query_json = json.load(f'"{post_data}"') # 文字列のままなことが多いから一旦
                except:
                    pass
                
                # 'Gallery' とか 'Picture' とかが入ってるクエリを重点的に探す
                if 'gallery' in post_data.lower() or 'picture' in post_data.lower():
                    gql_requests.append({
                        'url': url,
                        'method': req['method'],
                        'headers': req['headers'],
                        'postData': post_data,
                        'status': res['status']
                    })

    print(f"\n--- アルバム関連っぽい通信: {len(gql_requests)} 件見つけたよ！ ---")
    
    # 最初の1件を詳細に保存してチェックするね
    if gql_requests:
        with open('gql_analysis.json', 'w', encoding='utf-8') as f:
            json.dump(gql_requests[0], f, indent=4, ensure_ascii=False)
        print("最初の1件の通信内容を gql_analysis.json に保存したよ！✨")
    else:
        print("うぅ、GraphQLっぽいのが見当たらない...画像URLそのものを探してみるね。")
        # 直接画像URLが含まれてる通信を探す
        for entry in entries:
            res_content = entry['response'].get('content', {}).get('text', '')
            if 'gallery' in res_content and 'picture' in res_content:
                print(f"怪しいレスポンスを発見: {entry['request']['url'][:100]}")
                break

analyze_har('s-nitori.com.har')
