import re
import unicodedata
from typing import Any

try:
    from langgraph.graph import END, START, StateGraph
except Exception:
    END = "__end__"
    START = "__start__"
    StateGraph = None

try:
    from .state import AgentState
except ImportError:
    from state import AgentState

try:
    from ..tools import calculate_price, create_itinerary, get_weather, search_vin_knowledge
except ImportError:
    from tools import calculate_price, create_itinerary, get_weather, search_vin_knowledge

try:
    from ..agent.gemini_model import get_gemini_status, polish_answer_with_gemini
except ImportError:
    from agent.gemini_model import get_gemini_status, polish_answer_with_gemini


MODEL_PROVIDER = "gemini"


def _normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFD", text or "")
    without_accents = "".join(char for char in normalized if unicodedata.category(char) != "Mn")
    return without_accents.lower()


def _model_status() -> str:
    """Return model availability without making the graph depend on it."""
    return get_gemini_status()


def _append_trace(state: AgentState, item: dict[str, Any]) -> list[dict[str, Any]]:
    return [*state.get("agent_trace", []), item]


def _append_tool_result(state: AgentState, result: str) -> list[str]:
    return [*state.get("tool_results", []), result]


def receive_input_node(state: AgentState) -> AgentState:
    """Receive user message and context, then append a thought trace."""
    return {
        **state,
        "user_profile": state.get("user_profile") or {},
        "chat_history": state.get("chat_history") or [],
        "tool_results": state.get("tool_results") or [],
        "agent_trace": _append_trace(
            state,
            {"type": "thought", "content": "Da nhan cau hoi va context nguoi dung."},
        ),
        "itinerary": state.get("itinerary") or [],
    }


def classify_intent_node(state: AgentState) -> AgentState:
    """Classify user intent with simple deterministic rules."""
    text = _normalize_text(state.get("user_message", ""))
    if any(keyword in text for keyword in ["thoi tiet", "mua", "nang", "weather"]):
        intent = "weather"
    elif any(keyword in text for keyword in ["lich trinh", "map", "1 ngay", "di dau truoc", "itinerary"]):
        intent = "itinerary"
    elif (
        "bao nhieu tien" in text
        or "ticket" in text
        or "price" in text
        or "gia ve" in text
        or re.search(r"\bve\b", text)
    ):
        intent = "price"
    elif any(keyword in text for keyword in ["be", "tre em", "5 tuoi", "choi gi", "tro gi", "kid", "children"]):
        intent = "knowledge"
    else:
        intent = "general"

    return {
        **state,
        "intent": intent,
        "agent_trace": _append_trace(
            state,
            {"type": "thought", "content": f"Phan loai intent: {intent}. {_model_status()}"},
        ),
    }


def _route_by_intent(state: AgentState) -> str:
    intent = state.get("intent", "general")
    if intent in {"weather", "price", "knowledge", "itinerary"}:
        return intent
    return "general"


def weather_tool_node(state: AgentState) -> AgentState:
    profile = state.get("user_profile") or {}
    location = str(profile.get("location") or profile.get("destination") or "VinWonders")
    date = str(profile.get("date") or "today")
    result = get_weather(location=location, date=date)
    return {
        **state,
        "tool_results": _append_tool_result(state, result),
        "agent_trace": [
            *state.get("agent_trace", []),
            {"type": "action", "tool": "get_weather", "parameters": {"location": location, "date": date}},
            {"type": "observation", "content": result},
        ],
    }


def knowledge_tool_node(state: AgentState) -> AgentState:
    query = state.get("user_message", "")
    result = search_vin_knowledge(query=query)
    return {
        **state,
        "tool_results": _append_tool_result(state, result),
        "agent_trace": [
            *state.get("agent_trace", []),
            {"type": "action", "tool": "search_vin_knowledge", "parameters": {"query": query}},
            {"type": "observation", "content": result},
        ],
    }


def _parse_guest_counts(text: str) -> tuple[int, int]:
    normalized = _normalize_text(text)
    adult_match = re.search(r"(\d+)\s*(nguoi lon|adult)", normalized)
    child_match = re.search(r"(\d+)\s*(tre em|be|child|children)", normalized)
    adults = int(adult_match.group(1)) if adult_match else 1
    children = int(child_match.group(1)) if child_match else 2
    return adults, children


def price_tool_node(state: AgentState) -> AgentState:
    adults, children = _parse_guest_counts(state.get("user_message", ""))
    result = calculate_price(adults=adults, children=children)
    return {
        **state,
        "tool_results": _append_tool_result(state, result),
        "agent_trace": [
            *state.get("agent_trace", []),
            {"type": "action", "tool": "calculate_price", "parameters": {"adults": adults, "children": children}},
            {"type": "observation", "content": result},
        ],
    }


def itinerary_tool_node(state: AgentState) -> AgentState:
    profile = state.get("user_profile") or {}
    preferences = profile.get("preferences") or []
    if not isinstance(preferences, list):
        preferences = [str(preferences)]
    weather_note = " ".join(state.get("tool_results", []))
    result = create_itinerary(
        travel_group=str(profile.get("travel_group") or "family"),
        duration=str(profile.get("duration") or "1_day"),
        preferences=preferences,
        weather_note=weather_note,
    )
    itinerary = [
        {"time": "09:00", "place": "Check-in", "description": "Vao cong va chuan bi lich trinh."},
        {"time": "09:30", "place": "Cong vien nuoc", "description": "Uu tien buoi sang neu thoi tiet nong."},
        {"time": "11:00", "place": "Ho boi tre em", "description": "Phu hop gia dinh co tre nho."},
        {"time": "12:00", "place": "An trua", "description": "Nghi chan va nap nang luong."},
        {"time": "14:00", "place": "Khu vui choi trong nha", "description": "Phuong an an toan khi mua/nang."},
        {"time": "16:00", "place": "Show bieu dien", "description": "Ket thuc nhe nhang."},
    ]
    return {
        **state,
        "tool_results": _append_tool_result(state, result),
        "itinerary": itinerary,
        "agent_trace": [
            *state.get("agent_trace", []),
            {
                "type": "action",
                "tool": "create_itinerary",
                "parameters": {
                    "travel_group": profile.get("travel_group", "family"),
                    "duration": profile.get("duration", "1_day"),
                    "preferences": preferences,
                    "weather_note": weather_note,
                },
            },
            {"type": "observation", "content": result},
        ],
    }


