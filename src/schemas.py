from __future__ import annotations
from pydantic import BaseModel, Field

class SupportResponse(BaseModel):
    answer: str
    citations: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)
    escalation_recommended: bool = False
    trace_id: str
    guardrail_action: str | None = None

class ReviewVerdict(BaseModel):
    approved: bool
    final_answer: str
    reason: str

class AskRequest(BaseModel):
    query: str = Field(min_length=1, max_length=8000)
    session_id: str = "default"

class AddDocumentRequest(BaseModel):
    id: str
    title: str
    text: str = Field(min_length=20, max_length=10000)
