"""Input and output safety controls; no raw fixed-format PII reaches logging or tools."""
from __future__ import annotations
import re

PAN = re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b", re.I)
AADHAAR = re.compile(r"\b\d{4}[ -]?\d{4}[ -]?\d{4}\b")
BANK_ACCOUNT = re.compile(r"\b\d{9,18}\b")
INJECTION_TERMS = re.compile(r"ignore (all |previous |your )?instructions|system prompt|jailbreak|reveal .*prompt", re.I)

def mask_pii(text: str) -> str:
    text = PAN.sub("[MASKED_PAN]", text)
    text = AADHAAR.sub("[MASKED_AADHAAR]", text)
    return BANK_ACCOUNT.sub("[MASKED_BANK_ACCOUNT]", text)

def inspect_input(text: str) -> tuple[str, str | None]:
    masked = mask_pii(text)
    if INJECTION_TERMS.search(masked):
        return masked, "prompt_injection_blocked"
    return masked, "pii_masked" if masked != text else None

def grounded(answer: str, contexts: list[str]) -> bool:
    """Reject factual responses with no retrieval support; refusal text is always safe."""
    if answer.startswith("I don't know") or answer.startswith("I can only"):
        return True
    haystack = " ".join(contexts).lower()
    tokens = [t.lower() for t in re.findall(r"[a-z]{5,}", answer)]
    return bool(tokens) and sum(t in haystack for t in tokens) / len(tokens) >= 0.45
