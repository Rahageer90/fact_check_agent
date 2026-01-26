"""
MCP Server for Fact-Check AI Agent
Provides web_search and news_search tools via MCP protocol
"""

import os
import json
import http.client
from dotenv import load_dotenv
from mcp.server import Server
from mcp.types import Tool, TextContent

load_dotenv()

SERPER_API_KEY = os.getenv("SERPAPI_API_KEY")
NEWS_API_KEY = os.getenv("NEWSAPI_API_KEY")

# Initialize MCP Server
server = Server("fact-check-mcp-server")


def web_search(query: str) -> str:
    """Search the web using Google Serper API"""
    if not SERPER_API_KEY:
        return json.dumps({
            "error": "SERPAPI_API_KEY not configured", 
            "results": [],
            "count": 0
        })

    try:
        conn = http.client.HTTPSConnection("google.serper.dev")
        payload = json.dumps({
            "q": query,
            "num": 10
        })
        headers = {
            'X-API-KEY': SERPER_API_KEY,
            'Content-Type': 'application/json'
        }
        
        conn.request("POST", "/search", payload, headers)
        res = conn.getresponse()
        data = json.loads(res.read().decode("utf-8"))
        conn.close()
        
        results = []
        for item in data.get("organic", []):
            results.append({
                "title": item.get("title", ""),
                "url": item.get("link", ""),
                "type": "web",
                "snippet": item.get("snippet", ""),
                "position": item.get("position", 0)
            })
        
        return json.dumps({
            "results": results if results else [],
            "query": query,
            "count": len(results)
        })
    
    except Exception as e:
        return json.dumps({
            "error": str(e),
            "results": [],
            "count": 0
        })


def news_search(query: str) -> str:
    """Search for news articles using NewsAPI"""
    if not NEWS_API_KEY:
        return json.dumps({
            "error": "NEWSAPI_API_KEY not configured", 
            "results": [],
            "count": 0
        })

    try:
        from newsapi import NewsApiClient
        newsapi_client = NewsApiClient(api_key=NEWS_API_KEY)
        
        all_articles = newsapi_client.get_everything(
            q=query,
            language="en",
            page_size=10,
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
                    "published_at": article.get("publishedAt", ""),
                    "description": article.get("description", "")
                })

        return json.dumps({
            "results": results if results else [],
            "query": query,
            "count": len(results)
        })
    except Exception as e:
        return json.dumps({
            "error": str(e),
            "results": [],
            "count": 0
        })


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls from the client"""
    
    if name == "web_search":
        query = arguments.get("query", "")
        if not query:
            return [TextContent(type="text", text=json.dumps({"error": "query parameter required"}))]
        
        result = web_search(query)
        return [TextContent(type="text", text=result)]
    
    elif name == "news_search":
        query = arguments.get("query", "")
        if not query:
            return [TextContent(type="text", text=json.dumps({"error": "query parameter required"}))]
        
        result = news_search(query)
        return [TextContent(type="text", text=result)]
    
    else:
        error_response = json.dumps({"error": f"Unknown tool: {name}"})
        return [TextContent(type="text", text=error_response)]


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools"""
    return [
        Tool(
            name="web_search",
            description="Search the web for information using Google Serper API",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query string"
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="news_search",
            description="Search recent news articles using NewsAPI",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query string"
                    }
                },
                "required": ["query"]
            }
        )
    ]


async def main():
    """Run the MCP server"""
    async with server.stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())