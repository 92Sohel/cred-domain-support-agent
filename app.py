from __future__ import annotations
import time, uuid
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from src.crew import build_crew
from src.governance import within_request_budget
from src.observability import log_request
from src.review import review_draft
from src.schemas import AddDocumentRequest, AskRequest, SupportResponse

app = FastAPI(title="Cred Domain Support Agent", version="1.0.0")
crew = build_crew()
def run_ask(query: str, session_id: str) -> SupportResponse:
    trace_id, started = str(uuid.uuid4()), time.perf_counter()
    if not within_request_budget(query):
        response = SupportResponse(answer="Request rejected: it exceeds the configured per-request budget.", confidence=1, trace_id=trace_id, guardrail_action="budget_rejected")
    else:
        response = crew.kickoff({"query": query, "session_id": session_id, "trace_id": trace_id})
        # The independent review stage is post-crew and gets the original retrieval context.
        if response.citations != ["loan_applications"] and response.guardrail_action != "prompt_injection_blocked":
            context = [hit["text"] for hit in crew.rag.retrieve(query)]
            verdict = review_draft(response.answer, context)
            response = response.model_copy(update={"answer": verdict.final_answer})
    log_request(trace_id, query, (time.perf_counter()-started)*1000, response.guardrail_action or "ok")
    return response

@app.post("/ask", response_model=SupportResponse)
def ask(request: AskRequest) -> SupportResponse: return run_ask(request.query, request.session_id)

@app.post("/add-document")
def add_document(request: AddDocumentRequest) -> dict:
    crew.rag.add_document(request.id, request.title, request.text)
    return {"indexed": request.id, "collections": ["cred_fixed_overlap", "cred_sentence"]}

@app.websocket("/ws/chat/{session_id}")
async def chat(websocket: WebSocket, session_id: str) -> None:
    await websocket.accept()
    try:
        while True:
            payload = await websocket.receive_json()
            await websocket.send_json(run_ask(str(payload.get("query", "")), session_id).model_dump())
    except WebSocketDisconnect:
        return
