from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class InitUserRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    name: str = Field(..., min_length=1)
    email: Optional[str] = None
    travel_group: str = "general"
    age_group: str = "general"
    budget: str = "medium"
    preferences: List[str] = Field(default_factory=list)
    duration: str = "1_day"
    priority: str = "general_advice"

    @model_validator(mode="before")
    @classmethod
    def map_frontend_fields(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        aliases = {
            "username": "name",
            "fullName": "name",
            "userName": "name",
            "group": "travel_group",
            "travelWith": "travel_group",
            "age": "age_group",
            "ages": "age_group",
            "interests": "preferences",
            "hobbies": "preferences",
            "time": "duration",
            "tripDuration": "duration",
            "note": "priority",
        }
        normalized = dict(data)
        for source, target in aliases.items():
            if target not in normalized and source in normalized:
                normalized[target] = normalized[source]

        if isinstance(normalized.get("preferences"), str):
            normalized["preferences"] = [normalized["preferences"]]
        elif normalized.get("preferences") is None:
            normalized["preferences"] = []
        return normalized


class InitUserResponse(BaseModel):
    status: int = 200
    user_id: str
    session_id: str
    message: str


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    user_id: Optional[str] = None
    session_id: Optional[str] = None
    text: Optional[str] = None
    message: Optional[str] = None
    content: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def strip_strings(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        normalized = dict(data)
        for key in ("user_id", "session_id", "text", "message", "content"):
            if isinstance(normalized.get(key), str):
                normalized[key] = normalized[key].strip()
        return normalized

    def get_user_message(self) -> Optional[str]:
        for value in (self.text, self.message, self.content):
            if isinstance(value, str) and value.strip():
                return value.strip()
        return None


class MessageResponse(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class HistoryResponse(BaseModel):
    status: int = 200
    session_id: str
    messages: List[MessageResponse]


class AgentTraceItem(BaseModel):
    type: str
    content: Optional[str] = None
    tool: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None


class ItineraryItem(BaseModel):
    time: str
    place: str
    description: str


class ChatResponse(BaseModel):
    status: int = 200
    reply: str
    type: Literal["text", "fallback"] = "text"
    user_id: str
    session_id: str
    agent_trace: List[Dict[str, Any]] = Field(default_factory=list)
    itinerary: List[Dict[str, Any]] = Field(default_factory=list)
