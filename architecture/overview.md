# Architecture

```text
Client → FastAPI (/ask or WebSocket)
             │
             ├─ input guardrails → masked structured JSONL log
             ├─ budget limiter → MockCrew.kickoff()
             │    ├─ Retrieval Agent → sentence retrieval collection → response cache
             │    ├─ Lookup Agent only → synthetic loan application dataset
             │    └─ Response Composer → SupportResponse (Pydantic)
             ├─ output groundedness check
             └─ two-turn policy review → ReviewVerdict (Pydantic)
```

`src/rag.py` carries two separate collection objects, `cred_fixed_overlap` and
`cred_sentence`. The default implementation uses deterministic local cosine retrieval
for fully offline repeatability. `src/crewai_runtime.py` and
`src/autogen_runtime.py` are opt-in native integrations, kept separate from the
zero-key evidence path.

## Trust boundaries

Untrusted client input is masked and injection-checked before tools, memory, or disk
logging. Lookup is a narrowly scoped capability: only the Lookup Agent is wired to
`check_loan_application_status`. The response is validated by Pydantic, checked
against retrieval context, then independently reviewed.
