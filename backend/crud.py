from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from bson import ObjectId

try:
    from .database import db
except ImportError:
    from database import db


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def object_id_to_str(document: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not document:
        return None
    document["_id"] = str(document["_id"])
    return document


def make_session_id() -> str:
    return f"session_{uuid4().hex[:12]}"


MEMORY_USERS: Dict[str, Dict[str, Any]] = {}
MEMORY_PROFILES: Dict[str, Dict[str, Any]] = {}
MEMORY_SESSIONS: Dict[str, Dict[str, Any]] = {}
MEMORY_MESSAGES: List[Dict[str, Any]] = []


async def create_user(name: str, email: Optional[str] = None) -> str:
    document = {"name": name, "created_at": now_iso()}
    if email:
        document["email"] = email
    try:
        result = await db.users.insert_one(document)
        return str(result.inserted_id)
    except Exception:
        user_id = str(ObjectId())
        MEMORY_USERS[user_id] = {"_id": user_id, **document}
        return user_id


async def create_user_profile(user_id: str, profile: Dict[str, Any]) -> str:
    document = {
        "user_id": user_id,
        "travel_group": profile.get("travel_group", "general"),
        "age_group": profile.get("age_group", "general"),
        "budget": profile.get("budget", "medium"),
        "preferences": profile.get("preferences", []),
        "duration": profile.get("duration", "1_day"),
        "priority": profile.get("priority", "general_advice"),
        "created_at": now_iso(),
    }
    try:
        result = await db.user_profiles.insert_one(document)
        return str(result.inserted_id)
    except Exception:
        profile_id = str(ObjectId())
        MEMORY_PROFILES[user_id] = {"_id": profile_id, **document}
        return profile_id


async def create_chat_session(user_id: str) -> str:
    session_id = make_session_id()
    timestamp = now_iso()
    document = {
        "session_id": session_id,
        "user_id": user_id,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    try:
        await db.chat_sessions.insert_one(document)
    except Exception:
        MEMORY_SESSIONS[session_id] = {"_id": str(ObjectId()), **document}
    return session_id


async def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    if not ObjectId.is_valid(user_id):
        return None
    try:
        return object_id_to_str(await db.users.find_one({"_id": ObjectId(user_id)}))
    except Exception:
        return MEMORY_USERS.get(user_id)


async def get_user_profile(user_id: str) -> Optional[Dict[str, Any]]:
    try:
        return object_id_to_str(await db.user_profiles.find_one({"user_id": user_id}))
    except Exception:
        return MEMORY_PROFILES.get(user_id)


async def get_chat_session(session_id: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    query: Dict[str, Any] = {"session_id": session_id}
    if user_id:
        query["user_id"] = user_id
    try:
        return object_id_to_str(await db.chat_sessions.find_one(query))
    except Exception:
        session = MEMORY_SESSIONS.get(session_id)
        if session and (not user_id or session.get("user_id") == user_id):
            return session
        return None


async def add_message(session_id: str, user_id: str, role: str, content: str) -> str:
    document = {
        "session_id": session_id,
        "user_id": user_id,
        "role": role,
        "content": content,
        "created_at": now_iso(),
    }
    try:
        result = await db.messages.insert_one(document)
        await db.chat_sessions.update_one(
            {"session_id": session_id},
            {"$set": {"updated_at": now_iso()}},
        )
        return str(result.inserted_id)
    except Exception:
        message_id = str(ObjectId())
        MEMORY_MESSAGES.append({"_id": message_id, **document})
        if session_id in MEMORY_SESSIONS:
            MEMORY_SESSIONS[session_id]["updated_at"] = now_iso()
        return message_id


async def get_chat_history(session_id: str) -> List[Dict[str, Any]]:
    try:
        cursor = db.messages.find({"session_id": session_id}).sort("created_at", 1)
        return [object_id_to_str(document) for document in await cursor.to_list(length=None)]
    except Exception:
        return [message for message in MEMORY_MESSAGES if message.get("session_id") == session_id]
