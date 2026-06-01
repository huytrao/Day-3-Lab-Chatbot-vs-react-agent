import os
from datetime import datetime
from typing import Any

import requests


def _mock_weather(location: str, date: str) -> str:
    return (
        f"Thoi tiet tai {location} {date}: nang nong khoang 35°C. "
        "Khuyen nghi uu tien cong vien nuoc buoi sang, nghi trong nha tu 11:00 den 15:00."
    )


def get_weather(location: str, date: str = "today") -> str:
    """Get weather advice for a VinWonders/Vinpearl travel plan.

    Args:
        location: Destination or city name, for example "Ha Noi", "Nha Trang",
            "Phu Quoc", or "VinWonders".
        date: Requested date. This demo accepts free-form values such as
            "today", "tomorrow", or "2026-06-01".

    Returns:
        Vietnamese text containing weather information and travel advice. The
        function never raises exceptions to callers. If `OPENWEATHER_API_KEY`
        is missing or the HTTP request fails, it returns mock weather guidance.
    """
    safe_location = (location or "VinWonders").strip() or "VinWonders"
    safe_date = (date or "today").strip() or "today"
    api_key = os.getenv("OPENWEATHER_API_KEY")

    if not api_key:
        return _mock_weather(safe_location, "hom nay" if safe_date == "today" else safe_date)

    try:
        response = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={
                "q": safe_location,
                "appid": api_key,
                "units": "metric",
                "lang": "vi",
            },
            timeout=5,
        )
        response.raise_for_status()
        payload: dict[str, Any] = response.json()
        weather = payload.get("weather", [{}])[0].get("description", "khong ro")
        temperature = payload.get("main", {}).get("temp", "khong ro")
        today = datetime.now().strftime("%Y-%m-%d")
        return (
            f"Thoi tiet tai {safe_location} ngay {safe_date if safe_date != 'today' else today}: "
            f"{weather}, khoang {temperature}°C. Neu nang nong, nen choi ngoai troi som, "
            "nghi trong nha buoi trua va uu tien cong vien nuoc cuoi chieu."
        )
    except Exception:
        return _mock_weather(safe_location, "hom nay" if safe_date == "today" else safe_date)
