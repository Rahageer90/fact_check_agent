import logging
import json
import re
from typing import List, Dict
from contextlib import AsyncExitStack

from langchain_core.tools import tool
from langchain.agents import create_react_agent, AgentExecutor
from langchain_core.prompts import PromptTemplate
from mcp import ClientSession, StdioServerParameters
from mcp.client.sse import sse_client

from services.gemini import get_gemini_llm

# -------------------------------------------------------------------
# Logging
# -------------------------------------------------------------------

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fact_check_agent")

# -------------------------------------------------------------------
# MCP Client and Tool Wrapping
# -------------------------------------------------------------------

async def get_mcp_tools():
    """Connect to MCP server via SSE and wrap tools as LangChain tools."""
    async with AsyncExitStack() as stack:
        # Connect to MCP server via SSE
        transport = await stack.enter_async_context(sse_client("http://localhost:8000/sse"))
        session = await stack.enter_async_context(ClientSession(*transport))

        # List available tools
        tools_response = await session.list_tools()
        available_tools = tools_response.tools

        # Wrap MCP tools as LangChain tools
        langchain_tools = []
        for mcp_tool in available_tools:
            if mcp_tool.name in ["web_search", "news_search"]:
                langchain_tool = tool(
                    name=mcp_tool.name,
                    description=mcp_tool.description,
                    func=lambda query, tool_name=mcp_tool.name: call_mcp_tool(session, tool_name, query)
                )
                langchain_tools.append(langchain_tool)

        return langchain_tools

async def call_mcp_tool(session, tool_name, query):
    """Call an MCP tool via the session."""
    logger.info(f"[TOOL] {tool_name} called with query: {query}")
    result = await session.call_tool(tool_name, {"query": query})
    # Extract text from MCP response
    return result.content[0].text if result.content else "No result"


# -------------------------------------------------------------------
# Helper Functions
# -------------------------------------------------------------------

def extract_sources_from_text(text: str, source_type: str) -> List[Dict]:
    """
    Extract titles and URLs from tool output text and format as source objects.
    Tool output format: "- Title (URL)"
    """
    sources = []
    lines = text.strip().split('\n')

    for line in lines:
        line = line.strip()
        if line.startswith('- ') and '(' in line and ')' in line:
            # Parse "- Title (URL)" format
            content = line[2:].strip()  # Remove "- "
            if content.endswith(')') and '(' in content:
                title_part, url_part = content.rsplit('(', 1)
                title = title_part.strip()
                url = url_part.rstrip(')').strip()
                if url.startswith('http'):
                    sources.append({
                        "title": title,
                        "url": url,
                        "type": source_type
                    })

    return sources


def determine_verdict(output: str) -> str:
    """
    Determine verdict from LLM output in a robust way.
    """
    text = output.lower()

    if "likely false" in text or "false" in text:
        return "Likely False"
    if "likely true" in text or "true" in text:
        return "Likely True"

    return "Uncertain"


# -------------------------------------------------------------------
# Agent Runner
# -------------------------------------------------------------------

async def run_fact_check_agent(claim: str) -> dict:
    async with AsyncExitStack() as stack:
        # Connect to MCP server via SSE
        transport = await stack.enter_async_context(sse_client("http://localhost:8000/sse"))
        session = await stack.enter_async_context(ClientSession(*transport))

        # Get MCP tools wrapped as LangChain tools
        tools = await get_mcp_tools_with_session(session)

        llm = get_gemini_llm()

        prompt = PromptTemplate(
            input_variables=["input", "agent_scratchpad", "tools", "tool_names"],
            template="""You are a professional fact-checking AI.

You have access to the following tools:
{tools}

Tool names: {tool_names}

RULES (MANDATORY):
1. You MUST call web_search first.
2. You MUST call news_search second.
3. Do NOT give a verdict before using BOTH tools.

Use the following format strictly:

Question: {input}
Thought: reasoning about next step
Action: the tool to use
Action Input: the tool input
Observation: the tool result
... (repeat Thought/Action/Observation as needed)
Thought: I now have enough information
Final Answer: provide verdict and explanation

Begin.

Question: {input}
Thought:{agent_scratchpad}
"""
        )

        agent = create_react_agent(llm, tools, prompt)

        executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            handle_parsing_errors=True,
            return_intermediate_steps=True,
            max_iterations=10,
        )

        try:
            result = await executor.ainvoke({"input": claim})

            output = result["output"]
            steps = result.get("intermediate_steps", [])

            # -------------------------------------------------------------------
            # Enforce Tool Usage (Issue #2)
            # -------------------------------------------------------------------

            used_tools = {step[0].tool for step in steps}
            required_tools = {"web_search", "news_search"}

            if not required_tools.issubset(used_tools):
                raise ValueError(
                    f"Agent failed to use required tools. Used: {used_tools}"
                )

            # -------------------------------------------------------------------
            # Extract Sources (Issue #3)
            # -------------------------------------------------------------------

            sources: List[Dict] = []

            for action, observation in steps:
                if action.tool == "web_search":
                    sources.extend(extract_sources_from_text(observation, "web"))
                elif action.tool == "news_search":
                    sources.extend(extract_sources_from_text(observation, "news"))

            # Deduplicate sources by URL
            seen = set()
            unique_sources = []
            for src in sources:
                if src["url"] not in seen:
                    seen.add(src["url"])
                    unique_sources.append(src)

            verdict = determine_verdict(output)

            return {
                "verdict": verdict,
                "explanation": output,
                "sources": unique_sources[:10],
                "tools_used": list(required_tools),
            }

        except Exception as e:
            logger.exception("Fact-check agent failed")
            return {
                "verdict": "Uncertain",
                "explanation": f"Error during fact-checking: {str(e)}",
                "sources": [],
                "tools_used": [],
            }

async def get_mcp_tools_with_session(session):
    """Get MCP tools wrapped as LangChain tools using the provided session."""
    # List available tools
    tools_response = await session.list_tools()
    available_tools = tools_response.tools

    # Wrap MCP tools as LangChain tools
    langchain_tools = []
    for mcp_tool in available_tools:
        if mcp_tool.name in ["web_search", "news_search"]:
            async def tool_func(query, tool_name=mcp_tool.name):
                return await call_mcp_tool(session, tool_name, query)

            langchain_tool = tool(
                name=mcp_tool.name,
                description=mcp_tool.description,
                func=tool_func
            )
            langchain_tools.append(langchain_tool)

    return langchain_tools
