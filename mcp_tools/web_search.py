import os
import json
import http.client
from dotenv import load_dotenv

load_dotenv()

SERPER_API_KEY = os.getenv("SERPAPI_API_KEY")

if not SERPER_API_KEY:
    raise ValueError("SERPAPI_API_KEY environment variable is not set")


def web_search(query: str) -> list:
    """Retrieve general web evidence using Google Serper API"""
    try:
        conn = http.client.HTTPSConnection("google.serper.dev")
        
        payload = json.dumps({
            "q": query,
            "num": 10  # Number of results - increased for better coverage
        })
        
        headers = {
            'X-API-KEY': SERPER_API_KEY,
            'Content-Type': 'application/json'
        }
        
        conn.request("POST", "/search", payload, headers)
        res = conn.getresponse()
        data = json.loads(res.read().decode("utf-8"))
        
        results = []
        
        # Extract organic search results with additional metadata
        for item in data.get("organic", []):
            result = {
                "title": item.get("title", ""),
                "url": item.get("link", ""),
                "type": "web",
                "snippet": item.get("snippet", ""),
                "position": item.get("position", 0)
            }
            results.append(result)
        
        conn.close()
        
        return results if results else [{"title": "No results found", "url": "", "type": "web"}]
    
    except Exception as e:
        error_msg = f"Web Search Error: {str(e)}"
        print(f"❌ {error_msg}")
        return [{"title": error_msg, "url": "", "type": "web", "error": True}]