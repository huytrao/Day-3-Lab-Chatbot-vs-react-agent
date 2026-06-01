import os
import time
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv


BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_DIR.parent

load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(BACKEND_DIR / ".env", override=True)

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"


def _safe_error_message(exc: Exception) -> str:
    """Return an error message that never exposes API keys."""
    response = getattr(exc, "response", None)
    if response is not None:
        status_code = getattr(response, "status_code", "unknown")
        reason = getattr(response, "reason", "")
        return f"HTTP {status_code} {reason}".strip()
    message = str(exc)
    api_key = get_gemini_api_key()
    if api_key:
        message = message.replace(api_key, "***")
    return message


def get_gemini_api_key() -> str:
    """Return the Gemini API key from server environment variables."""
    return os.getenv("GEMINI_API_KEY", "").strip()


def get_gemini_model_name() -> str:
    """Return the configured Gemini model name."""
    configured = os.getenv("GEMINI_MODEL") or os.getenv("DEFAULT_MODEL") or DEFAULT_GEMINI_MODEL
    configured = configured.strip()
    if configured.startswith("gemini-"):
        return configured
    return DEFAULT_GEMINI_MODEL


def is_gemini_configured() -> bool:
    """Return True when FastAPI has a Gemini key available server-side."""
    return bool(get_gemini_api_key())


def get_gemini_status() -> str:
    """Return a short Gemini availability status without exposing the API key."""
    if not get_gemini_api_key():
        return "Gemini API key is missing; using rule-based answer."
    return f"Gemini API configured with model {get_gemini_model_name()}."


def polish_answer_with_gemini(
    user_message: str,
    draft_answer: str,
    user_profile: dict[str, Any] | None = None,
    chat_history: list[Any] | None = None,
) -> dict[str, Any]:
    """Use Gemini API to rewrite the final VinWonders answer.

    This function never raises. If the API key, network, quota, or model call
    fails, it returns the original draft answer with `used=False`.
    """
    api_key = get_gemini_api_key()
    model = get_gemini_model_name()
    if not api_key:
        return {"text": draft_answer, "used": False, "status": "Gemini API key is missing."}

    history_preview = chat_history[-6:] if chat_history else []
    prompt = (
        "Ban la tro ly tu van du lich VinWonders/Vinpearl than thien. "
        "Hay tra loi bang tieng Viet tu nhien, ngan gon, uu tien gia dinh/tre em khi phu hop. "
        "Khong bia gia ve chinh thuc; neu co gia ve demo thi noi ro la gia demo.\n\n"
        f"Ho so nguoi dung: {user_profile or {}}\n"
        f"Lich su gan day: {history_preview}\n"
        f"Cau hoi hien tai: {user_message}\n"
        f"Ban nhap tu tools: {draft_answer}\n\n"
        "Hay viet cau tra loi cuoi cung cho khach."
    )

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": prompt}],
            }
        ],
        "generationConfig": {
            "temperature": 0.4,
            "maxOutputTokens": 4048,
        },
    }

    last_error = ""
    for attempt in range(1, 4):
        try:
            response = requests.post(
                GEMINI_API_URL.format(model=model),
                params={"key": api_key},
                json=payload,
                timeout=25,
            )
            response.raise_for_status()
            data = response.json()
            parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
            text = "\n".join(part.get("text", "") for part in parts).strip()
            if not text:
                return {"text": draft_answer, "used": False, "status": "Gemini returned an empty response."}
            return {"text": text, "used": True, "status": f"Gemini API used model {model}."}
        except requests.HTTPError as exc:
            status_code = exc.response.status_code if exc.response is not None else 0
            last_error = _safe_error_message(exc)
            if status_code not in {500, 502, 503, 504}:
                break
            time.sleep(0.8 * attempt)
        except Exception as exc:
            last_error = _safe_error_message(exc)
            time.sleep(0.8 * attempt)

    return {"text": draft_answer, "used": False, "status": f"Gemini API failed: {last_error}"}
