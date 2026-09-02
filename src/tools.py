from __future__ import annotations
from dataset import LOAN_APPLICATIONS

def check_loan_application_status(record_id: str) -> dict:
    """Only the Lookup Agent is granted access to this tool.

    score = 0.65*fraud_flag + 0.35*(days_since_created/30). Escalate at >= 0.70.
    """
    record = next((row for row in LOAN_APPLICATIONS if row["record_id"] == record_id.upper()), None)
    if not record: return {"error": "Application record was not found."}
    score = 0.65 * int(record["flagged_for_fraud_review"]) + 0.35 * (record["days_since_created"] / 30)
    return {key: record[key] for key in ("record_id", "status", "loan_amount_inr") } | {"escalation_score": round(score, 3), "escalation_recommended": score >= 0.70}
