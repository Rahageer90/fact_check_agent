import os
import json
import httpx
from dotenv import load_dotenv

# 1. Load Environment Variables
load_dotenv()

# We use os.getenv to read from your .env file
SERPER_API_KEY = os.getenv("SERPAPI_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

async def web_search_tool(query: str) -> str:
    """Local Python function to search the web using Serper."""
    print(f"\n[TOOL] Executing web_search for: '{query}'")
    
    if not SERPER_API_KEY:
        return "ERROR: SERPAPI_API_KEY not found in .env file."
    
    url = "https://google.serper.dev/search"
    payload = json.dumps({"q": query, "num": 5})
    headers = {'X-API-KEY': SERPER_API_KEY, 'Content-Type': 'application/json'}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, content=payload, timeout=20.0)
            response.raise_for_status()
            data = response.json()

        results = []
        for item in data.get("organic", []):
            title = item.get('title', 'No Title')
            snippet = item.get('snippet', 'No Snippet')
            link = item.get('link', '')
            results.append(f"- {title} ({link}): {snippet}")
        
        return "\n".join(results) if results else "No results found."

    except Exception as e:
        print(f"[TOOL ERROR] Web Search failed: {e}")
        return f"Error searching web: {str(e)}"

async def news_search_tool(query: str) -> str:
    """Local Python function to search news using NewsAPI.org."""
    print(f"\n[TOOL] Executing news_search for: '{query}'")
    
    if not NEWS_API_KEY:
        return "ERROR: NEWS_API_KEY not found in .env file."

    # Using HTTPX directly is faster and safer than the blocking library
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": query,
        "apiKey": NEWS_API_KEY,
        "language": "en",
        "pageSize": 5,
        "sortBy": "relevancy"
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, timeout=20.0)
            response.raise_for_status()
            data = response.json()

        results = []
        if data.get("articles"):
            for article in data.get("articles", []):
                title = article.get("title", "No Title")
                source = article.get("source", {}).get("name", "Unknown Source")
                description = article.get("description", "No Description")
                url = article.get("url", "")
                results.append(f"- [{source}] {title}: {description} ({url})")
        
        return "\n".join(results) if results else "No news found."

    except Exception as e:
        print(f"[TOOL ERROR] News Search failed: {e}")
        return f"Error searching news: {str(e)}"