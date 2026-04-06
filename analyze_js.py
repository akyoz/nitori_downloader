import requests
import re

url1 = "https://s-nitori.com/_nuxt/3fe9d7f.js"
url2 = "https://s-nitori.com/_nuxt/1acd16d.js"
url3 = "https://s-nitori.com/_nuxt/5811090.js" # This might be the gallery chunk

for url in [url1, url2, url3]:
    try:
        r = requests.get(url)
        content = r.text
        print(f"--- {url} ---")
        # looking for API calls
        endpoints = re.findall(r'["\'](https?://api\.[a-z0-9\-_\.]+|/api/[a-zA-Z0-9\-_\./]+|graphql)["\']', content)
        if endpoints:
            print("Found endpoints:", set(endpoints))
        
        # looking for anything related to API or pictures
        if 'gallery' in content:
            print("Contains 'gallery'")
    except Exception as e:
        print("Error:", e)
