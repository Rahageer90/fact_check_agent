import logging
from typing import List, Dict, Any
from contextlib import AsyncExitStack

from langchain.agents import create_react_agent, AgentExecutor
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import StructuredTool

# MCP Imports
from mcp import ClientSession
from mcp.client.sse import sse_client

# Internal Imports
from services.gemini import get_gemini_llm

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fact_check_agent")

# -------------------------------------------------------------------
# 1. HELPER FUNCTIONS (Parsing & Verdicts)
# -------------------------------------------------------------------

def extract_sources(text: str, source_type: str) -> List[Dict[str, str]]:
    """Parses '- Title (URL)' format into structured source objects."""
    sources = []
    lines = text.strip().split('\n')
    for line in lines:
        line = line.strip()
        if line.startswith("- ") and "(" in line and line.endswith(")"):
            try:
                # Remove "- " prefix
                content = line[2:]
                # Split from the right to handle titles with parentheses
                title_part, url_part = content.rsplit("(", 1)
                url = url_part.rstrip(")")
                if url.startswith("http"):
                    sources.append({
                        "title": title_part.strip(),
                        "url": url,
                        "type": source_type
                    })
            except ValueError:
                continue
    return sources

def determine_verdict(text: str) -> str:
    text = text.lower()
    if "likely false" in text or "false" in text:
        return "Likely False"
    if "likely true" in text or "true" in text:
        return "Likely True"
    return "Uncertain"

# -------------------------------------------------------------------
# 2. CORE AGENT LOGIC (FIXED: Proper Session Lifecycle)
# -------------------------------------------------------------------

