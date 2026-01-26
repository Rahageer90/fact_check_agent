import logging
from langchain_core.tools import tool
from langchain.agents import create_react_agent, AgentExecutor
from langchain_core.prompts import PromptTemplate
from services.gemini import get_gemini_llm

# IMPORT TOOLS DIRECTLY (No Network required!)
from mcp_tools.mcp_server import web_search_tool, news_search_tool

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("agent")

# --- DEFINE LANGCHAIN TOOLS ---

@tool
async def web_search(query: str) -> str:
    """Search the web for information."""
    # Directly call the python function
    return await web_search_tool(query)

@tool
async def news_search(query: str) -> str:
    """Search for news articles."""
    return await news_search_tool(query)

# --- AGENT LOGIC ---

async def run_fact_check_agent(claim: str) -> dict:
    llm = get_gemini_llm()
    tools = [web_search, news_search]
    
    template = """Answer the following questions as best you can. You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Claim: {input}
Thought:{agent_scratchpad}"""

    prompt = PromptTemplate(
        input_variables=["input", "agent_scratchpad", "tools", "tool_names"],
        template=template
    )
    
    agent = create_react_agent(llm, tools, prompt)
    
    executor = AgentExecutor(
        agent=agent, 
        tools=tools, 
        verbose=True, 
        handle_parsing_errors=True
    )

    try:
        result = await executor.ainvoke({"input": claim})
        output = result["output"]
        
        verdict = "Uncertain"
        lower_out = output.lower()
        if "true" in lower_out: verdict = "Likely True"
        if "false" in lower_out: verdict = "Likely False"
        
        return {
            "verdict": verdict,
            "explanation": output,
            "sources": [], 
            "tools_used": ["web_search", "news_search"]
        }
    except Exception as e:
        return {"verdict": "Error", "explanation": str(e), "sources": [], "tools_used": []}