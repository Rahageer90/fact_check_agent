# FastAPI entrypoint
from fastapi import FastAPI
from app.schemas import FactCheckRequest, FactCheckResponse
from app.agent import run_fact_check_agent

app = FastAPI(title="Fact-Check AI Agent")


@app.post("/fact-check", response_model=FactCheckResponse)
def fact_check(request: FactCheckRequest):
    result = run_fact_check_agent(request.claim)
    return result
