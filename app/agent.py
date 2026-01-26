"""
LangChain ReAct Agent with MCP Client
Communicates with MCP server to call web_search and news_search tools
"""

import json
import os
import subprocess
import time
import asyncio
from dotenv import load_dotenv
from services.gemini import get_gemini_llm
from langchain_core.tools import tool
from langchain.agents import create_react_agent, AgentExecutor
from langchain_core.prompts import PromptTemplate
from mcp import ClientSession
from mcp.client.stdio import StdioClientTransport

load_dotenv()

# MCP Server process reference
mcp_process = None
mcp_session: ClientSession = None


def start_mcp_server():
    """Start the MCP server as a subprocess"""
    global mcp_process
    try:
        mcp_process = subprocess.Popen(
            ["python", "-m", "mcp_tools.mcp_server"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        time.sleep(3)
        
        if mcp_process.poll() is None:
            return True
        else:
            return False
    except Exception:
        return False


def stop_mcp_server():
    """Stop the MCP server"""
    global mcp_process
    if mcp_process:
        try:
            mcp_process.terminate()
            mcp_process.wait(timeout=5)
        except Exception:
            pass


async def get_mcp_session():
    """Get or create MCP client session"""
    global mcp_session
    
    if mcp_session is not None:
        return mcp_session
    
    try:
        transport = StdioClientTransport(
            command="python",
            args=["-m", "mcp_tools.mcp_server"]
        )
        
        mcp_session = ClientSession(transport)
        await mcp_session.initialize()
        return mcp_session
    except Exception:
        raise


async def close_mcp_session():
    """Close MCP client session"""
    global mcp_session
    if mcp_session:
        try:
            await mcp_session.close()
            mcp_session = None
        except Exception:
            pass


# ============================================================================
# Tool Implementations - Call MCP Server via Client
# ============================================================================

@tool
def web_search(query: str) -> str:
    """
    Search the web for information about a claim using MCP web_search tool.
    
    Args:
        query: The search query string
        
    Returns:
        JSON string containing search results with title, URL, and source type
    """
    try:
        session = asyncio.run(get_mcp_session())
        result = asyncio.run(session.call_tool("web_search", {"query": query}))
        
        if result.content and len(result.content) > 0:
            text_content = result.content[0].text
            return text_content
        else:
            return json.dumps({"error": "No content returned", "results": [], "count": 0})
    
    except Exception as e:
        return json.dumps({"error": str(e), "results": [], "count": 0})


@tool
def news_search(query: str) -> str:
    """
    Search recent news articles for information about a claim using MCP news_search tool.
    
    Args:
        query: The search query string
        
    Returns:
        JSON string containing news articles with title, URL, and source type
    """
    try:
        session = asyncio.run(get_mcp_session())
        result = asyncio.run(session.call_tool("news_search", {"query": query}))
        
        if result.content and len(result.content) > 0:
            text_content = result.content[0].text
            return text_content
        else:
            return json.dumps({"error": "No content returned", "results": [], "count": 0})
    
    except Exception as e:
        return json.dumps({"error": str(e), "results": [], "count": 0})


# ============================================================================
# ReAct Agent Configuration
# ============================================================================

def create_fact_check_agent():
    """Create and configure the ReAct agent for fact-checking."""
    
    llm = get_gemini_llm()
    
    system_prompt = """You are an expert fact-checking AI assistant with access to search tools.

Your task is to verify factual claims by gathering evidence from multiple sources.

CRITICAL RULES:
1. FIRST ACTION: Call web_search with the claim or key terms
2. SECOND ACTION: Call news_search with the same or similar query
3. You MUST complete BOTH actions before making any conclusions
4. ONLY after both tools have returned results, analyze and provide verdict
5. Do NOT provide a final answer until you have results from BOTH tools
6. If either tool returns no results, still wait for both to complete

VERDICT CLASSIFICATIONS:
- "Likely True": Strong supporting evidence from multiple sources, minimal contradictions
- "Likely False": Strong contradicting evidence from credible sources
- "Uncertain": Mixed evidence, conflicting information, or insufficient data

FORMAT YOUR FINAL RESPONSE EXACTLY AS:
VERDICT: [Likely True | Likely False | Uncertain]
EXPLANATION: [Your detailed reasoning based on evidence from both tools]
SOURCES_USED: [List the sources that influenced your verdict]"""

    prompt = PromptTemplate(
        input_variables=["input", "agent_scratchpad"],
        template=system_prompt + """

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now have results from both web_search and news_search tools, I can provide final answer
Final Answer: [Your structured response with VERDICT, EXPLANATION, and SOURCES_USED]

Begin!

Question: {input}
Thought:{agent_scratchpad}"""
    )
    
    tools = [web_search, news_search]
    agent = create_react_agent(llm, tools, prompt)
    
    return agent, tools


# ============================================================================
# Main Fact-Check Function
# ============================================================================

def run_fact_check_agent(claim: str) -> dict:
    """
    Run the fact-check agent for a given claim.
    
    Args:
        claim: The factual claim to verify
        
    Returns:
        Dictionary with verdict, explanation, sources, and tools_used
        
    Raises:
        ValueError: If both tools were not called
    """
    
    agent, tools = create_fact_check_agent()
    
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=False,
        max_iterations=20,
        handle_parsing_errors=True
    )
    
    try:
        result = agent_executor.invoke({"input": claim})
        
        output = result.get("output", "")
        intermediate_steps = result.get("intermediate_steps", [])
        
        web_search_called = False
        news_search_called = False
        web_results = []
        news_results = []
        
        for action, observation in intermediate_steps:
            tool_name = action.tool
            
            if tool_name == "web_search":
                web_search_called = True
                try:
                    obs_data = json.loads(observation)
                    web_results = obs_data.get("results", [])
                except:
                    pass
                    
            elif tool_name == "news_search":
                news_search_called = True
                try:
                    obs_data = json.loads(observation)
                    news_results = obs_data.get("results", [])
                except:
                    pass
        
        if not web_search_called:
            raise ValueError(
                "HARD RULE FAILED: web_search tool must be called."
            )
        
        if not news_search_called:
            raise ValueError(
                "HARD RULE FAILED: news_search tool must be called."
            )
        
        verdict = "Uncertain"
        explanation = output
        
        output_upper = output.upper()
        if "VERDICT: LIKELY TRUE" in output_upper or "VERDICT:LIKELY TRUE" in output_upper:
            verdict = "Likely True"
        elif "VERDICT: LIKELY FALSE" in output_upper or "VERDICT:LIKELY FALSE" in output_upper:
            verdict = "Likely False"
        elif "VERDICT: UNCERTAIN" in output_upper or "VERDICT:UNCERTAIN" in output_upper:
            verdict = "Uncertain"
        
        all_sources = []
        
        for result in web_results:
            if isinstance(result, dict) and result.get("url"):
                all_sources.append({
                    "title": result.get("title", "Untitled"),
                    "url": result.get("url", ""),
                    "type": "web"
                })
        
        for result in news_results:
            if isinstance(result, dict) and result.get("url"):
                all_sources.append({
                    "title": result.get("title", "Untitled"),
                    "url": result.get("url", ""),
                    "type": "news"
                })
        
        seen_urls = set()
        unique_sources = []
        for source in all_sources:
            if source["url"] not in seen_urls:
                seen_urls.add(source["url"])
                unique_sources.append(source)
        
        final_sources = unique_sources[:10]
        
        return {
            "verdict": verdict,
            "explanation": explanation,
            "sources": final_sources,
            "tools_used": ["web_search", "news_search"]
        }
        
    except ValueError as e:
        raise
    except Exception as e:
        raise