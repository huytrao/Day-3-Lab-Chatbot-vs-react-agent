# Workflow Backend - VinWonders Travel AI Agent

Tai lieu nay mo ta backend demo da duoc xay dung trong thu muc `backend/`. Backend dong vai tro API & System Orchestrator: nhan JSON tu frontend bat ky, luu du lieu vao MongoDB, lay profile/history, goi AI Agent mock, luu cau tra loi va tra JSON ve frontend.

## 1. Vi tri cac file

```text
backend/
├── main.py                         # Khai bao FastAPI app, CORS, routes API
├── database.py                     # Ket noi MongoDB va load bien moi truong
├── schemas.py                      # Pydantic request/response schemas
├── crud.py                         # Ham thao tac MongoDB collections
├── agent_connector.py              # Mock connector goi VinWonders AI Agent
├── requirements.txt                # Dependencies backend
├── README.md                       # Huong dan cai dat/chay API
├── WORKFLOW.md                     # Tai lieu workflow nay
└── vinwonders_backend_workflow.drawio # So do workflow mo bang draw.io
```

## 2. Chuc nang tong quan

Backend cung cap REST API JSON, khong phu thuoc React/Next.js/Vue/Flutter hay bat ky frontend framework nao.

Pham vi demo:

- Tu van tro choi phu hop cho khach di VinWonders/Vinpearl.
- Goi y theo profile: nhom di, do tuoi, ngan sach, so thich, thoi luong, uu tien.
- Luu user demo vao MongoDB.
- Luu profile khao sat ban dau.
- Tao chat session.
- Luu lich su tin nhan user/assistant.
- Reload lich su chat khi frontend F5.
- Goi mock AI Agent qua `run_vinwonders_agent()`.
- Tra ve `reply`, `agent_trace`, `itinerary` de frontend render.

Khong lam trong demo:

- Thanh toan that.
- Booking that.
- JWT phuc tap.
- GPS realtime.
- Google Maps that.
- Admin dashboard.

## 3. Bien moi truong

Backend doc bien moi truong tu:

1. `.env` o project root.
2. `backend/.env`, neu ton tai thi override bien tu root.

File lien quan: `backend/database.py`, `backend/main.py`.

Bien can co:

```env
MONGO_URI=mongodb://localhost:27017
MONGO_DB_NAME=vinwonders_agent
FRONTEND_ORIGIN=http://localhost:3000
```

Neu muon demo nhanh voi moi frontend:

```env
FRONTEND_ORIGIN=*
```

## 4. MongoDB Collections

### 4.1. `users`

Luu thong tin user demo.

Duoc tao boi ham:

- `crud.create_user(name, email=None)`

Document mau:

```json
{
  "_id": "ObjectId",
  "name": "Nguyen Van A",
  "created_at": "2026-06-01T10:00:00+00:00"
}
```

### 4.2. `user_profiles`

Luu thong tin khao sat ban dau cua user.

Duoc tao boi ham:

- `crud.create_user_profile(user_id, profile)`

Duoc doc boi ham:

- `crud.get_user_profile(user_id)`

Document mau:

```json
{
  "_id": "ObjectId",
  "user_id": "string",
  "travel_group": "family",
  "age_group": "children",
  "budget": "medium",
  "preferences": ["water_park", "kids_friendly", "less_walking"],
  "duration": "1_day",
  "priority": "avoid_hot_weather",
  "created_at": "2026-06-01T10:00:00+00:00"
}
```

### 4.3. `chat_sessions`

Luu session chat cua user.

Duoc tao boi ham:

- `crud.create_chat_session(user_id)`

Duoc doc boi ham:

- `crud.get_chat_session(session_id, user_id=None)`

Document mau:

```json
{
  "_id": "ObjectId",
  "session_id": "session_abc123",
  "user_id": "string",
  "created_at": "2026-06-01T10:00:00+00:00",
  "updated_at": "2026-06-01T10:05:00+00:00"
}
```

### 4.4. `messages`

Luu lich su chat.

Duoc tao boi ham:

- `crud.add_message(session_id, user_id, role, content)`

Duoc doc boi ham:

- `crud.get_chat_history(session_id)`

Document mau:

```json
{
  "_id": "ObjectId",
  "session_id": "session_abc123",
  "user_id": "string",
  "role": "user",
  "content": "Co tro gi cho be 5 tuoi?",
  "created_at": "2026-06-01T10:01:00+00:00"
}
```

## 5. Cac file va ham chinh

## 5.1. `main.py`

Day la entrypoint cua FastAPI app.

Thanh phan chinh:

