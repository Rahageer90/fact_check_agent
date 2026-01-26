import os
import json
import http.client
import requests
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
from newsapi import NewsApiClient

load_dotenv()

SERPER_API_KEY = os.getenv("SERPAPI_API_KEY")
NEWS_API_KEY = os.getenv("NEWSAPI_API_KEY")
NEWSAPI_URL = "https://newsapi.org/v2/everything"

# Initialize NewsAPI client if key is available
newsapi_client = None
if NEWS_API_KEY:
    try:
        newsapi_client = NewsApiClient(api_key=NEWS_API_KEY)
    except Exception as e:
        print(f"Warning: Failed to initialize NewsAPI client: {e}")

# Create FastAPI app for MCP server
app = FastAPI(
    title="Unified Search MCP Server",
    description="MCP Server providing web_search and news_search tools"
)

class ToolRequest(BaseModel):
    query: str


def web_search_impl(query: str) -> list:
    """Implementation of web search using Google Serper API"""
    if not SERPER_API_KEY:
        return [{"title": "API Key Missing", "url": "", "type": "web"}]

    try:
        conn = http.client.HTTPSConnection("google.serper.dev")

        payload = json.dumps({
            "q": query,
            "num": 5
        })

        headers = {
            'X-API-KEY': SERPER_API_KEY,
            'Content-Type': 'application/json'
        }

        conn.request("POST", "/search", payload, headers)
        res = conn.getresponse()
        data = json.loads(res.read().decode("utf-8"))

        results = []
        for item in data.get("organic", []):
            results.append({
                "title": item.get("title", ""),
                "url": item.get("link", ""),
                "type": "web"
            })

        conn.close()

        return results if results else [{"title": "No results found", "url": "", "type": "web"}]

    except Exception as e:
        return [{"title": f"Web Search Error: {str(e)}", "url": "", "type": "web"}]


def news_search_impl(query: str) -> list:
    """Implementation of news search using NewsAPI"""
    if not NEWS_API_KEY or not newsapi_client:
        return [{"title": "API Key Missing", "url": "", "type": "news"}]

    try:
        # Use NewsAPI client's get_everything method for better results
        all_articles = newsapi_client.get_everything(
            q=query,
            language="en",
            page_size=5,
            sort_by="relevancy"
        )

        results = []
        if all_articles and all_articles.get("articles"):
            for article in all_articles.get("articles", []):
                results.append({
                    "title": article.get("title", ""),
                    "url": article.get("url", ""),
                    "type": "news",
                    "source": article.get("source", {}).get("name", ""),
                    "published_at": article.get("publishedAt", "")
                })

        return results if results else [{"title": "No results found", "url": "", "type": "news"}]
    except Exception as e:
        return [{"title": f"News Search Error: {str(e)}", "url": "", "type": "news"}]


@app.post("/web_search")
async def web_search(request: ToolRequest):
    """Web search endpoint"""
    results = web_search_impl(request.query)
    return {"results": results}


@app.post("/news_search")
async def news_search(request: ToolRequest):
    """News search endpoint"""
    results = news_search_impl(request.query)
    return {"results": results}


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Unified Search MCP Server",
        "tools": ["web_search", "news_search"]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)
