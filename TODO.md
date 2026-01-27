# TODO: Fact-Check AI Agent Implementation

## Step 1: Update MCP Server (mcp_tools/mcp_server.py)
- Change import from `mcp.server` to `fastmcp`
- Update server instantiation to use FastMCP
- Add SSE runner at the end for transport

## Step 2: Refactor Agent (app/agent.py)
- Remove local tool definitions and imports from mcp_server.py
- Implement MCP client connection using AsyncExitStack and SseServerTransport
- Use langchain_mcp_adapters to wrap MCP tools as LangChain tools
- Improve source extraction to parse titles and URLs from tool outputs
- Ensure agent enforces calling both tools

## Step 3: Update FastAPI App (app/main.py)
- Import Pydantic models from app.schemas
- Update endpoint to use FactCheckRequest and return FactCheckResponse

## Step 4: Test and Verify
- Run MCP server with SSE transport
- Run FastAPI app
- Test /fact-check endpoint with provided claims to ensure both tools are called
