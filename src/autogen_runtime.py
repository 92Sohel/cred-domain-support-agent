"""Optional native AutoGen review stage with the required structured-message registration."""
from __future__ import annotations
from .schemas import ReviewVerdict
try:
    from autogen_agentchat.agents import AssistantAgent
    from autogen_agentchat.base import TaskResult
    from autogen_agentchat.messages import StructuredMessage
    from autogen_agentchat.teams import RoundRobinGroupChat
    AUTOGEN_AVAILABLE = True
except ImportError:
    AUTOGEN_AVAILABLE = False

def create_round_robin_review_team(model_client):
    if not AUTOGEN_AVAILABLE:
        raise RuntimeError("Install autogen-agentchat to use the native review team.")
    policy = AssistantAgent("Policy-Compliance-Reviewer", model_client=model_client, system_message="Check whether every claim is supported by the supplied context.")
    editor = AssistantAgent("Final-Editor", model_client=model_client, system_message="Approve or correct the draft.", output_content_type=ReviewVerdict)
    return RoundRobinGroupChat([policy, editor], max_turns=2, custom_message_types=[StructuredMessage[ReviewVerdict]])
