from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.schemas import FactCheckRequest, FactCheckResponse
from app.agent import run_fact_check_agent, shutdown_mcp

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await shutdown_mcp()

app = FastAPI(
    title="Fact-Check AI Agent",
    version="1.0.0",
    lifespan=lifespan
)

@app.post("/fact-check", response_model=FactCheckResponse)
async def fact_check(request: FactCheckRequest):
    return run_fact_check_agent(request.claim)