- `lifespan(app)`: ping MongoDB khi startup, dong MongoDB client khi shutdown.
- `app = FastAPI(...)`: tao app va metadata cho Swagger.
- `app.add_middleware(CORSMiddleware, ...)`: bat CORS cho frontend goi API.
- `health_check()`: route `/health` va `/api/health`, dung de kiem tra service song.
- `init_user(payload)`: route `POST /api/init_user`.
- `get_history(session_id)`: route `GET /api/history/{session_id}`.
- `chat(payload)`: route `POST /api/chat`.

## 5.2. `database.py`

Phu trach ket noi MongoDB.

Ham/chuc nang:

- `get_settings()`: doc `MONGO_URI`, `MONGO_DB_NAME`.
- `client = AsyncIOMotorClient(...)`: tao MongoDB async client.
- `db = client[settings["mongo_db_name"]]`: lay database dang dung.
- `ping_database()`: kiem tra MongoDB khi app startup.
- `close_database()`: dong connection khi app shutdown.

## 5.3. `schemas.py`

Dinh nghia data contract bang Pydantic.

Schemas request:

- `InitUserRequest`: request cua `/api/init_user`.
- `ChatRequest`: request cua `/api/chat`, nhan linh hoat `text`, `message`, hoac `content`; `user_id` va `session_id` la tuy chon.

Schemas response:

- `InitUserResponse`: response tao user/session.
- `HistoryResponse`: response lich su chat.
- `MessageResponse`: tung message trong history.
- `ChatResponse`: response chat gom `status`, `reply`, `type`, `user_id`, `session_id`, `agent_trace`, `itinerary`.

Schemas phu:

- `AgentTraceItem`: mo ta trace dang thought/action/observation.
- `ItineraryItem`: mo ta tung moc lich trinh.

## 5.4. `crud.py`

Chua cac ham CRUD voi MongoDB. `main.py` khong thao tac database truc tiep ma goi qua file nay.

Ham tien ich:

- `now_iso()`: tao timestamp ISO UTC.
- `object_id_to_str(document)`: doi MongoDB `_id` tu `ObjectId` sang `str`.
- `make_session_id()`: tao session id dang `session_xxxxxxxxxxxx`.

Ham ghi du lieu:

- `create_user(name, email=None)`: insert vao `users`, tra ve `user_id`.
- `create_user_profile(user_id, profile)`: insert vao `user_profiles`.
- `create_chat_session(user_id)`: insert vao `chat_sessions`, tra ve `session_id`.
- `add_message(session_id, user_id, role, content)`: insert vao `messages`, dong thoi update `chat_sessions.updated_at`.

Ham doc du lieu:

- `get_user_by_id(user_id)`: tim user theo ObjectId.
- `get_user_profile(user_id)`: tim profile theo `user_id`.
- `get_chat_session(session_id, user_id=None)`: tim session, co the rang buoc them `user_id`.
- `get_chat_history(session_id)`: lay messages theo session va sort theo `created_at`.

## 5.5. `agent_connector.py`

Day la diem ket noi voi AI Agent cua thanh vien khac.

Ham chinh:

```python
def run_vinwonders_agent(user_message: str, user_profile: dict, chat_history: list) -> dict
```

Input:

- `user_message`: cau hoi moi nhat cua user.
- `user_profile`: profile lay tu MongoDB.
- `chat_history`: toan bo lich su chat cua session.

Output:

```json
{
  "reply": "...",
  "agent_trace": [
    {
      "type": "thought",
      "content": "..."
    },
    {
      "type": "action",
      "tool": "search_vinwonders_info",
      "parameters": {
        "query": "..."
      }
    },
    {
      "type": "observation",
      "content": "..."
    }
  ],
  "itinerary": [
    {
      "time": "09:00",
      "place": "Check-in",
      "description": "..."
    }
  ]
}
```

Hien tai day la mock agent. Sau nay team AI chi can thay body cua ham nay bang agent that, giu nguyen input/output contract.

## 6. Workflow API

## 6.1. Khoi tao user - `POST /api/init_user`

Muc tieu:

- Nhan thong tin user va khao sat ban dau.
- Tao user.
- Luu profile.
- Tao session chat.
- Tra ve `user_id` va `session_id`.

Luồng chi tiết:

1. Frontend gui JSON toi `/api/init_user`.
2. FastAPI validate request bang `InitUserRequest`.
3. `main.init_user()` goi `crud.create_user()`.
4. MongoDB insert document vao `users`.
5. `main.init_user()` goi `crud.create_user_profile()`.
6. MongoDB insert document vao `user_profiles`.
7. `main.init_user()` goi `crud.create_chat_session()`.
8. MongoDB insert document vao `chat_sessions`.
9. Backend tra response `InitUserResponse`.

Response:

```json
{
  "user_id": "...",
  "session_id": "session_...",
  "message": "User initialized successfully"
}
```

