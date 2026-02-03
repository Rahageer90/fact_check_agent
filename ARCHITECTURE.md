# Fact-Check AI Agent Workflow

## Application Flowchart

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT REQUEST                           │
│  POST /fact-check with JSON: {"claim": "The Earth is flat"}     │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FASTAPI ENDPOINT                             │
│  app/main.py: fact_check() function                             │
│  - Validates request using FactCheckRequest schema             │
│  - Calls run_fact_check_agent(request.claim)                    │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   AGENT EXECUTION                               │
│  app/agent.py: run_fact_check_agent(claim)                      │
│  - Establishes MCP client connection via SSE transport         │
│  - Initializes session with MCP server at localhost:8000/sse   │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   TOOL DISCOVERY                                │
│  - Lists available tools from MCP server                        │
│  - Finds web_search and news_search tools                       │
│  - Wraps MCP tools into LangChain StructuredTool objects       │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                 LANGCHAIN REACT AGENT                           │
│  - Initializes Gemini LLM (gemini-2.0-flash)                    │
│  - Creates ReAct agent with custom prompt                       │
│  - AgentExecutor configured with tools and max_iterations=10   │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                 TOOL EXECUTION                                  │
│  Agent calls tools in loop until both are used:                │
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐                     │
│  │   web_search    │    │   news_search   │                     │
│  │ (Google Serper) │    │   (NewsAPI)     │                     │
│  │                 │    │                 │                     │
│  │ - Queries web   │    │ - Queries news  │                     │
│  │ - Returns top 5 │    │ - Returns top 5 │                     │
│  │   results       │    │   articles      │                     │
│  └─────────────────┘    └─────────────────┘                     │
│            │                       │                           │
│            └───────────┬───────────┘                           │
│                        │                                       │
│                        ▼                                       │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │            COLLECT AND PROCESS RESULTS                 │   │
│  │  - Extracts sources from tool responses                 │   │
│  │  - Parses "- Title (URL)" format into structured data   │   │
│  │  - Deduplicates sources by URL                          │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│               VERDICT DETERMINATION                             │
│  - Agent analyzes collected evidence                            │
│  - Uses Gemini LLM to reason about claim veracity              │
│  - Determines verdict: Likely True/Likely False/Uncertain      │
│  - Generates detailed explanation with evidence                 │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                 STRUCTURED RESPONSE                             │
│  Returns FactCheckResponse:                                     │
│  {                                                              │
│    "verdict": "Likely False",                                   │
│    "explanation": "Based on scientific evidence...",           │
│    "sources": [                                                 │
│      {"title": "...", "url": "...", "type": "web"}              │
│    ],                                                           │
│    "tools_used": ["web_search", "news_search"]                  │
│  }                                                              │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      CLIENT RESPONSE                            │
│  FastAPI returns JSON response to client                       │
└─────────────────────────────────────────────────────────────────┘
```

## Key Components Involved

### 1. FastAPI Application (app/main.py)
- Entry point for HTTP requests
- Routes to agent execution
- Handles errors and responses

### 2. MCP Server (mcp_tools/mcp_server.py)
- Runs separately on port 8000
- Provides web_search and news_search tools
- Uses FastMCP framework with SSE transport

### 3. Agent Logic (app/agent.py)
- Manages MCP client session lifecycle
- Wraps tools for LangChain compatibility
- Orchestrates the fact-checking process

### 4. LLM Service (services/gemini.py)
- Provides Gemini 2.0 Flash model
- Used by LangChain agent for reasoning

### 5. Data Schemas (app/schemas.py)
- FactCheckRequest: Input validation
- FactCheckResponse: Output structure
- Source: Individual source format

## External Dependencies
- **Google Serper API**: For web search results
- **NewsAPI**: For news article search
- **Google Gemini API**: For language model reasoning

## Execution Requirements
1. MCP server must be running: `fastmcp run mcp_tools/mcp_server.py --transport sse`
2. FastAPI app must be running: `python -m uvicorn app.main:app --port 9090`
3. Environment variables configured in .env file
