"""FastAPI entrypoint for Fact-Check AI Agent"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.schemas import FactCheckRequest, FactCheckResponse
from app.agent import run_fact_check_agent, start_mcp_server, stop_mcp_server


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle: startup and shutdown"""
    
    start_mcp_server()
    
    yield
    
    stop_mcp_server()


# Create FastAPI application
app = FastAPI(
    title="Fact-Check AI Agent",
    description="AI-powered fact-checking using LangChain ReAct agent with FastMCP server",
    version="1.0.0",
    lifespan=lifespan
)


@app.post("/fact-check", response_model=FactCheckResponse)
async def fact_check(request: FactCheckRequest):
    """
    Fact-check a claim using ReAct agent with dual search tools via MCP
    
    Args:
        request: FactCheckRequest with the claim to verify
        
    Returns:
        FactCheckResponse with verdict, explanation, sources, and tools used
    """
    result = run_fact_check_agent(request.claim)
    return FactCheckResponse(**result)


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Fact-Check AI Agent",
        "agent_type": "LangChain ReAct",
        "tools": ["web_search", "news_search"],
        "llm": "Gemini API"
    }


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Fact-Check AI Agent API",
        "version": "1.0.0",
        "endpoints": {
            "POST /fact-check": "Submit a claim for fact-checking",
            "GET /health": "Check API health status",
            "GET /docs": "Interactive API documentation (Swagger UI)",
            "GET /redoc": "Alternative API documentation (ReDoc)"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=False
    )