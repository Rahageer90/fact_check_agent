import os
import json
import http.client
from dotenv import load_dotenv

load_dotenv()

SERPER_API_KEY = os.getenv("SERPAPI_API_KEY")


def web_search(query: str) -> list:
    """Retrieve general web evidence using Google Serper API"""
    if not SERPER_API_KEY:
        return [{"title": "API Key Missing", "url": "", "type": "web"}]
    
    try:
        conn = http.client.HTTPSConnection("google.serper.dev")
        
        payload = json.dumps({
            "q": query,
            "num": 5  # Number of results
        })
        
        headers = {
            'X-API-KEY': SERPER_API_KEY,
            'Content-Type': 'application/json'
        }
        
        conn.request("POST", "/search", payload, headers)
        res = conn.getresponse()
        data = json.loads(res.read().decode("utf-8"))
        
        results = []
        
        # Extract organic search results
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