async def run_fact_check_agent(claim: str) -> Dict[str, Any]:
    """
    Execute fact-checking agent with proper MCP session lifecycle management.
    
    CRITICAL FIXES:
    1. Transport properly unpacked from sse_client tuple
    2. Session.initialize() called and awaited before any tool usage
    3. AgentExecutor.ainvoke() kept inside AsyncExitStack context
    4. Tool factory uses closure to capture tool_name correctly
    """
    # Hardcoded URL for local FastMCP SSE server
    sse_url = "http://localhost:8000/sse"

    # Use AsyncExitStack for robust context management
    async with AsyncExitStack() as stack:
        try:
            # A. Connect to Transport (FIXED: Proper tuple unpacking)
            logger.info(f"[MCP] Connecting to SSE transport at {sse_url}")
            read_stream, write_stream = await stack.enter_async_context(sse_client(sse_url))
            
            # B. Initialize Session (FIXED: Await initialize before any other calls)
            logger.info("[MCP] Initializing ClientSession")
            session = await stack.enter_async_context(ClientSession(read_stream, write_stream))
            await session.initialize()
            logger.info("[MCP] Session initialized successfully")

            # C. List Tools
            logger.info("[MCP] Listing available tools")
            tools_response = await session.list_tools()
            available_tools = tools_response.tools
            logger.info(f"[MCP] Found {len(available_tools)} tools: {[t.name for t in available_tools]}")

            # D. Tool Factory (CRITICAL: Closure captures tool_name)
            def make_tool_func(tool_name: str):
                """Factory to capture tool_name in closure."""
                async def implementation(query: str) -> str:
                    logger.info(f"[TOOL REQUEST] {tool_name} -> {query}")
                    try:
                        result = await session.call_tool(tool_name, arguments={"query": query})
                        # FastMCP returns a list of content blocks
                        if result.content and hasattr(result.content[0], "text"):
                            logger.info(f"[TOOL RESPONSE] {tool_name} returned data")
                            return result.content[0].text
                        logger.warning(f"[TOOL RESPONSE] {tool_name} returned no data")
                        return "No data returned."
                    except Exception as e:
                        logger.error(f"[TOOL ERROR] {tool_name} failed: {e}")
                        return f"Tool execution failed: {str(e)}"
                return implementation

            # E. Wrap Tools for LangChain (FIXED: Use StructuredTool.from_function)
            langchain_tools = []
            for mcp_tool in available_tools:
                if mcp_tool.name in ["web_search", "news_search"]:
                    # Use StructuredTool.from_function which accepts name and description
                    lc_tool = StructuredTool.from_function(
                        func=make_tool_func(mcp_tool.name),
                        name=mcp_tool.name,
                        description=mcp_tool.description,
                        coroutine=make_tool_func(mcp_tool.name)  # For async support
                    )
                    langchain_tools.append(lc_tool)
                    logger.info(f"[MCP] Registered tool: {mcp_tool.name}")

            if not langchain_tools:
                logger.error("[MCP] No compatible tools found on server")
                return {
                    "verdict": "Uncertain",
                    "explanation": "No tools found on MCP server.",
                    "sources": [],
                    "tools_used": []
                }

            # F. Configure Agent (Prompt & LLM)
            logger.info("[AGENT] Initializing Gemini LLM")
            llm = get_gemini_llm()
            
            # FIXED: Stricter prompt requiring both tools before Final Answer
            template = """You are a rigorous fact-checker that MUST use ALL available tools.

MANDATORY RULES:
1. You MUST call web_search at least once
2. You MUST call news_search at least once
3. You are FORBIDDEN from giving a Final Answer until BOTH tools have been used
4. If you skip a tool, you have failed the task

Tools available:
{tools}

Tool names: {tool_names}

Use this EXACT format:
Question: the question to answer
Thought: your reasoning about what to do next
Action: the tool name (must be from tool names above)
Action Input: the query for the tool
Observation: the tool's result
... (repeat Thought/Action/Action Input/Observation until you have used BOTH tools)
Thought: I have gathered evidence from both web_search and news_search
Final Answer: [Likely True / Likely False / Uncertain] followed by detailed explanation with evidence

Begin!

Question: {input}
Thought:{agent_scratchpad}
"""
            prompt = PromptTemplate(
                input_variables=["input", "agent_scratchpad", "tools", "tool_names"],
                template=template
            )

            logger.info("[AGENT] Creating ReAct agent")
            agent = create_react_agent(llm, langchain_tools, prompt)
            
            executor = AgentExecutor(
                agent=agent,
                tools=langchain_tools,
                verbose=True,
                handle_parsing_errors=True,
                return_intermediate_steps=True,
                max_iterations=10,  # Increased to ensure both tools can be called
                early_stopping_method="generate"
            )

            # G. Execute Agent (FIXED: Inside AsyncExitStack so session stays alive)
            logger.info(f"[AGENT] Starting fact-check for claim: {claim}")
            result = await executor.ainvoke({"input": claim})
            logger.info("[AGENT] Execution completed successfully")
            
            # H. Process Output (Strict Schema Compliance)
            output_text = result["output"]
            steps = result.get("intermediate_steps", [])

            # Extract Sources & Tools Used
            used_tools = set()
            all_sources = []
            
            for action, observation in steps:
                used_tools.add(action.tool)
                logger.info(f"[PROCESSING] Tool used: {action.tool}")
                if action.tool == "web_search":
                    all_sources.extend(extract_sources(observation, "web"))
                elif action.tool == "news_search":
                    all_sources.extend(extract_sources(observation, "news"))

            # Deduplicate sources by URL
            unique_sources = {s['url']: s for s in all_sources}.values()

            # Validate that both tools were used
            if len(used_tools) < 2:
                logger.warning(f"[AGENT] Only {len(used_tools)} tool(s) used: {used_tools}")

            logger.info(f"[RESULT] Verdict: {determine_verdict(output_text)}, Sources: {len(list(unique_sources))}")
            return {
                "verdict": determine_verdict(output_text),
                "explanation": output_text,
                "sources": list(unique_sources)[:10],
                "tools_used": list(used_tools)
            }

        except Exception as e:
            logger.error(f"[FATAL] Agent Execution Failed: {e}", exc_info=True)
            return {
                "verdict": "Uncertain",
                "explanation": f"System error during fact check: {str(e)}",
                "sources": [],
                "tools_used": []
            }