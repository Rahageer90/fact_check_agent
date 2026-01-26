import os
from dotenv import load_dotenv
from newsapi import NewsApiClient

load_dotenv()

NEWS_API_KEY = os.getenv("NEWSAPI_API_KEY")

if not NEWS_API_KEY:
    raise ValueError("NEWSAPI_API_KEY environment variable is not set")

# Initialize NewsAPI client
newsapi_client = NewsApiClient(api_key=NEWS_API_KEY)


def news_search(query: str) -> list:
    """Retrieve news-based evidence using NewsAPI"""
    try:
        # Use NewsAPI client's get_everything method for comprehensive search
        all_articles = newsapi_client.get_everything(
            q=query,
            language="en",
            page_size=10,  # Increased for better coverage
            sort_by="relevancy"
        )

        results = []
        if all_articles and all_articles.get("articles"):
            for article in all_articles.get("articles", []):
                result = {
                    "title": article.get("title", ""),
                    "url": article.get("url", ""),
                    "type": "news",
                    "source": article.get("source", {}).get("name", ""),
                    "published_at": article.get("publishedAt", ""),
                    "description": article.get("description", "")
                }
                results.append(result)

        return results if results else [{"title": "No results found", "url": "", "type": "news"}]
    except Exception as e:
        error_msg = f"News Search Error: {str(e)}"
        print(f"❌ {error_msg}")
        return [{"title": error_msg, "url": "", "type": "news", "error": True}]
