"""Autogen-compatible two-turn review model, defaulting to local deterministic review."""
from __future__ import annotations
from .schemas import ReviewVerdict

def review_draft(draft: str, retrieved_context: list[str]) -> ReviewVerdict:
    """Policy reviewer then final editor; mirrors RoundRobinGroupChat(max_turns=2)."""
    context = " ".join(retrieved_context).lower()
    unsupported = [word for word in ("guaranteed", "always", "zero fee", "instant approval") if word in draft.lower() and word not in context]
    if unsupported:
        revised = "I can only provide information supported by the retrieved Cred policy context."
        return ReviewVerdict(approved=False, final_answer=revised, reason=f"Removed unsupported claim(s): {', '.join(unsupported)}.")
    return ReviewVerdict(approved=True, final_answer=draft, reason="Policy reviewer found the draft supported by retrieved context.")

# Optional real integration blueprint (requires autogen-agentchat):
# policy_reviewer = AssistantAgent("Policy-Compliance-Reviewer", model_client=client)
# final_editor = AssistantAgent("Final-Editor", model_client=client, output_content_type=ReviewVerdict)
# team = RoundRobinGroupChat([policy_reviewer, final_editor], max_turns=2,
#     custom_message_types=[StructuredMessage[ReviewVerdict]])
