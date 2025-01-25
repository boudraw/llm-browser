import requests
import json
from search.env import SERPER_URL, SERPER_API_KEY


def search_google(query):
    print("Searching Google for:", query)
    payload = json.dumps({
        "q": query,
        "autocorrect": False
    })
    headers = {
        'X-API-KEY': SERPER_API_KEY,
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", SERPER_URL, headers=headers, data=payload)
    return response.json()
