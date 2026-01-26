import os
import requests
from dotenv import load_dotenv

load_dotenv()

NEWSAPI_URL = "https://newsapi.org/v2/everything"
NEWS_API_KEY = os.getenv("NEWSAPI_API_KEY")


def news_search(query: str) -> list:
    """Retrieve news-based evidence using NewsAPI"""
    if not NEWS_API_KEY:
        return [{"title": "API Key Missing", "url": "", "type": "news"}]
    
    params = {
        "q": query,
        "apiKey": NEWS_API_KEY,
        "language": "en",
        "pageSize": 5,
        "sortBy": "relevancy"
    }

    try:
        response = requests.get(NEWSAPI_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        results = []
        for article in data.get("articles", []):
            results.append({
                "title": article.get("title"),
                "url": article.get("url"),
                "type": "news"
            })

        return results
    except Exception as e:
        return [{"title": f"News Search Error: {str(e)}", "url": "", "type": "news"}]
