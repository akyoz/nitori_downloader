import json

def deep_analyze_har(har_file):
    print(f"新・HAR解析開始！✨🔍: {har_file}")
    with open(har_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    entries = data['log']['entries']
    print(f"通信件数: {len(entries)}")
    
    found_targets = []
    
    for i, entry in enumerate(entries):
        req = entry['request']
        res = entry['response']
        url = req['url']
        post_data = req.get('postData', {}).get('text', '')
        
        # ターゲットになりそうなキーワード
        keywords = ['gallery', 'picture', 'content', 'items', 'list']
        
        # GraphQL かつ キーワードが含まれるものを探す
        if 'graphql' in url.lower() and any(kw in post_data.lower() for kw in keywords):
            res_text = res.get('content', {}).get('text', '')
            found_targets.append({
                'index': i,
                'op_name': 'Unknown',
                'query_preview': post_data[:100],
                'res_preview': res_text[:200]
            })
            
            # オペレーション名があれば抽出
            try:
                pd_json = json.loads(post_data)
                found_targets[-1]['op_name'] = pd_json.get('operationName', 'Unknown')
            except:
                pass

    print(f"\n--- 怪しい通信を {len(found_targets)} 件発見！ ---")
    for t in found_targets:
        print(f"[{t['index']}] OP: {t['op_name']} | Res: {t['res_preview']}...")
    
    # 全部詳細に書き出しちゃう！
    results = []
    for t in found_targets:
        entry = entries[t['index']]
        results.append({
            'url': entry['request']['url'],
            'headers': entry['request']['headers'],
            'postData': entry['request'].get('postData', {}).get('text', ''),
            'response': entry['response'].get('content', {}).get('text', '')
        })
    
    with open('deep_gql_analysis.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=4, ensure_ascii=False)
    print("\n詳細データを deep_gql_analysis.json に保存したよ！✨🎯")

deep_analyze_har('s-nitori.com.har')
