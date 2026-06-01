# VinWonders Travel AI Agent Backend

Backend demo using FastAPI + MongoDB. It acts as a JSON API and system orchestrator for any frontend framework.

Current frontend flow:

1. User enters a name.
2. User fills an optional travel survey.
3. Frontend moves to the chat page.
4. Frontend calls this backend with JSON.

## Features

- No login, no JWT, no authentication requirement.
- `email` is optional.
- Create demo users and initial travel profiles.
- Create chat sessions automatically.
- Store and reload chat history.
- Accept chat message from `text`, `message`, or `content`.
- Create a guest user if `/api/chat` is called without `user_id`.
- Create a new session if `/api/chat` is called without `session_id`.
- Call a mock `run_vinwonders_agent()` connector.
- Return frontend-friendly JSON with `reply`, `type`, `user_id`, `session_id`, `agent_trace`, and `itinerary`.
- CORS enabled for frontend demos.

## Setup

Create a `.env` file in the project root or inside `backend/`:

```env
MONGO_URI=mongodb://localhost:27017
MONGO_DB_NAME=vinwonders_agent
FRONTEND_ORIGIN=*
```

Install dependencies:

```bash
cd backend
python -m pip install -r requirements.txt
```

Start MongoDB locally, then run the API:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Or from the project root:

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Open Swagger:

```text
http://localhost:8000/docs
```

## API

### GET `/api/health`

Response:

```json
{
  "status": 200,
  "message": "Backend is running"
}
```

### POST `/api/init_user`

Minimum request:

```json
{
  "name": "Dao"
}
```

Full request:

```json
{
  "name": "Dao",
  "travel_group": "family",
  "age_group": "children",
  "budget": "medium",
  "preferences": ["water_park", "kids_friendly", "less_walking"],
  "duration": "1_day",
  "priority": "avoid_hot_weather"
}
```

Flexible frontend field names are accepted:

- `username`, `fullName`, `userName` -> `name`
- `group`, `travelWith` -> `travel_group`
- `age`, `ages` -> `age_group`
- `interests`, `hobbies` -> `preferences`
- `time`, `tripDuration` -> `duration`
- `note` -> `priority`

Response:

```json
{
  "status": 200,
  "user_id": "665f1c...",
  "session_id": "session_abc123",
  "message": "User initialized successfully"
}
```

### GET `/api/history/{session_id}`

Response if messages exist:

```json
{
  "status": 200,
  "session_id": "session_abc123",
  "messages": [
    {
      "role": "user",
      "content": "Co tro gi cho be 5 tuoi?"
    },
    {
      "role": "assistant",
      "content": "Voi be 5 tuoi, ban nen uu tien ho boi tre em..."
    }
  ]
}
```

Response if there is no history:

```json
{
  "status": 200,
  "session_id": "session_abc123",
  "messages": []
}
```

### POST `/api/chat`

Preferred request:

```json
{
  "user_id": "665f1c...",
  "session_id": "session_abc123",
  "text": "Co tro gi cho be 5 tuoi?"
}
```

Also accepted:

```json
{
  "message": "Co tro gi cho be 5 tuoi?"
}
```

or:

```json
{
  "content": "Co tro gi cho be 5 tuoi?"
}
```

If `user_id` is missing, the backend creates a guest user. If `session_id` is missing, the backend creates a new session. The response always returns both values so the frontend can store them.

Success response:

```json
{
  "status": 200,
  "reply": "Voi be nho, ban nen uu tien ho boi tre em...",
  "type": "text",
  "user_id": "665f1c...",
  "session_id": "session_abc123",
  "agent_trace": [],
  "itinerary": []
}
```

Fallback response if the agent fails:

```json
{
  "status": 200,
  "reply": "Hien tai AI Agent gap loi tam thoi. Ban co the thu lai hoac dung lich trinh mac dinh: sang cong vien nuoc, trua an uong nghi ngoi, chieu khu vui choi trong nha.",
  "type": "fallback",
  "user_id": "665f1c...",
  "session_id": "session_abc123",
  "agent_trace": [],
  "itinerary": []
}
```

If the message is missing:

```json
{
  "detail": "Missing message. Please send one of: text, message, content."
}
```

## Collections

- `users`
- `user_profiles`
- `chat_sessions`
- `messages`

## Agent Integration

The current `agent_connector.py` contains a mock function:

```python
def run_vinwonders_agent(user_message: str, user_profile: dict, chat_history: list) -> dict:
    ...
```

The AI team can replace only this function body later while keeping the same response format.
