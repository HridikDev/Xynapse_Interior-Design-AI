import os
import requests
from dotenv import load_dotenv

load_dotenv()
SERPAPI_KEY = os.getenv("SERPAPI_KEY")

def fetch_products(prompt):
    url = "https://serpapi.com/search.json"
    params = {
        "q": prompt + " interior furniture",
        "engine": "google_shopping",
        "api_key": SERPAPI_KEY
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        results = []
        for item in data.get("shopping_results", [])[:5]:
            results.append({
                "name": item.get("title", "Unknown Item"),
                "url": item.get("link", "#")
            })
        return results

    except Exception as e:
        return [{"name": "Error fetching products", "url": "#"}]
