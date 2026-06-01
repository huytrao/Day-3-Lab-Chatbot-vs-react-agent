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

## Agent Pipeline

`backend/agent_connector.py` first tries the LangGraph pipeline in `backend/graph/graph.py`.
If the graph, tools, local model, or retrieval layer fails, it falls back to a safe demo response.

Local GGUF model:

```text
models/Phi-3-mini-4k-instruct-q4.gguf
```

Configure path in `backend/.env`:

```text
LOCAL_MODEL_PATH=./models/Phi-3-mini-4k-instruct-q4.gguf
```

The local model is optional. If `llama-cpp-python`, the model file, or the CPU runtime fails, `/api/chat` still returns the rule-based LangGraph answer and records the fallback reason in `agent_trace`.

Tools live in:

```text
backend/tools/
```

Flowchart:

```text
backend/graph/flowchart.md
```
