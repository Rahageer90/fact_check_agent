"""
MCP Server for Fact-Check AI Agent (FastMCP Implementation)
"""
import os
import json
import logging
import asyncio
import httpx 
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# --- 1. SETUP LOGGING ---
logging.basicConfig(
    filename='mcp_server.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("fastmcp_server")

# --- 2. LOAD CONFIG ---
load_dotenv()
SERPER_API_KEY = os.getenv("SERPAPI_API_KEY")
NEWS_API_KEY = os.getenv("NEWSAPI_API_KEY")

# --- 3. INITIALIZE FAST MCP ---
mcp = FastMCP("fact-check-mcp-server")

# --- 4. ASYNC TOOL DEFINITIONS ---

@mcp.tool()
async def web_search(query: str) -> str:
    """Search the web for general information using Serper API."""
    logger.info(f"TOOL EXEC: web_search query='{query}'")
    
    if not SERPER_API_KEY:
        return json.dumps({"error": "SERPAPI_API_KEY not configured"})

    # FIX: Use httpx for non-blocking Async HTTP requests
    try:
        url = "https://google.serper.dev/search"
        payload = json.dumps({"q": query, "num": 5})
        headers = {
            'X-API-KEY': SERPER_API_KEY,
            'Content-Type': 'application/json'
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, content=payload, timeout=10.0)
            response.raise_for_status()
            data = response.json()

        results = []
        for item in data.get("organic", []):
            results.append({
                "title": item.get("title", ""),
                "url": item.get("link", ""),
                "snippet": item.get("snippet", "")
            })
        
        logger.info(f"Found {len(results)} web results")
        return json.dumps({"results": results})

    except Exception as e:
        logger.error(f"Web search failed: {e}")
        return json.dumps({"error": str(e)})


@mcp.tool()
async def news_search(query: str) -> str:
    """Search for recent news articles using NewsAPI."""
    logger.info(f"TOOL EXEC: news_search query='{query}'")
    
    if not NEWS_API_KEY:
        return json.dumps({"error": "NEWSAPI_API_KEY not configured"})

    # FIX: Run the blocking NewsAPI client in a separate thread so it doesn't freeze the MCP server
    try:
        def _blocking_news_call():
            from newsapi import NewsApiClient
            newsapi_client = NewsApiClient(api_key=NEWS_API_KEY)
            return newsapi_client.get_everything(q=query, language="en", page_size=5)

        # Await the thread execution
        all_articles = await asyncio.to_thread(_blocking_news_call)
        
        results = []
        if all_articles and all_articles.get("articles"):
            for article in all_articles.get("articles", []):
                results.append({
                    "title": article.get("title", ""),
                    "url": article.get("url", ""),
                    "source": article.get("source", {}).get("name", "")
                })
        
        logger.info(f"Found {len(results)} news results")
        return json.dumps({"results": results})

    except Exception as e:
        logger.error(f"News search failed: {e}")
        return json.dumps({"error": str(e)})

# --- 5. RUN ENTRYPOINT ---
if __name__ == "__main__":
    logger.info("Starting FastMCP Server (Async Mode)...")
    mcp.run()