from fastapi import FastAPI, HTTPException
from app.agent import run_fact_check_agent
from app.schemas import FactCheckRequest, FactCheckResponse

app = FastAPI(title="Fact Check Agent")

@app.post("/fact-check", response_model=FactCheckResponse)
async def fact_check(request: FactCheckRequest):
    """
    Endpoint to verify a claim using the AI Agent.
    """
    try:
        # Run the agent (logic is now safely inside agent.py)
        result = await run_fact_check_agent(request.claim)
        return FactCheckResponse(**result)
    except Exception as e:
        # If something drastically fails outside the agent's try/except
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def home():
    return {"message": "Fact Check Agent is Running! Go to /docs to test."}