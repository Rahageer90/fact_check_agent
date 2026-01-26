from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
# We only need to import the runner now, no shutdown logic needed
from app.agent import run_fact_check_agent

app = FastAPI(title="Fact Check Agent")

class FactCheckRequest(BaseModel):
    claim: str

@app.post("/fact-check")
async def fact_check(request: FactCheckRequest):
    """
    Endpoint to verify a claim using the AI Agent.
    """
    try:
        # Run the agent directly
        result = await run_fact_check_agent(request.claim)
        return result
    except Exception as e:
        # If something breaks, return the error
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def home():
    return {"message": "Fact Check Agent is Running! Go to /docs to test."}