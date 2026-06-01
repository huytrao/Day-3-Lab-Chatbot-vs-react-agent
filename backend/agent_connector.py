from typing import Any, Dict


def _run_mock_agent(user_message: str, user_profile: dict, chat_history: list) -> Dict[str, Any]:
    """Return a safe demo response for VinWonders/Vinpearl travel questions."""
    text = user_message.lower()
    preferences = user_profile.get("preferences", [])
    travel_group = user_profile.get("travel_group", "general")
    age_group = user_profile.get("age_group", "general")

    itinerary = [
        {"time": "09:00", "place": "Check-in", "description": "Vao cong som, lay ban do va thong nhat diem hen."},
        {"time": "09:30", "place": "Khu vui choi nhe", "description": "Phu hop gia dinh, tre em va khach muon di chuyen it."},
        {"time": "12:00", "place": "Nha hang gia dinh", "description": "An trua, nghi ngoi va nap nuoc."},
        {"time": "14:00", "place": "Thuy cung / show trong nha", "description": "Phuong an tot khi troi mua hoac nang gat."},
        {"time": "16:00", "place": "Cong vien nuoc", "description": "Ket thuc bang khu nuoc, uu tien khu nhe neu co tre em."},
    ]

    agent_trace = [
        {"type": "thought", "content": "Classify user request within VinWonders/Vinpearl travel demo scope."},
        {"type": "action", "tool": "demo_vinwonders_planner", "parameters": {"query": user_message}},
        {"type": "observation", "content": "Use demo knowledge for rides, weather fallback, ticket estimate, food, and 1-day itinerary."},
    ]

    if any(keyword in text for keyword in ["gia", "ve", "ticket", "price"]):
        reply = (
            "Gia ve demo: nguoi lon khoang 250000 VND, tre em khoang 150000 VND. "
            "Day chi la du lieu demo de lap ke hoach, khong phai gia chinh thuc hay booking that."
        )
    elif any(keyword in text for keyword in ["mua", "nang", "weather", "thoi tiet"]):
        reply = (
            "Neu troi mua, hay uu tien thuy cung, show trong nha, nha hang va khu co mai che. "
            "Neu troi nang, nen vao cong som, nghi trua lau hon va de cong vien nuoc vao cuoi chieu."
        )
    elif any(keyword in text for keyword in ["be", "tre", "children", "kid", "family"]):
        reply = (
            "Voi tre em, nen uu tien ho boi tre em, khu vui choi nhe, thuy cung, show trong nha "
            f"va nghi giua chang. Profile hien tai: nhom {travel_group}, do tuoi {age_group}."
        )
    else:
        reply = (
            "Minh goi y lich trinh VinWonders 1 ngay: check-in som, choi khu phu hop so thich "
            f"{preferences or ['family friendly']}, nghi trua tai nha hang, vao khu trong nha khi nang/mua, "
            "va ket thuc bang cong vien nuoc cuoi chieu."
        )

    return {"reply": reply, "agent_trace": agent_trace, "itinerary": itinerary}


def run_vinwonders_agent(
    user_message: str,
    user_profile: dict | None = None,
    chat_history: list | None = None,
) -> Dict[str, Any]:
    """Run LangGraph pipeline first and fall back to a safe mock response."""
    safe_profile = user_profile or {}
    safe_history = chat_history or []

    try:
        try:
            from .graph.graph import run_langgraph_agent
        except ImportError:
            from graph.graph import run_langgraph_agent

        result = run_langgraph_agent(user_message, safe_profile, safe_history)
        if result.get("reply"):
            return result
    except Exception as exc:
        fallback = _run_mock_agent(user_message, safe_profile, safe_history)
        fallback["agent_trace"] = [
            {
                "type": "thought",
                "content": f"LangGraph pipeline loi hoac chua san sang, dung fallback. Error: {str(exc)}",
            },
            *fallback.get("agent_trace", []),
        ]
        return fallback

    return _run_mock_agent(user_message, safe_profile, safe_history)
