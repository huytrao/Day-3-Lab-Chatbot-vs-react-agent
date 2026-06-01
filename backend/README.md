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

Gemini API model:

```text
GEMINI_API_KEY=your_key
DEFAULT_PROVIDER=gemini
DEFAULT_MODEL=gemini-2.5-flash
```

FastAPI loads the Gemini key from the server-side `.env`; the frontend never sends or sees the key. `/api/health` reports whether Gemini is configured without exposing the key.

The LangGraph pipeline uses Gemini during the final synthesis step. If Gemini fails because of network, quota, or key issues, `/api/chat` still returns the tool-based draft answer and records the reason in `agent_trace`.

Local GGUF model, optional fallback helper:

```text
models/Phi-3-mini-4k-instruct-q4.gguf
```

Configure path in `backend/.env`:

```text
LOCAL_MODEL_PATH=./models/Phi-3-mini-4k-instruct-q4.gguf
```

If Windows shows `0xc000001d` while loading the model, the GGUF file is usually fine but the installed `llama-cpp-python` wheel is not compatible with the CPU. Install Visual Studio C++ Build Tools, then rebuild the package with:

```powershell
powershell -ExecutionPolicy Bypass -File backend\scripts\install_llama_cpp_portable_cpu.ps1
```

Tools live in:

```text
backend/tools/
```

Flowchart:

```text
backend/graph/flowchart.md
```
