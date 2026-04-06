import requests
import json

with open('session.json', 'r') as f:
    token = json.load(f)['id_token']

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json",
    "x-site-id": "7888" # internalId from __NUXT__
}

query = """
    query {
        # guess some standard queries
        viewer { id name }
        site(id: "c2l0ZSM3ODg4") { name }
        galleries { id title }
    }
"""

r = requests.post("https://api.thefam.jp/graphql", json={"query": query}, headers=headers)
print(r.status_code)
print(r.text[:500])
