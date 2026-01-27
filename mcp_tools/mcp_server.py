import os
import json
import httpx
from dotenv import load_dotenv

from fastmcp import FastMCP

# ---------------------------------------------------
# Environment
# ---------------------------------------------------

load_dotenv()

SERPER_API_KEY = os.getenv("SERPAPI_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

# ---------------------------------------------------
# MCP SERVER
# ---------------------------------------------------

app = FastMCP("fact-check-mcp-server")

# ---------------------------------------------------
# Tool Implementations
# ---------------------------------------------------

@app.tool()
async def web_search(query: str) -> str:
    """Search the web using Google Serper for factual information."""
    if not SERPER_API_KEY:
        return "SERPAPI_API_KEY missing"

    url = "https://google.serper.dev/search"
    headers = {"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"}
    payload = {"q": query, "num": 5}

    async with httpx.AsyncClient() as client:
        r = await client.post(url, json=payload, headers=headers, timeout=20)
        r.raise_for_status()
        data = r.json()

    results = [
        f"- {item.get('title')} ({item.get('link')})"
        for item in data.get("organic", [])
    ]
    return "\n".join(results) or "No results"


@app.tool()
async def news_search(query: str) -> str:
    """Search news articles using NewsAPI for recent and authoritative sources."""
    if not NEWS_API_KEY:
        return "NEWS_API_KEY missing"

    url = "https://newsapi.org/v2/everything"
    params = {
        "q": query,
        "apiKey": NEWS_API_KEY,
        "language": "en",
        "pageSize": 5,
    }

    async with httpx.AsyncClient() as client:
        r = await client.get(url, params=params, timeout=20)
        r.raise_for_status()
        data = r.json()

    results = [
        f"- {a['title']} ({a['url']})"
        for a in data.get("articles", [])
    ]
    return "\n".join(results) or "No news"


# ---------------------------------------------------
# Actual Tool Logic
# ---------------------------------------------------

async def web_search(query: str) -> str:
    if not SERPER_API_KEY:
        return "SERPAPI_API_KEY missing"

    url = "https://google.serper.dev/search"
    headers = {"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"}
    payload = {"q": query, "num": 5}

    async with httpx.AsyncClient() as client:
        r = await client.post(url, json=payload, headers=headers, timeout=20)
        r.raise_for_status()
        data = r.json()

    results = [
        f"- {item.get('title')} ({item.get('link')})"
        for item in data.get("organic", [])
    ]
    return "\n".join(results) or "No results"


async def news_search(query: str) -> str:
    if not NEWS_API_KEY:
        return "NEWS_API_KEY missing"

    url = "https://newsapi.org/v2/everything"
    params = {
        "q": query,
        "apiKey": NEWS_API_KEY,
        "language": "en",
        "pageSize": 5,
    }

    async with httpx.AsyncClient() as client:
        r = await client.get(url, params=params, timeout=20)
        r.raise_for_status()
        data = r.json()

    results = [
        f"- {a['title']} ({a['url']})"
        for a in data.get("articles", [])
    ]
    return "\n".join(results) or "No news"


# ---------------------------------------------------
# Run the server with SSE transport
# ---------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
