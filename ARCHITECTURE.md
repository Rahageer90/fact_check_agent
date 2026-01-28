# Fact-Check AI Agent Architecture

## Overview
This is a comprehensive fact-checking AI agent system built using modern Python frameworks and protocols. The system leverages Model Context Protocol (MCP) for tool integration, LangChain for agent orchestration, and FastAPI for web services. It provides automated fact-checking capabilities by querying web and news sources to verify claims.

## Core Components

### 1. FastAPI Web Application (`app/main.py`)
- **Purpose**: Provides REST API endpoints for client interactions
- **Key Features**:
  - `/fact-check` POST endpoint: Accepts claims for verification
  - `/` GET endpoint: Health check
  - Error handling with HTTPException
- **Dependencies**: Uses Pydantic schemas for request/response validation

### 2. AI Agent Logic (`app/agent.py`)
- **Purpose**: Core fact-checking intelligence using LangChain ReAct agent
- **Key Features**:
  - Asynchronous MCP client integration with proper session lifecycle management
  - Tool wrapping using LangChain's StructuredTool
  - Source extraction and verdict determination
  - Strict enforcement of using both web and news search tools
- **Architecture**:
  - Uses AsyncExitStack for robust resource management
  - Implements SSE transport for MCP communication
  - Processes intermediate steps to extract sources and track tool usage

### 3. MCP Server (`mcp_tools/mcp_server.py`)
- **Purpose**: Provides external tool capabilities via Model Context Protocol
- **Tools Implemented**:
  - `web_search`: Uses Google Serper API for general web search
  - `news_search`: Uses NewsAPI for recent news articles
- **Framework**: Built with FastMCP for simplified MCP implementation
- **Transport**: Supports SSE (Server-Sent Events) for real-time communication

### 4. Data Models (`app/schemas.py`)
- **Purpose**: Defines structured data contracts using Pydantic
- **Models**:
  - `FactCheckRequest`: Input claim validation
  - `FactCheckResponse`: Output with verdict, explanation, sources, and tools used
  - `Source`: Structured source information with title, URL, and type

### 5. LLM Integration (`services/gemini.py`)
- **Purpose**: Provides language model capabilities for agent reasoning
- **Implementation**: Integrates Google's Gemini LLM via LangChain

## System Architecture Flow

```
Client Request
    ↓
FastAPI Endpoint (/fact-check)
    ↓
Agent Execution (run_fact_check_agent)
    ↓
MCP Client Connection (SSE Transport)
    ↓
Tool Discovery & Wrapping
    ↓
LangChain ReAct Agent
    ↓
Parallel Tool Calls (web_search + news_search)
    ↓
Source Extraction & Verdict Determination
    ↓
Structured Response
```

## Key Design Patterns

### 1. Separation of Concerns
- **API Layer**: FastAPI handles HTTP requests/responses
- **Business Logic**: Agent module manages fact-checking workflow
- **Tool Layer**: MCP server provides external data sources
- **Data Layer**: Pydantic schemas ensure type safety

### 2. Asynchronous Programming
- Full async/await implementation for scalability
- Proper resource management with AsyncExitStack
- Concurrent tool execution potential

### 3. Protocol-Based Tool Integration
- MCP enables standardized tool discovery and calling
- LangChain adapters bridge MCP tools to agent framework
- SSE transport for real-time bidirectional communication

### 4. Error Handling & Resilience
- Comprehensive try/catch blocks at multiple levels
- Graceful degradation when tools fail
- Detailed logging for debugging

## Dependencies & Environment

### Core Dependencies
- **FastAPI**: Web framework
- **LangChain**: Agent orchestration
- **MCP**: Tool protocol
- **Pydantic**: Data validation
- **httpx**: Async HTTP client
- **uvicorn**: ASGI server

### External APIs
- **Google Serper API**: Web search capabilities
- **NewsAPI**: News article search
- **Google Gemini**: Language model

### Environment Configuration
- Uses python-dotenv for API key management
- Requires SERPAPI_API_KEY and NEWSAPI_API_KEY

## Deployment Considerations

### Local Development
- Run MCP server with SSE transport
- Start FastAPI application
- Ensure API keys are configured

### Production Deployment
- Containerization recommended
- Separate MCP server and API application instances
- Load balancing for scalability
- Monitoring and logging integration

## Future Enhancements
Based on TODO.md, planned improvements include:
- Enhanced MCP server configuration
- Improved agent tool integration
- Better source parsing and validation
- Comprehensive testing suite