def synthesize_answer_node(state: AgentState) -> AgentState:
    """Synthesize final Vietnamese answer from tool outputs."""
    tool_results = state.get("tool_results", [])
    if tool_results:
        final_answer = " ".join(tool_results)
    else:
        final_answer = (
            "Em da nhan yeu cau cua quy khach. Voi khach du lich di VinWonders, "
            "em goi y bat dau bang khu vui choi phu hop gia dinh, kiem tra thoi tiet, "
            "sau do tao lich trinh 1 ngay."
        )

    if state.get("intent") in {"knowledge", "general"}:
        final_answer += " Neu di cung gia dinh co tre nho, hay uu tien khu vui choi nhe, ho boi tre em va diem nghi chan."

    gemini_result = polish_answer_with_gemini(
        user_message=state.get("user_message", ""),
        draft_answer=final_answer,
        user_profile=state.get("user_profile") or {},
        chat_history=state.get("chat_history") or [],
    )
    polished_answer = gemini_result.get("text") or final_answer
    used_model = bool(gemini_result.get("used"))
    model_status = str(gemini_result.get("status") or _model_status())

    itinerary = state.get("itinerary") or [
        {"time": "09:00", "place": "Check-in", "description": "Vao cong va thong nhat diem hen."},
        {"time": "09:30", "place": "Cong vien nuoc / khu vui choi nhe", "description": "Uu tien hoat dong phu hop gia dinh."},
        {"time": "12:00", "place": "An trua", "description": "Nghi chan, nap nuoc va tranh nang."},
        {"time": "14:00", "place": "Khu vui choi trong nha", "description": "Phuong an tot khi mua hoac nang gat."},
        {"time": "16:00", "place": "Show bieu dien", "description": "Ket thuc lich trinh nhe nhang."},
    ]

    return {
        **state,
        "final_answer": polished_answer,
        "itinerary": itinerary,
        "agent_trace": [
            *_append_trace(
                state,
                {"type": "thought", "content": "Da tong hop ket qua tool thanh cau tra loi cuoi."},
            ),
            {
                "type": "observation",
                "content": model_status if used_model else f"Gemini skipped. {model_status}",
            },
        ],
    }


def _build_graph():
    if StateGraph is None:
        return None

    graph = StateGraph(AgentState)
    graph.add_node("receive_input_node", receive_input_node)
    graph.add_node("classify_intent_node", classify_intent_node)
    graph.add_node("weather_tool_node", weather_tool_node)
    graph.add_node("knowledge_tool_node", knowledge_tool_node)
    graph.add_node("price_tool_node", price_tool_node)
    graph.add_node("itinerary_tool_node", itinerary_tool_node)
    graph.add_node("synthesize_answer_node", synthesize_answer_node)

    graph.add_edge(START, "receive_input_node")
    graph.add_edge("receive_input_node", "classify_intent_node")
    graph.add_conditional_edges(
        "classify_intent_node",
        _route_by_intent,
        {
            "weather": "weather_tool_node",
            "price": "price_tool_node",
            "knowledge": "knowledge_tool_node",
            "itinerary": "itinerary_tool_node",
            "general": "knowledge_tool_node",
        },
    )
    graph.add_edge("weather_tool_node", "synthesize_answer_node")
    graph.add_edge("price_tool_node", "synthesize_answer_node")
    graph.add_edge("knowledge_tool_node", "synthesize_answer_node")
    graph.add_edge("itinerary_tool_node", "synthesize_answer_node")
    graph.add_edge("synthesize_answer_node", END)
    return graph.compile()


def _run_fallback_graph(initial_state: AgentState) -> AgentState:
    state = receive_input_node(initial_state)
    state = classify_intent_node(state)
    route = _route_by_intent(state)
    if route == "weather":
        state = weather_tool_node(state)
    elif route == "price":
        state = price_tool_node(state)
    elif route == "itinerary":
        state = itinerary_tool_node(state)
    else:
        state = knowledge_tool_node(state)
    return synthesize_answer_node(state)


def run_langgraph_agent(
    user_message: str,
    user_profile: dict | None = None,
    chat_history: list | None = None,
) -> dict:
    """Run the VinWonders LangGraph pipeline."""
    initial_state: AgentState = {
        "user_message": user_message,
        "user_profile": user_profile or {},
        "chat_history": chat_history or [],
        "intent": "",
        "tool_results": [],
        "final_answer": "",
        "agent_trace": [],
        "itinerary": [],
    }

    try:
        compiled_graph = _build_graph()
        final_state = compiled_graph.invoke(initial_state) if compiled_graph else _run_fallback_graph(initial_state)
    except Exception:
        final_state = _run_fallback_graph(initial_state)

    return {
        "reply": final_state.get("final_answer") or final_state.get("reply") or "",
        "agent_trace": final_state.get("agent_trace", []),
        "itinerary": final_state.get("itinerary", []),
    }
