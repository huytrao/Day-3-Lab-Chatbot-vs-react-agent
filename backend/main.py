from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

try:
    from . import crud
    from .agent_connector import run_vinwonders_agent
    from .database import close_database, ping_database
    from .schemas import ChatRequest, ChatResponse, HistoryResponse, InitUserRequest, InitUserResponse, MessageResponse
except ImportError:
    import crud
    from agent_connector import run_vinwonders_agent
    from database import close_database, ping_database
    from schemas import ChatRequest, ChatResponse, HistoryResponse, InitUserRequest, InitUserResponse, MessageResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    await ping_database()
    yield
    close_database()


app = FastAPI(title="VinWonders Travel AI Agent Backend", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
@app.get("/api/health")
async def health_check() -> dict:
    return {"status": 200, "message": "Backend is running"}


def default_user_profile(user_id: str) -> dict:
    return {"user_id": user_id, "travel_group": "general", "age_group": "general", "budget": "medium", "preferences": [], "duration": "1_day", "priority": "general_advice"}


async def create_guest_user() -> str:
    return await crud.create_user(name="Guest User")


@app.post("/api/init_user", response_model=InitUserResponse)
async def init_user(payload: InitUserRequest) -> InitUserResponse:
    user_id = await crud.create_user(name=payload.name, email=payload.email)
    await crud.create_user_profile(user_id=user_id, profile=payload.model_dump())
    session_id = await crud.create_chat_session(user_id=user_id)
    return InitUserResponse(user_id=user_id, session_id=session_id, message="User initialized successfully")


@app.get("/api/history/{session_id}", response_model=HistoryResponse)
async def get_history(session_id: str) -> HistoryResponse:
    if not session_id.strip():
        raise HTTPException(status_code=400, detail="session_id is required")
    session = await crud.get_chat_session(session_id=session_id)
    if not session:
        return HistoryResponse(session_id=session_id, messages=[])
    history = await crud.get_chat_history(session_id=session_id)
    messages = [MessageResponse(role=item["role"], content=item["content"]) for item in history if item.get("role") in {"user", "assistant"}]
    return HistoryResponse(session_id=session_id, messages=messages)


@app.post("/api/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest) -> ChatResponse:
    user_message = payload.get_user_message()
    if not user_message:
        raise HTTPException(status_code=400, detail="Missing message. Please send one of: text, message, content.")

    user_id = payload.user_id
    if user_id:
        user = await crud.get_user_by_id(user_id)
        if not user:
            user_id = await create_guest_user()
    else:
        user_id = await create_guest_user()

    session_id = payload.session_id
    if session_id:
        session = await crud.get_chat_session(session_id=session_id, user_id=user_id)
        if not session:
            session_id = await crud.create_chat_session(user_id=user_id)
    else:
        session_id = await crud.create_chat_session(user_id=user_id)

    user_profile = await crud.get_user_profile(user_id=user_id) or default_user_profile(user_id)
    await crud.add_message(session_id=session_id, user_id=user_id, role="user", content=user_message)
    chat_history = await crud.get_chat_history(session_id=session_id)

    try:
        agent_result = run_vinwonders_agent(user_message=user_message, user_profile=user_profile, chat_history=chat_history)
        reply = agent_result.get("reply") or ""
        if not reply:
            raise ValueError("agent returned empty reply")
        response_type = "text"
    except Exception:
        reply = "Hien tai AI Agent gap loi tam thoi. Ban co the thu lai hoac dung lich trinh mac dinh: sang cong vien nuoc, trua an uong nghi ngoi, chieu khu vui choi trong nha."
        agent_result = {"agent_trace": [], "itinerary": []}
        response_type = "fallback"

    await crud.add_message(session_id=session_id, user_id=user_id, role="assistant", content=reply)
    return ChatResponse(reply=reply, type=response_type, user_id=user_id, session_id=session_id, agent_trace=agent_result.get("agent_trace", []), itinerary=agent_result.get("itinerary", []))