## 6.2. Lay history - `GET /api/history/{session_id}`

Muc tieu:

- Lay lai toan bo lich su chat theo session.
- Frontend reload/F5 khong mat conversation.

Luồng chi tiết:

1. Frontend goi `/api/history/{session_id}`.
2. `main.get_history()` kiem tra `session_id`.
3. Goi `crud.get_chat_session(session_id)`.
4. Neu khong co session: tra `status: 200` voi `messages: []`.
5. Goi `crud.get_chat_history(session_id)` neu session ton tai.
6. Chuyen MongoDB documents thanh list `{role, content}`.
7. Tra `HistoryResponse`.

Response:

```json
{
  "session_id": "session_abc123",
  "messages": [
    {
      "role": "user",
      "content": "Co tro gi cho be 5 tuoi?"
    },
    {
      "role": "assistant",
      "content": "Voi be nho, ban nen uu tien..."
    }
  ]
}
```

## 6.3. Chat voi Agent - `POST /api/chat`

Muc tieu:

- Nhan cau hoi moi tu frontend.
- Luu message user.
- Lay profile va history.
- Goi AI Agent mock.
- Luu assistant response.
- Tra JSON de frontend render.

Luồng chi tiết:

1. Frontend gui JSON toi `/api/chat`.
2. `main.chat()` lay cau hoi tu `text`, `message`, hoac `content`.
3. Neu khong co ca 3 field tren: tra HTTP 400 voi thong bao ro rang.
4. Neu thieu `user_id`: tao guest user bang `crud.create_user(name="Guest User")`.
5. Neu co `user_id` nhung user khong ton tai: tao guest user moi de frontend khong bi crash.
6. Neu thieu `session_id`: tao session moi bang `crud.create_chat_session(user_id)`.
7. Neu co `session_id` nhung session khong hop le voi user hien tai: tao session moi.
8. Lay profile bang `crud.get_user_profile(user_id)`; neu chua co thi dung profile mac dinh trong memory.
9. Luu message cua user bang `crud.add_message(..., role="user")`.
10. Lay chat history moi nhat bang `crud.get_chat_history(session_id)`.
11. Goi `run_vinwonders_agent(user_message, user_profile, chat_history)`.
12. Neu agent loi hoac khong co reply: tra fallback `status: 200`, `type: fallback`.
13. Luu reply assistant bang `crud.add_message(..., role="assistant")`.
14. Tra `ChatResponse` gom `status`, `reply`, `type`, `user_id`, `session_id`, `agent_trace`, `itinerary`.

Response:

```json
{
  "reply": "Voi be nho, ban nen uu tien ho boi tre em...",
  "session_id": "session_abc123",
  "agent_trace": [
    {
      "type": "thought",
      "content": "User asks for VinWonders travel advice..."
    }
  ],
  "itinerary": [
    {
      "time": "09:00",
      "place": "Check-in",
      "description": "Vao cong..."
    }
  ]
}
```

## 7. Xu ly loi co ban

Backend dang xu ly cac loi chinh:

- Thieu ca `text`, `message`, `content`: HTTP 400.
- Thieu `user_id`: backend tao guest user tam.
- Thieu `session_id`: backend tao session moi.
- `user_id` khong hop le hoac user khong ton tai: backend tao guest user moi.
- Session khong ton tai hoac khong thuoc user hien tai: backend tao session moi.
- User profile khong ton tai: backend dung profile mac dinh.
- Agent loi: backend khong crash, tra fallback `status: 200`, `type: fallback`.
- Agent khong tra `reply`: backend khong crash, tra fallback `status: 200`, `type: fallback`.

## 8. Cach chay demo

Tu project root:

```powershell
cd f:\VinUni_Lab\VinUni_Day3\Day-3-Lab-Chatbot-vs-react-agent
..\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Mo Swagger:

```text
http://127.0.0.1:8000/docs
```

Kiem tra health:

```text
http://127.0.0.1:8000/api/health
```

## 9. Cach thay mock agent bang agent that

Thanh vien AI chi can sua file:

```text
backend/agent_connector.py
```

Va giu nguyen ham:

```python
def run_vinwonders_agent(user_message: str, user_profile: dict, chat_history: list) -> dict:
```

Backend se tiep tuc goi ham nay trong `main.chat()`. Mien la agent that tra ve dict co cac key:

- `reply`
- `agent_trace`
- `itinerary`

Thi frontend khong can thay doi.

## 10. Tom tat vai tro backend

```text
Frontend bat ky
    -> FastAPI REST JSON API
    -> MongoDB profile/history/session
    -> agent_connector.run_vinwonders_agent()
    -> MongoDB luu assistant response
    -> JSON response ve frontend
```
