"""MCP Tools Package for Fact-Check Agent

This package contains MCP (Model Context Protocol) server implementations
for web search and news search tools.
"""

from .web_search import web_search
from .news_search import news_search

__all__ = ["web_search", "news_search"]
__version__ = "1.0.0"
