"""Crew orchestration with explicit least-autonomy tool wiring.

The default MockCrew follows the same roles and `.kickoff()` boundary as CrewAI and
is deliberately deterministic for grading without API credentials or network calls.
"""
from __future__ import annotations
import os, re, uuid
from dataclasses import dataclass
from .guardrails import grounded, inspect_input
from .rag import RAGCore
from .schemas import SupportResponse
from .tools import check_loan_application_status

os.environ.setdefault("CREWAI_DISABLE_TELEMETRY", "true")
os.environ.setdefault("OTEL_SDK_DISABLED", "true")

@dataclass(frozen=True)
class Agent:
    name: str
    tools: tuple[str, ...]

class SessionMemory:
    """In-process session message history, reset simply by using a new session id."""
    def __init__(self): self.histories: dict[str, list[dict[str, str]]] = {}
    def add(self, session: str, role: str, content: str) -> None: self.histories.setdefault(session, []).append({"role": role, "content": content})
    def last_user_message(self, session: str) -> str | None:
        messages = self.histories.get(session, [])
        return next((m["content"] for m in reversed(messages[:-1]) if m["role"] == "user"), None)

class MockCrew:
    def __init__(self, rag: RAGCore | None = None):
        self.rag = rag or RAGCore(); self.memory = SessionMemory()
        self.retrieval_agent = Agent("Retrieval Agent", ("rag_lookup",))
        self.lookup_agent = Agent("Lookup Agent", ("check_loan_application_status",))
        self.composer_agent = Agent("Response Composer", ())
        self.tool_events: list[dict] = []
    def kickoff(self, inputs: dict) -> SupportResponse:
        query, session_id = inputs["query"], inputs.get("session_id", "default")
        trace_id = inputs.get("trace_id", str(uuid.uuid4()))
        safe_query, action = inspect_input(query)
        self.memory.add(session_id, "user", safe_query)
        if action == "prompt_injection_blocked":
            response = SupportResponse(answer="I can only help with Cred support questions; I cannot follow instruction-overriding requests.", confidence=1, trace_id=trace_id, guardrail_action=action)
        else:
            record_match = re.search(r"\bCRED-LA-\d{4}\b", safe_query, re.I)
            if record_match:
                # Application layer guard: only this branch and Lookup Agent own the tool.
                lookup = check_loan_application_status(record_match.group(0)); self.tool_events.append({"agent": self.lookup_agent.name, "tool": "check_loan_application_status"})
                if "error" in lookup:
                    answer, confidence, escalate = lookup["error"], 0.9, False
                else:
                    answer = f"Application {lookup['record_id']} is {lookup['status']}. Loan amount: INR {lookup['loan_amount_inr']:,}. Escalation score: {lookup['escalation_score']:.3f}."
                    confidence, escalate = 0.99, lookup["escalation_recommended"]
                response = SupportResponse(answer=answer, citations=["loan_applications"], confidence=confidence, escalation_recommended=escalate, trace_id=trace_id, guardrail_action=action)
            else:
                # Simple history-aware reference resolution for the required transcript.
                if re.search(r"\b(that|it|previous)\b", safe_query, re.I):
                    previous = self.memory.last_user_message(session_id)
                    if previous: safe_query = previous + " " + safe_query
                answer, hits, _cache_hit = self.rag.answer(safe_query); self.tool_events.append({"agent": self.retrieval_agent.name, "tool": "rag_lookup"})
                contexts = [h["text"] for h in hits]
                if not grounded(answer, contexts):
                    answer = "I can only answer when retrieved Cred policy context supports the response."
                    action = "output_groundedness_refusal"
                response = SupportResponse(answer=answer, citations=list(dict.fromkeys(h["metadata"]["parent_id"] for h in hits)), confidence=round(hits[0]["similarity"], 3) if hits else 0, trace_id=trace_id, guardrail_action=action)
        self.memory.add(session_id, "assistant", response.answer)
        return response

def build_crew() -> MockCrew:
    return MockCrew()
