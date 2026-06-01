def create_itinerary(
    travel_group: str = "family",
    duration: str = "1_day",
    preferences: list | None = None,
    weather_note: str = "",
) -> str:
    """Create a demo one-day VinWonders itinerary.

    Args:
        travel_group: Visitor group such as "family", "couple", or "friends".
        duration: Trip duration. The current demo mainly supports "1_day".
        preferences: Optional list of interests such as "water_park",
            "kids_friendly", or "less_walking".
        weather_note: Optional weather advice to adapt the plan.

    Returns:
        Vietnamese text itinerary for rendering in chat. The function is fully
        rule-based and never raises exceptions to callers.
    """
    safe_preferences = preferences or []
    indoor_bias = "mua" in weather_note.lower() or "nang" in weather_note.lower()
    morning = "Cong vien nuoc" if "water_park" in safe_preferences else "Khu vui choi gia dinh"
    midday = "Khu vui choi trong nha" if indoor_bias else "Ho boi tre em"

    return (
        "09:00 Check-in -> "
        f"09:30 {morning} -> "
        "11:00 Ho boi tre em -> "
        "12:00 An trua va nghi chan -> "
        f"14:00 {midday} -> "
        "16:00 Show bieu dien -> "
        "17:00 Ket thuc. "
        f"Lich trinh phu hop nhom {travel_group}, thoi luong {duration}."
    )
