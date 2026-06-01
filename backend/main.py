from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response

try:
    from . import crud
    from .agent_connector import run_vinwonders_agent
    from .agent.gemini_model import get_gemini_model_name, get_gemini_status, is_gemini_configured
    from .database import close_database, ping_database
    from .schemas import (
        ChatRequest,
        ChatResponse,
        HistoryResponse,
        InitUserRequest,
        InitUserResponse,
        MessageResponse,
    )
except ImportError:
    import crud
    from agent_connector import run_vinwonders_agent
    from agent.gemini_model import get_gemini_model_name, get_gemini_status, is_gemini_configured
    from database import close_database, ping_database
    from schemas import (
        ChatRequest,
        ChatResponse,
        HistoryResponse,
        InitUserRequest,
        InitUserResponse,
        MessageResponse,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.ai_provider = "gemini"
    app.state.ai_model = get_gemini_model_name()
    app.state.ai_configured = is_gemini_configured()
    await ping_database()
    yield
    close_database()


app = FastAPI(
    title="VinWonders Travel AI Agent Backend",
    description="FastAPI + MongoDB API orchestrator for the VinWonders travel demo.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def serve_demo() -> FileResponse:
    demo_path = Path(__file__).resolve().parent.parent / "demo.html"
    if not demo_path.exists():
        raise HTTPException(status_code=404, detail="demo.html not found")
    return FileResponse(demo_path)


@app.get("/favicon.ico", include_in_schema=False)
async def favicon() -> Response:
    return Response(status_code=204)


@app.get("/health")
@app.get("/api/health")
async def health_check() -> dict:
    return {
        "status": 200,
        "message": "Backend is running",
        "ai_provider": "gemini",
        "ai_model": get_gemini_model_name(),
        "ai_configured": is_gemini_configured(),
        "ai_status": get_gemini_status(),
    }


def default_user_profile(user_id: str) -> dict:
    return {
        "user_id": user_id,
        "travel_group": "general",
        "age_group": "general",
        "budget": "medium",
        "preferences": [],
        "duration": "1_day",
        "priority": "general_advice",
    }


def profile_from_chat_payload(payload: ChatRequest, user_id: str) -> dict:
    extras = getattr(payload, "__pydantic_extra__", {}) or {}
    participants = extras.get("participants")
    has_children = str(extras.get("has_children", "")).lower()
    interests = extras.get("interests") or extras.get("preferences") or []
    if isinstance(interests, str):
        interests = [item.strip() for item in interests.split(",") if item.strip()]

    children = 1 if has_children in {"co", "có", "yes", "true", "1"} else 0
    try:
        adults = max(1, int(participants or 1) - children)
    except Exception:
        adults = 1

    return {
        "user_id": user_id,
        "travel_group": "family" if children else "general",
        "age_group": "children" if children else "general",
        "budget": extras.get("budget", "medium"),
        "preferences": interests,
        "duration": "1_day",
        "priority": "general_advice",
        "adults": adults,
        "children": children,
        "location": extras.get("location", "VinWonders"),
    }


async def create_guest_user(payload: ChatRequest | None = None) -> str:
    extras = getattr(payload, "__pydantic_extra__", {}) if payload else {}
    name = extras.get("user_name") or extras.get("name") or "Guest User"
    return await crud.create_user(name=name)


@app.post("/api/init_user", response_model=InitUserResponse)
async def init_user(payload: InitUserRequest) -> InitUserResponse:
    user_id = await crud.create_user(name=payload.name, email=payload.email)
    await crud.create_user_profile(user_id=user_id, profile=payload.model_dump())
    session_id = await crud.create_chat_session(user_id=user_id)

    return InitUserResponse(
        status=200,
        user_id=user_id,
        session_id=session_id,
        message="User initialized successfully",
    )


@app.get("/api/history/{session_id}", response_model=HistoryResponse)
async def get_history(session_id: str) -> HistoryResponse:
    if not session_id.strip():
        raise HTTPException(status_code=400, detail="session_id is required")

    session = await crud.get_chat_session(session_id=session_id)
    if not session:
        return HistoryResponse(status=200, session_id=session_id, messages=[])

    history = await crud.get_chat_history(session_id=session_id)
    messages = [
        MessageResponse(role=item["role"], content=item["content"])
        for item in history
        if item.get("role") in {"user", "assistant"}
    ]
    return HistoryResponse(status=200, session_id=session_id, messages=messages)


@app.post("/api/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest) -> ChatResponse:
    user_message = payload.get_user_message()
    if not user_message:
        raise HTTPException(
            status_code=400,
            detail="Missing message. Please send one of: text, message, content.",
        )

    user_id = payload.user_id
    if user_id:
        user = await crud.get_user_by_id(user_id)
        if not user:
            user_id = await create_guest_user(payload)
    else:
        user_id = await create_guest_user(payload)

    session_id = payload.session_id
    if session_id:
        session = await crud.get_chat_session(session_id=session_id, user_id=user_id)
        if not session:
            session_id = await crud.create_chat_session(user_id=user_id)
    else:
        session_id = await crud.create_chat_session(user_id=user_id)

    user_profile = await crud.get_user_profile(user_id=user_id) or profile_from_chat_payload(payload, user_id)
    if not user_profile:
        user_profile = default_user_profile(user_id)

    await crud.add_message(
        session_id=session_id,
        user_id=user_id,
        role="user",
        content=user_message,
    )

    chat_history = await crud.get_chat_history(session_id=session_id)

    try:
        agent_result = run_vinwonders_agent(
            user_message=user_message,
            user_profile=user_profile,
            chat_history=chat_history,
        )
        response_type = agent_result.get("type", "text")
    except Exception:
        agent_result = {
            "reply": (
                "Hiện tại AI Agent gặp lỗi tạm thời. Bạn có thể thử lại hoặc dùng lịch trình mặc định: "
                "sáng công viên nước, trưa ăn uống nghỉ ngơi, chiều khu vui chơi trong nhà."
            ),
            "agent_trace": [],
            "itinerary": [],
        }
        response_type = "fallback"

    reply = agent_result.get("reply")
    if not reply:
        reply = (
            "Hiện tại AI Agent gặp lỗi tạm thời. Bạn có thể thử lại hoặc dùng lịch trình mặc định: "
            "sáng công viên nước, trưa ăn uống nghỉ ngơi, chiều khu vui chơi trong nhà."
        )
        agent_result = {"agent_trace": [], "itinerary": []}
        response_type = "fallback"

    await crud.add_message(
        session_id=session_id,
        user_id=user_id,
        role="assistant",
        content=reply,
    )

    return ChatResponse(
        status=200,
        reply=reply,
        type=response_type,
        user_id=user_id,
        session_id=session_id,
        agent_trace=agent_result.get("agent_trace", []),
        itinerary=agent_result.get("itinerary", []),
    )
