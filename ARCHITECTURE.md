┌─────────────────────────────────────────┐
│        FastAPI Application              │
│      POST /fact-check endpoint          │
└────────────┬────────────────────────────┘
             │
┌────────────▼────────────────────────────┐
│    LangChain ReAct Agent                │
│  (Reasoning & Tool Orchestration)       │
└────────────┬─────────┬──────────────────┘
             │         │
        ┌────▼─┐   ┌───▼────┐
        │ Tool │   │  Tool  │
        └────┬─┘   └───┬────┘
     web_    │         │    news_
     search  │         │    search
             │         │
┌────────────▼─────────▼────────────────┐
│   MCP Client (StdioClientTransport)   │
│   Communicates via MCP Protocol       │
└────────────┬────────────────────────────┘
             │
┌────────────▼────────────────────────────┐
│  MCP Server (Subprocess)                │
│  - web_search handler (Serper API)      │
│  - news_search handler (NewsAPI)        │
└────────────┬────────────────────────────┘
             │
    ┌────────┴────────┐
    │                 │
┌───▼──┐         ┌────▼──┐
│Serper│         │NewsAPI│
│ API  │         │       │
└──────┘         └───────┘