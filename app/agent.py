from langchain.agents import initialize_agent, AgentType
from langchain.tools import Tool
from mcp_tools.web_search import web_search_tool
from mcp_tools.news_search import news_search_tool
from services.gemini import gemini_llm
from langchain.prompts import PromptTemplate

fact_check_prompt = PromptTemplate(
    input_variables=["claim"],
    template="""
You are a fact-checking agent. Your task is to verify the given claim using available tools.

Claim: {claim}

Steps:
1. Use web_search_tool to find general information about the claim.
2. Use news_search_tool to find recent news articles related to the claim.
3. Analyze the information and determine if the claim is True, False, or Partially True.
4. Provide a verdict, explanation, and list of sources.

Return your response in JSON format with keys: verdict, explanation, sources.
"""
)

async def fact_check_agent(claim: str):
    tools = [web_search_tool, news_search_tool]

    agent = initialize_agent(
        tools=tools,
        llm=gemini_llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True,
        prompt=fact_check_prompt
    )

    result = await agent.arun(claim)
    # Parse the result (assuming it's JSON)
    import json
    try:
        parsed_result = json.loads(result)
        return parsed_result
    except:
        return {
            "verdict": "Unknown",
            "explanation": "Failed to parse agent response",
            "sources": []
        }
