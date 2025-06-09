import requests
import os
from dotenv import load_dotenv

load_dotenv()

SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")

def fetch_products(prompt):
    API_URL = "https://serpapi.com/search"

    params = {
        "engine": "amazon",
        "amazon_domain": "amazon.in",
        "k": prompt,  # 'k' is the correct parameter for keyword search
        "api_key": SERPAPI_API_KEY
    }

    response = requests.get(API_URL, params=params)
    response.raise_for_status()
    data = response.json()

    results = data.get("organic_results", [])
    sample = results[0] if results else {}

    print("Sample product data:", sample)

    products = []
    for item in results[:5]:
        title = item.get("title", "No title")
        url = item.get("link") or item.get("url") or "#"
        products.append({"name": title, "url": url})

    return products
