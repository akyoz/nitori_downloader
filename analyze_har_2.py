import json

def extract_second_gql(har_file):
    with open(har_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    entries = data['log']['entries']
    gql_requests = []
    
    for entry in entries:
        req = entry['request']
        if 'graphql' in req['url'].lower():
            post_data = req.get('postData', {}).get('text', '')
            if post_data:
                gql_requests.append(entry)

    # 2件目があるならそっちを詳細表示
    if len(gql_requests) >= 2:
        target = gql_requests[1]
        req = target['request']
        res = target['response']
        
        analysis = {
            'url': req['url'],
            'headers': req['headers'],
            'postData': req.get('postData', {}).get('text', ''),
            'response_text_preview': res.get('content', {}).get('text', '')[:500]
        }
        
        with open('gql_analysis_2.json', 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=4, ensure_ascii=False)
        print("2件目の通信内容を gql_analysis_2.json に保存したよ！✨🎯")
    else:
        print("うぅ、2件目が見つからなかった...。1件目をもっと詳しく見るね。")

extract_second_gql('s-nitori.com.har')
