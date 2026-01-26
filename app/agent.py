from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.tools import tool
from langchain_core.prompts import PromptTemplate
from services.gemini import get_gemini_llm
from mcp_tools.web_search import web_search as web_search_api
from mcp_tools.news_search import news_search as news_search_api


# Define tools for LangChain with @tool decorator
@tool
def web_search(query: str) -> str:
    """Call web search API to find general web evidence about a claim"""
    try:
        results = web_search_api(query)
        return str(results)
    except Exception as e:
        return f"Web search failed: {str(e)}"


@tool
def news_search(query: str) -> str:
    """Call news search API to find recent news articles about a claim"""
    try:
        results = news_search_api(query)
        return str(results)
    except Exception as e:
        return f"News search failed: {str(e)}"


def run_fact_check_agent(claim: str):
    """Run fact-check agent with LangChain ReAct pattern"""
    
    # Define tools for the agent
    tools = [web_search, news_search]
    
    # Get LLM
    llm = get_gemini_llm()
    
    # Define the ReAct prompt template
    prompt_template = """Answer the following questions as best you can. You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now have enough information to provide a verdict
Final Answer: the final answer to the original input question

Begin!

Question: {input}
{agent_scratchpad}"""
    
    prompt = PromptTemplate(
        template=prompt_template,
        input_variables=["input", "agent_scratchpad", "tools", "tool_names"]
    )
    
    # Create the ReAct agent
    agent = create_react_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        max_iterations=10,
        handle_parsing_errors=True
    )
    
    # Create the fact-check prompt
    fact_check_prompt = f"""Fact-check the following claim. You MUST use both web_search and news_search tools to gather evidence.

Claim: "{claim}"

Steps:
1. Use web_search to find general web evidence about the claim
2. Use news_search to find recent news evidence about the claim
3. Analyze the evidence from both sources
4. Provide your final verdict: either "Likely True", "Uncertain", or "Likely False"
5. Explain your reasoning based on the evidence found

Format your final answer as:
VERDICT: [Likely True/Uncertain/Likely False]
EXPLANATION: [Your detailed explanation based on the evidence]"""
    
    # Run the agent
    result = agent_executor.invoke({"input": fact_check_prompt})
    
    agent_output = result.get("output", "")
    
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
