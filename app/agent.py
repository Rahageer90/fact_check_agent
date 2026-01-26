from langchain_core.tools import tool
from services.gemini import get_gemini_llm
from mcp_tools.web_search import web_search as web_search_api
from mcp_tools.news_search import news_search as news_search_api


# Define tools for LangChain with @tool decorator
@tool
def web_search(query: str) -> str:
    """Search the web for general evidence about a claim. Returns a list of search results with titles and URLs."""
    try:
        results = web_search_api(query)
        return str(results)
    except Exception as e:
        return f"Web search failed: {str(e)}"


@tool
def news_search(query: str) -> str:
    """Search news articles for recent evidence about a claim. Returns a list of news articles with titles and URLs."""
    try:
        results = news_search_api(query)
        return str(results)
    except Exception as e:
        return f"News search failed: {str(e)}"


def run_fact_check_agent(claim: str):
    """Run fact-check agent using LangChain with tool calling"""
    
    # Get LLM
    llm = get_gemini_llm()
    
    # Bind tools to the LLM
    tools = [web_search, news_search]
    llm_with_tools = llm.bind_tools(tools)
    
    # Create the fact-check prompt
    fact_check_prompt = f"""You are a fact-checking AI assistant. Your task is to verify claims by searching for evidence.

Claim: "{claim}"

Instructions:
1. Use the web_search tool to find general web evidence about this claim
2. Use the news_search tool to find recent news evidence about this claim
3. Analyze all the evidence from both search results
4. Provide your verdict: "Likely True", "Uncertain", or "Likely False"
5. Explain your reasoning based on the evidence found

CRITICAL: You MUST call BOTH the web_search and news_search tools.

Format your final answer as:
VERDICT: [Likely True/Uncertain/Likely False]
EXPLANATION: [Your detailed explanation based on the evidence from both searches]"""
    
    # Run the LLM with tool calling
    try:
        # First call to get tool invocations
        response = llm_with_tools.invoke(fact_check_prompt)
        
        # Process tool calls if needed
        if hasattr(response, 'tool_calls') and response.tool_calls:
            # Execute tools
            tool_results = []
            for tool_call in response.tool_calls:
                if tool_call['name'] == 'web_search':
                    result = web_search_api(tool_call['args'].get('query', claim))
                    tool_results.append(f"Web Search Results: {result}")
                elif tool_call['name'] == 'news_search':
                    result = news_search_api(tool_call['args'].get('query', claim))
                    tool_results.append(f"News Search Results: {result}")
            
            # Get final response with tool results
            full_prompt = f"""{fact_check_prompt}

Tool Results:
{chr(10).join(tool_results)}

Now provide your verdict and explanation based on these search results."""
            
            agent_output = llm.invoke(full_prompt).content
        else:
            agent_output = response.content if hasattr(response, 'content') else str(response)
    except Exception as e:
        print(f"Error during agent execution: {e}")
        # Fallback: just call the tools directly
        agent_output = f"Agent error: {str(e)}. Calling tools directly..."
        web_results = web_search_api(claim)
        news_results = news_search_api(claim)
        agent_output += f"\n\nWeb Results: {web_results}\n\nNews Results: {news_results}"
    
    # Parse the agent output
    verdict = "Uncertain"
    explanation = agent_output
    
    if "verdict: likely true" in agent_output.lower():
        verdict = "Likely True"
    elif "verdict: likely false" in agent_output.lower():
        verdict = "Likely False"
    elif "verdict: uncertain" in agent_output.lower():
        verdict = "Uncertain"
    
    # Get sources from tool calls
    sources = []
    try:
        web_results = web_search_api(claim)
        news_results = news_search_api(claim)
        sources = web_results + news_results
    except Exception as e:
        print(f"Error retrieving sources: {e}")
    
    return {
        "verdict": verdict,
        "explanation": explanation,
        "sources": sources,
        "tools_used": ["web_search", "news_search"]
    }
