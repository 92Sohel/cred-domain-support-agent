from __future__ import annotations
import json, time
from pathlib import Path
from .guardrails import mask_pii

LOG_PATH = Path(__file__).resolve().parents[1] / "logs" / "requests.jsonl"
def log_request(trace_id: str, raw_query: str, elapsed_ms: float, status: str) -> None:
    LOG_PATH.parent.mkdir(exist_ok=True)
    event = {"trace_id": trace_id, "query": mask_pii(raw_query), "elapsed_ms": round(elapsed_ms, 2), "status": status, "timestamp": time.time()}
    with LOG_PATH.open("a", encoding="utf-8") as file: file.write(json.dumps(event) + "\n")
