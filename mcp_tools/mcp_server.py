import os
import httpx
from dotenv import load_dotenv
from fastmcp import FastMCP

# 1. Load Environment Variables
load_dotenv()

# 2. Variable Mapping (FIXED: Correct mapping from .env)
SERPER_API_KEY = os.getenv("SERPAPI_API_KEY")  # Maps to SERPAPI_API_KEY in .env
NEWS_API_KEY = os.getenv("NEWSAPI_API_KEY")    # Maps to NEWSAPI_API_KEY in .env

# 3. Initialize FastMCP Instance
mcp = FastMCP("fact-check-mcp-server")

@mcp.tool()
async def web_search(query: str) -> str:
    """Search the web using Google Serper for factual information."""
    if not SERPER_API_KEY:
        return "Error: SERPAPI_API_KEY missing in .env"

    url = "https://google.serper.dev/search"
    headers = {"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"}
    payload = {"q": query, "num": 5}

    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(url, json=payload, headers=headers, timeout=20)
            r.raise_for_status()
            data = r.json()

        results = [
            f"- {item.get('title', 'No Title')} ({item.get('link', '')})"
            for item in data.get("organic", [])
        ]
        return "\n".join(results) if results else "No results found."
    except Exception as e:
        return f"Web search failed: {str(e)}"

@mcp.tool()
async def news_search(query: str) -> str:
    """Search news articles using NewsAPI for recent and authoritative sources."""
    if not NEWS_API_KEY:
        return "Error: NEWSAPI_API_KEY missing in .env"

    url = "https://newsapi.org/v2/everything"
    params = {
        "q": query,
        "apiKey": NEWS_API_KEY,
        "language": "en",
        "pageSize": 5,
        "sortBy": "relevancy",
    }

    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(url, params=params, timeout=20)
            r.raise_for_status()
            data = r.json()

        results = [
            f"- {a.get('title', 'No Title')} ({a.get('url', '')})"
            for a in data.get("articles", [])
        ]
        return "\n".join(results) if results else "No news found."
    except Exception as e:
        return f"News search failed: {str(e)}"