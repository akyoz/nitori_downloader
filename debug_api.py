import json
import requests
import re

def debug_api():
    with open('session.json', 'r') as f:
        token = json.load(f)['id_token']
        
    api_url = "https://api.thefam.jp/graphql"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "accept": "*/*",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36"
    }

    payload = {
        "operationName": "galleriesV2",
        "variables": {
            "paginationOptions": {"type": "OFFSET", "offsetOptions": {"offset": 0, "limit": 1}},
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
      }
    }
  }
}"""
    }

    print("APIを叩いてみるよ...🚀")
    response = requests.post(api_url, json=payload, headers=headers)
    print(f"Status: {response.status_code}")
    print("\n--- APIからの生レスポンス ---")
    print(response.text)
    
    with open('api_response_debug.json', 'w', encoding='utf-8') as f:
        f.write(response.text)

debug_api()
