import os
import requests
from dotenv import load_dotenv

load_dotenv()

SERPAPI_URL = "https://serpapi.com/search.json"
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")


def web_search(query: str) -> list:
    """Retrieve general web evidence using SerpAPI"""
    if not SERPAPI_API_KEY:
        return [{"title": "API Key Missing", "url": "", "type": "web"}]
    
    params = {
        "q": query,
        "api_key": SERPAPI_API_KEY,
        "num": 5
    }

    try:
        response = requests.get(SERPAPI_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        results = []
        for item in data.get("organic_results", []):
            results.append({
                "title": item.get("title"),
                "url": item.get("link"),
                "type": "web"
            })

        return results
    except Exception as e:
        return [{"title": f"Web Search Error: {str(e)}", "url": "", "type": "web"}]
