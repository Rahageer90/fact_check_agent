"""
LangChain ReAct Agent with MCP Client (Corrected)
"""

import json
import asyncio
from contextlib import AsyncExitStack
from langchain_core.tools import tool
from langchain.agents import create_react_agent, AgentExecutor
from langchain_core.prompts import PromptTemplate
from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters
from services.gemini import get_gemini_llm

# Global MCP session
_mcp_stack: AsyncExitStack | None = None
_mcp_session: ClientSession | None = None


async def init_mcp():
    global _mcp_stack, _mcp_session

    if _mcp_session:
        return _mcp_session

    _mcp_stack = AsyncExitStack()
    await _mcp_stack.__aenter__()

    params = StdioServerParameters(
        command="python",
        args=["-m", "mcp_tools.mcp_server"]
    )

    transport = _mcp_stack.enter_context(stdio_client(params))
    read, write = await transport.__aenter__()

    _mcp_session = ClientSession(read, write)
    await _mcp_session.initialize()
    return _mcp_session


async def shutdown_mcp():
    global _mcp_session, _mcp_stack
    if _mcp_session:
        await _mcp_session.close()
    if _mcp_stack:
        await _mcp_stack.__aexit__(None, None, None)


def _run_async(coro):
    """Run async safely inside FastAPI/LangChain"""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        return asyncio.run_coroutine_threadsafe(coro, loop).result()
    else:
        return asyncio.run(coro)


# ===================== TOOLS =====================

@tool
def web_search(query: str) -> str:
    """
    Search the general web for factual information related to a claim.

    This tool MUST be used first during fact-checking.
    It retrieves general web evidence from search engines
    via the MCP web_search tool.
    """
    session = _run_async(init_mcp())
    result = _run_async(session.call_tool("web_search", {"query": query}))
    return result.content[0].text if result.content else "{}"


@tool
def news_search(query: str) -> str:
    """
    Search authoritative and recent news articles related to a claim.

    This tool MUST be used after web_search.
    It retrieves evidence from news sources via the MCP news_search tool.
    """
    session = _run_async(init_mcp())
    result = _run_async(session.call_tool("news_search", {"query": query}))
    return result.content[0].text if result.content else "{}"



# ===================== AGENT =====================

def create_fact_check_agent():
    llm = get_gemini_llm()

    prompt = PromptTemplate(
        input_variables=["input", "agent_scratchpad"],
        template="""
You are a fact-checking AI.

RULES:
- You MUST call web_search first
- You MUST call news_search second
- Do NOT give verdict before both are called

{tools}

Question: {input}
Thought:{agent_scratchpad}
"""
    )

    tools = [web_search, news_search]
    agent = create_react_agent(llm, tools, prompt)
    return agent, tools


def run_fact_check_agent(claim: str) -> dict:
    agent, tools = create_fact_check_agent()

    executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        return_intermediate_steps=True,
        max_iterations=10
    )

    result = executor.invoke({"input": claim})

    steps = result["intermediate_steps"]
    tool_names = [step[0].tool for step in steps]

    if "web_search" not in tool_names or "news_search" not in tool_names:
        raise ValueError("HARD RULE FAILED: Both MCP tools not called")

    verdict = "Uncertain"
    output = result["output"]

    if "LIKELY TRUE" in output.upper():
        verdict = "Likely True"
    elif "LIKELY FALSE" in output.upper():
        verdict = "Likely False"

    sources = []
    for action, obs in steps:
        try:
            data = json.loads(obs)
            for r in data.get("results", []):
                if r.get("url"):
                    sources.append({
                        "title": r.get("title", "Untitled"),
                        "url": r["url"],
                        "type": action.tool.replace("_search", "")
                    })
        except:
            pass

    # dedupe
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
