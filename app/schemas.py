from pydantic import BaseModel
from typing import List, Literal


class FactCheckRequest(BaseModel):
    claim: str


class Source(BaseModel):
    title: str
    url: str
    type: Literal["web", "news"]


class FactCheckResponse(BaseModel):
    verdict: Literal["Likely True", "Uncertain", "Likely False"]
    explanation: str
    sources: List[Source]
    tools_used: List[str]
