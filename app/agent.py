import json
import sys
from contextlib import AsyncExitStack
from langchain_core.tools import tool
from langchain.agents import create_react_agent, AgentExecutor
from langchain_core.prompts import PromptTemplate
from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters
from services.gemini import get_gemini_llm
import os
# Global MCP session (ONE per app)
_mcp_stack: AsyncExitStack | None = None
_mcp_session: ClientSession | None = None




async def init_mcp():
    global _mcp_stack, _mcp_session

    if _mcp_session:
        return _mcp_session

    _mcp_stack = AsyncExitStack()
    
    # Force UTF-8 environment
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUNBUFFERED"] = "1"

    # Configure Parameters
    params = StdioServerParameters(
        command=sys.executable,
        args=["-u", "-m", "mcp_tools.mcp_server"], 
        env=env
    )

    try:
        # Initialize
        read, write = await _mcp_stack.enter_async_context(stdio_client(params))
        _mcp_session = ClientSession(read, write)
        await _mcp_session.initialize()
        return _mcp_session
    except Exception as e:
        print(f"CRITICAL ERROR initializing MCP: {e}")
        if _mcp_stack:
            await _mcp_stack.aclose()
        _mcp_stack = None
        raise e
    
async def shutdown_mcp():
    global _mcp_session, _mcp_stack
    if _mcp_session:
        # ClientSession doesn't always have close(), but good to check implementation.
        # usually just closing the stack handles the transport closure.
        pass
        
    if _mcp_stack:
        await _mcp_stack.aclose()  # Properly close the AsyncExitStack
        _mcp_stack = None
        _mcp_session = None


# ===================== ASYNC TOOLS =====================

@tool
async def web_search(query: str) -> str:
    """
    Search the web for factual information related to a claim.
    MUST be called before news_search.
    """
    try:
        session = await init_mcp()
        result = await session.call_tool("web_search", {"query": query})
        return result.content[0].text if result.content else "{}"
    except Exception as e:
        return f"Error during web_search: {str(e)}"


@tool
async def news_search(query: str) -> str:
    """
    Search recent and authoritative news articles related to a claim.
    MUST be called after web_search.
    """
    try:
        session = await init_mcp()
        result = await session.call_tool("news_search", {"query": query})
        return result.content[0].text if result.content else "{}"
    except Exception as e:
        return f"Error during news_search: {str(e)}"


# ===================== AGENT =====================

def create_fact_check_agent():
    llm = get_gemini_llm()

    prompt = PromptTemplate(
        input_variables=[
            "input",
            "agent_scratchpad",
            "tools",
            "tool_names",
        ],
        template="""You are an expert fact-checking AI.

You have access to the following tools:
{tools}

Tool names: {tool_names}

RULES (MANDATORY):
1. You MUST call web_search FIRST
2. You MUST call news_search SECOND
3. Do NOT give a verdict before BOTH are called

Use the following format strictly:

Question: {input}
Thought: you should always think about what to do
Action: the tool name to use
Action Input: the input to the tool
Observation: the result of the tool
... (this Thought/Action/Observation can repeat)
Thought: I now have enough information
Final Answer: your fact-check verdict and explanation

Begin.

Question: {input}
Thought:{agent_scratchpad}
"""
    )

    tools = [web_search, news_search]
    agent = create_react_agent(llm, tools, prompt)
    return agent, tools


async def run_fact_check_agent(claim: str) -> dict:
    agent, tools = create_fact_check_agent()

    executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        return_intermediate_steps=True,
        max_iterations=10,
        handle_parsing_errors=True # Added stability for parsing errors
    )

    result = await executor.ainvoke({"input": claim})

    steps = result["intermediate_steps"]
    tool_names = [step[0].tool for step in steps]

    # Rule Enforcement
    if "web_search" not in tool_names or "news_search" not in tool_names:
        # If one failed, we might still want to return a result but mark it, 
        # but your assignment says "automatically rejected".
        # We will attempt to survive if at least one tool ran, but STRICTLY
        # the assignment asks for both.
        # For the sake of the assignment, we keep the error, but check logs if tools fail internally.
        pass # The validation below handles the rejection logic

    # Check for hard rule failure
    if "web_search" not in tool_names or "news_search" not in tool_names:
         raise ValueError("HARD RULE FAILED: Both MCP tools not called. Agent logic incomplete.")

    verdict = "Uncertain"
    output = result["output"]

    # Improved Verdict Parsing
    output_lower = output.lower()
    if "likely true" in output_lower:
        verdict = "Likely True"
    elif "likely false" in output_lower:
        verdict = "Likely False"
    # Default is Uncertain

    sources = []
    for action, obs in steps:
        try:
            # obs is the JSON string returned by the tool
            data = json.loads(obs)
            # The server returns {"results": [...]}
            for r in data.get("results", []):
                if r.get("url"):
                    sources.append({
                        "title": r.get("title", "Untitled"),
                        "url": r["url"],
                        "type": action.tool.replace("_search", "") # "web" or "news"
                    })
        except Exception:
            continue

    # dedupe sources by URL
    seen = set()
    final_sources = []
    for s in sources:
        if s["url"] not in seen:
            seen.add(s["url"])
            final_sources.append(s)

    return {
        "verdict": verdict,
        "explanation": output,
        "sources": final_sources[:10],
        "tools_used": ["web_search", "news_search"]
    }