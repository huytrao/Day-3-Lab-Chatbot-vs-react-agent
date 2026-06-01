from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    user_message: str
    user_profile: dict[str, Any]
    chat_history: list[dict[str, Any]]
    intent: str
    tool_results: list[str]
    final_answer: str
    agent_trace: list[dict[str, Any]]
    itinerary: list[dict[str, str]]
