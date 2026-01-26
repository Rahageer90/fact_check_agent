import os
import requests
from fastmcp import FastMCP
from dotenv import load_dotenv

load_dotenv()

app = FastMCP("news_search_tool")

@app.tool()
def news_search(query: str) -> str:
    """
    Perform a news search using NewsAPI and return recent news articles.
    
    Args:
        query: The search query for news articles
        
    Returns:
        A string containing news articles with titles, URLs, and descriptions
    """
    api_key = os.getenv("NEWSAPI_API_KEY")
    if not api_key:
        return "Error: NEWSAPI_API_KEY not found in environment variables"
    
    try:
        url = "https://newsapi.org/v2/everything"
        params = {
            "q": query,
            "apiKey": api_key,
            "pageSize": 5,  # Limit to 5 articles
            "sortBy": "relevancy",
            "language": "en"
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        articles = []
        
        if "articles" in data:
            for article in data["articles"][:5]:
                title = article.get("title", "")
                url = article.get("url", "")
                description = article.get("description", "")
                source = article.get("source", {}).get("name", "")
                
                articles.append(f"Title: {title}\nSource: {source}\nURL: {url}\nDescription: {description}\n")
        
        return "\n".join(articles) if articles else "No news articles found"
    
    except Exception as e:
        return f"Error performing news search: {str(e)}"

# For LangChain compatibility
from langchain.tools import Tool

news_search_tool = Tool(
    name="news_search",
    description="Search for recent news articles related to a claim. Input should be a search query.",
    func=news_search
)
