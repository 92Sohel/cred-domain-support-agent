"""Deterministic synthetic loan-application dataset for the Cred capstone."""
from __future__ import annotations

from collections import Counter
from random import Random

SEED = 20260902
CATEGORY_WEIGHTS = {
    "Personal Loan": 0.28,
    "Home Loan": 0.18,
    "Auto Loan": 0.18,
    "Education Loan": 0.18,
    "Business Loan": 0.18,
}
STATUS_WEIGHTS = {
    "Submitted": 0.18,
    "Under Review": 0.22,
    "Approved": 0.24,
    "Rejected": 0.14,
    "Disbursed": 0.22,
}
AMOUNT_RANGE_INR = (50_000, 5_000_000)


def _weighted_choice(rng: Random, weights: dict[str, float]) -> str:
    labels, values = list(weights), list(weights.values())
    return rng.choices(labels, weights=values, k=1)[0]


def generate_loan_applications(count: int = 50, seed: int = SEED) -> list[dict]:
    """Generate reproducible records; first rows guarantee required coverage."""
    if count < 40:
        raise ValueError("The capstone dataset must contain at least 40 records.")
    rng = Random(seed)
    categories = list(CATEGORY_WEIGHTS)
    statuses = list(STATUS_WEIGHTS)
    records: list[dict] = []
    # Guarantees all five categories occur at least three times, without hand editing
    # random outcomes; remaining values are seeded weighted draws.
    category_stream = categories * 3 + [_weighted_choice(rng, CATEGORY_WEIGHTS) for _ in range(count - 15)]
    status_stream = statuses + [_weighted_choice(rng, STATUS_WEIGHTS) for _ in range(count - 5)]
    rng.shuffle(category_stream)
    rng.shuffle(status_stream)
    for index in range(count):
        records.append({
            "record_id": f"CRED-LA-{index + 1:04d}",
            "category": category_stream[index],
            "status": status_stream[index],
            "loan_amount_inr": rng.randrange(AMOUNT_RANGE_INR[0], AMOUNT_RANGE_INR[1] + 1, 5_000),
            "days_since_created": rng.randint(0, 30),
            "flagged_for_fraud_review": rng.random() < 0.20,
        })
    validate_dataset(records)
    return records


def validate_dataset(records: list[dict]) -> None:
    if len(records) < 40:
        raise ValueError("Expected at least 40 records")
    category_counts = Counter(row["category"] for row in records)
    status_counts = Counter(row["status"] for row in records)
    if any(category_counts[name] < 3 for name in CATEGORY_WEIGHTS):
        raise ValueError("Every required category needs at least three records")
    if any(status_counts[name] < 1 for name in STATUS_WEIGHTS):
        raise ValueError("Every required status must occur at least once")
    fraud_pct = 100 * sum(row["flagged_for_fraud_review"] for row in records) / len(records)
    if not 10 <= fraud_pct <= 30:
        raise ValueError(f"Fraud-review percentage {fraud_pct:.1f}% outside 10–30% band")
    for row in records:
        if not 0 <= row["days_since_created"] <= 30:
            raise ValueError("days_since_created must be 0–30")


LOAN_APPLICATIONS = generate_loan_applications()


def dataset_report(records: list[dict] = LOAN_APPLICATIONS) -> dict:
    return {
        "total": len(records),
        "category_counts": dict(Counter(row["category"] for row in records)),
        "status_counts": dict(Counter(row["status"] for row in records)),
        "fraud_review_percentage": round(100 * sum(row["flagged_for_fraud_review"] for row in records) / len(records), 2),
    }


if __name__ == "__main__":
    import json
    print(json.dumps(dataset_report(), indent=2))
