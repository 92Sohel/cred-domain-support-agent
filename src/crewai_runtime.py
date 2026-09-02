"""Optional native CrewAI runtime.

This module is intentionally isolated: `MOCK_LLM=true` needs neither an API key nor
network. When CrewAI is installed, `MockCrewAILLM` is the documented BaseLLM extension
point rather than an external interception shim.
"""
from __future__ import annotations
import json
from typing import Any

try:
    from crewai import Agent, Crew, Task
    from crewai.llms.base_llm import BaseLLM
    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False
    BaseLLM = object  # type: ignore[misc,assignment]

if CREWAI_AVAILABLE:
    class MockCrewAILLM(BaseLLM):
        """Deterministic CrewAI LLM that only returns generated response text.

        Important: callers parse this return value, never scan system-prompt history
        for `Observation:`; the built-in ReAct template itself contains that example.
        Tool dispatch must inspect a tool's declared argument schema, not its name.
        """
        def __init__(self) -> None: super().__init__(model="cred/mock", temperature=0)
        def call(self, messages: Any, tools: Any | None = None, callbacks: Any | None = None, available_functions: Any | None = None) -> str:
            generated = "Final Answer: I can only answer from the supplied tool context."
            return generated
        def supports_function_calling(self) -> bool: return False

    def create_native_crew(rag_tool: Any, lookup_tool: Any) -> Crew:
        llm = MockCrewAILLM()
        retrieval = Agent(role="Retrieval Agent", goal="Retrieve grounded policy context", backstory="Policy retrieval specialist", tools=[rag_tool], llm=llm)
        lookup = Agent(role="Lookup Agent", goal="Check one application safely", backstory="Operations lookup specialist", tools=[lookup_tool], llm=llm)
        composer = Agent(role="Response Composer", goal="Compose a supported response", backstory="Support response specialist", tools=[], llm=llm)
        # Least autonomy: `lookup_tool` appears only in Lookup Agent's tools list.
        return Crew(agents=[retrieval, lookup, composer], tasks=[Task(description="Use tools as needed and produce a support draft.", expected_output="Grounded support response", agent=composer)], verbose=False)
else:
    class MockCrewAILLM:  # import-safe explanatory placeholder
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            raise RuntimeError("Install crewai to use the native runtime; default MOCK_LLM does not require it.")
