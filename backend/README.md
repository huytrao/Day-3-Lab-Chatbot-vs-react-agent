# VinWonders Travel AI Agent Backend

FastAPI + MongoDB backend for the VinWonders/Vinpearl travel demo.

## Run

```bash
cd backend
python -m pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Or from project root:

```bash
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Swagger:

```text
http://localhost:8000/docs
```

## API

- `GET /api/health`
- `POST /api/init_user`
- `GET /api/history/{session_id}`
- `POST /api/chat`

`/api/chat` accepts `text`, `message`, or `content`. If `user_id` or `session_id` is missing, the backend creates them and returns them.
