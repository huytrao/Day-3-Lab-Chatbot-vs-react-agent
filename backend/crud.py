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


async def create_user(name: str, email: Optional[str] = None) -> str:
    document = {
        "name": name,
        "created_at": now_iso(),
    }
    if email:
        document["email"] = email

    result = await db.users.insert_one(document)
    return str(result.inserted_id)


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
    result = await db.user_profiles.insert_one(document)
    return str(result.inserted_id)


async def create_chat_session(user_id: str) -> str:
    session_id = make_session_id()
    timestamp = now_iso()
    await db.chat_sessions.insert_one(
        {
            "session_id": session_id,
            "user_id": user_id,
            "created_at": timestamp,
            "updated_at": timestamp,
        }
    )
    return session_id


async def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    if not ObjectId.is_valid(user_id):
        return None
    document = await db.users.find_one({"_id": ObjectId(user_id)})
    return object_id_to_str(document)


async def get_user_profile(user_id: str) -> Optional[Dict[str, Any]]:
    document = await db.user_profiles.find_one({"user_id": user_id})
    return object_id_to_str(document)


async def get_chat_session(session_id: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    query: Dict[str, Any] = {"session_id": session_id}
    if user_id:
        query["user_id"] = user_id
    document = await db.chat_sessions.find_one(query)
    return object_id_to_str(document)


async def add_message(session_id: str, user_id: str, role: str, content: str) -> str:
    result = await db.messages.insert_one(
        {
            "session_id": session_id,
            "user_id": user_id,
            "role": role,
            "content": content,
            "created_at": now_iso(),
        }
    )
    await db.chat_sessions.update_one(
        {"session_id": session_id},
        {"$set": {"updated_at": now_iso()}},
    )
    return str(result.inserted_id)


async def get_chat_history(session_id: str) -> List[Dict[str, Any]]:
    cursor = db.messages.find({"session_id": session_id}).sort("created_at", 1)
    documents = await cursor.to_list(length=None)
    return [object_id_to_str(document) for document in documents]
