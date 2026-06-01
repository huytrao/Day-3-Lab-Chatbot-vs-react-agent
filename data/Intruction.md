# Hướng dẫn chạy Data Pipeline VinWonders

Pipeline gồm 3 bước: **Crawl → Ingest → Retrieve**

```
crawler.py  →  raw_data.json  →  ingest.py  →  vector_db/  →  retrieval_service.py
```

---

## Yêu cầu môi trường

- Python 3.12+
- **Windows:** chạy lệnh với `$env:PYTHONIOENCODING = "utf-8"` để tránh lỗi encoding tiếng Việt

---

## Bước 0 — Cài đặt thư viện

```bash
pip install chromadb sentence-transformers langchain-text-splitters pdfplumber requests beautifulsoup4
```

> `sentence-transformers` tải model `all-MiniLM-L6-v2` (~90MB) lần đầu, cần internet.

---

## Bước 1 — Chạy Crawler

```bash
# Linux/macOS
python data/crawler.py

# Windows PowerShell
$env:PYTHONIOENCODING = "utf-8"; python data/crawler.py
```

Script sẽ crawl 8 URL VinWonders sau:

| URL | Nội dung |
|-----|----------|
| `/vi/vinwonders-wave-park-water-park-price-regulations/` | Giá vé & nội quy Wave Park / Water Park |
| `/vi/vinwonders-nha-trang-price-and-regulations/` | Giá vé & nội quy Nha Trang |
| `/vi/vinwonders-phu-quoc-price-and-regulations/` | Giá vé & nội quy Phú Quốc |
| `/vi/vinwonders-nam-hoi-an-price-and-regulations/` | Giá vé & nội quy Nam Hội An |
| `/vi/diem-den/water-park/` | Trang Water Park tổng quan |
| `/vi/wonderpedia/news/cong-vien-song-vinwonders-wave-park/` | Bài viết Wave Park |
| `/vi/wonderpedia/news/kinh-nghiem-di-vinwonders-va-vinpearl-safari-phu-quoc-day-du-nhat/` | Kinh nghiệm tham quan Phú Quốc |
| `/vi/bai-viet-du-lich/vinwonders-ha-noi/` | VinWonders Hà Nội |

**Kết quả mong đợi:**
```
[SUCCESS] Da luu 8 nguon du lieu vao file: data/raw_data.json
```

**Bổ sung PDF (tuỳ chọn):** Đặt file vào thư mục `data/` với tên:
- `bang_gia_ve_vinwonders.pdf`
- `quy_dinh_cong_vien_nuoc.pdf`

Chạy lại `crawler.py` — script sẽ tự nhận và thêm vào `raw_data.json`.

---

## Bước 2 — Ingest vào Vector DB

```bash
# Linux/macOS
python data/ingest.py

# Windows PowerShell
$env:PYTHONIOENCODING = "utf-8"; python data/ingest.py
```

**Kết quả mong đợi:**
```
[INFO] Dang khoi tao mo hinh Embedding (all-MiniLM-L6-v2)...
[INFO] Dang nap XX doan vao ChromaDB...
[SUCCESS] Hoan thanh qua trinh ingest vao: data/vector_db
```

**Thông số chunk:**

| Tham số | Giá trị |
|---------|---------|
| `chunk_size` | 500 ký tự |
| `chunk_overlap` | 50 ký tự |
| Embedding model | `all-MiniLM-L6-v2` |
| Vector DB | ChromaDB persistent (lưu tại `data/vector_db/`) |
| Collection | `vinwonders_knowledge_base` |

> **Lưu ý:** Nếu đã chạy ingest trước đó, ChromaDB sẽ báo lỗi duplicate ID. Xoá thư mục `data/vector_db/` rồi chạy lại.

---

## Bước 3 — Kiểm tra Retrieval

### Cách 1 — Chạy nhanh (db_accessor)

```bash
$env:PYTHONIOENCODING = "utf-8"; python data/db_accessor.py
```

Kết quả mong đợi:
```
[INFO] So luong doan trich xuat duoc: 2
```

### Cách 2 — Chạy chi tiết (retrieval_service)

```bash
$env:PYTHONIOENCODING = "utf-8"; python data/retrieval_service.py
```

Kết quả mong đợi (mỗi chunk có nội dung + nguồn + distance score):
```
[Doan thong tin 1]
Noi dung: ...
Nguon: VinWonders Wave Park & Water Park ...
Do sai lech Vector (Distance): 0.52  ← càng thấp càng liên quan
```

### Cách 3 — Test từ Python REPL

```python
import sys
sys.path.insert(0, "data")
from db_accessor import retrieve_info

queries = [
    "giá vé người lớn VinWonders Wave Park",
    "quy định mang đồ ăn vào công viên nước",
    "thời gian mở cửa VinWonders",
]

for q in queries:
    results = retrieve_info(q, n_results=3)
    print(f"\nQuery: {q}  →  {len(results)} chunks")
    for i, r in enumerate(results):
        print(f"  [{i+1}] {r['page_content'][:120]}...")
```

---

## Hướng dẫn cho Thành viên 4 — Tool Maker & LangGraph Engineer

### Tổng quan vai trò

Thành viên 4 chịu trách nhiệm:
- Xây dựng các **Python Tools** để Agent gọi (lấy thời tiết, tra giá vé, query Vector DB)
- Dùng **LangGraph** xây dựng State Graph định tuyến đúng Tool vào đúng thời điểm
- Định dạng **Observation** chuẩn để trả kết quả ngược lại cho ReAct Agent (Thành viên 5)

---

### Cài đặt thêm

```bash
pip install langgraph langchain langchain-anthropic
```

---

### Tool 1 — Query Vector DB (dùng file có sẵn)

Không cần viết lại, dùng thẳng `retrieve_info()` từ `db_accessor.py`:

```python
import sys
sys.path.insert(0, "data")
from db_accessor import retrieve_info

def tool_query_vinwonders(query: str) -> str:
    """Tool tra cứu thông tin VinWonders từ Vector DB."""
    chunks = retrieve_info(query, n_results=3)
    if not chunks:
        return "Không tìm thấy thông tin liên quan."
    context = "\n\n".join([c["page_content"] for c in chunks])
    return context
```

**Đầu vào:** `query` — câu hỏi của người dùng (ví dụ: `"giá vé người lớn Wave Park"`)

**Đầu ra:** chuỗi text gộp các chunk liên quan nhất từ Vector DB

---

### Tool 2 — Lấy thời tiết (Weather API)

```python
import requests

def tool_get_weather(location: str, date: str = "today") -> str:
    """Tool lấy thông tin thời tiết theo địa điểm và ngày."""
    # Dùng Open-Meteo (miễn phí, không cần API key)
    geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={location}&count=1&language=vi"
    geo_res = requests.get(geo_url).json()

    if not geo_res.get("results"):
        return f"Không tìm thấy địa điểm: {location}"

    lat = geo_res["results"][0]["latitude"]
    lon = geo_res["results"][0]["longitude"]

    weather_url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        f"&daily=temperature_2m_max,temperature_2m_min,precipitation_sum"
        f"&timezone=Asia%2FHo_Chi_Minh&forecast_days=3"
    )
    weather_res = requests.get(weather_url).json()
    daily = weather_res.get("daily", {})

    if not daily:
        return "Không lấy được dữ liệu thời tiết."

    result = f"Thời tiết tại {location}:\n"
    for i, d in enumerate(daily.get("time", [])):
        t_max = daily["temperature_2m_max"][i]
        t_min = daily["temperature_2m_min"][i]
        rain = daily["precipitation_sum"][i]
        result += f"  {d}: {t_min}°C – {t_max}°C, mưa {rain}mm\n"
    return result.strip()
```

---

### Tool 3 — Tra giá vé VinWonders

```python
TICKET_PRICES = {
    "wave_park": {"người lớn": 450000, "trẻ em": 350000, "người cao tuổi": 350000},
    "nha_trang": {"người lớn": 900000, "trẻ em": 700000, "người cao tuổi": 700000},
    "phu_quoc":  {"người lớn": 850000, "trẻ em": 650000, "người cao tuổi": 650000},
    "nam_hoi_an":{"người lớn": 750000, "trẻ em": 600000, "người cao tuổi": 600000},
}

def tool_get_ticket_price(location: str, ticket_type: str = "người lớn") -> str:
    """Tool tra giá vé VinWonders theo địa điểm và loại vé."""
    location_map = {
        "wave park": "wave_park", "nha trang": "nha_trang",
        "phú quốc": "phu_quoc",  "nam hội an": "nam_hoi_an",
    }
    key = location_map.get(location.lower().strip())
    if not key:
        return f"Không có thông tin giá vé cho địa điểm: {location}. Thử: Wave Park, Nha Trang, Phú Quốc, Nam Hội An."

    prices = TICKET_PRICES[key]
    ticket_key = ticket_type.lower().strip()
    if ticket_key not in prices:
        return f"Loại vé '{ticket_type}' không hợp lệ. Chọn: người lớn, trẻ em, người cao tuổi."

    price = prices[ticket_key]
    return f"Giá vé {ticket_type} tại VinWonders {location}: {price:,} VNĐ"
```

> **Lưu ý:** Giá vé trên là ví dụ minh họa. Nên gọi `tool_query_vinwonders("giá vé ...")` để lấy giá chính xác từ Vector DB thay vì hardcode.

---

### Xây dựng State Graph với LangGraph

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, Literal

# --- Định nghĩa State ---
class AgentState(TypedDict):
    user_query: str
    tool_name: str          # tên tool cần gọi (từ ReAct Agent)
    tool_args: dict         # tham số tool
    observation: str        # kết quả tool trả về
    next: str               # node tiếp theo

# --- Các node trong graph ---
def route_tool(state: AgentState) -> AgentState:
    """Định tuyến đến đúng tool dựa trên tool_name."""
    return state  # routing logic nằm ở conditional_edge

def run_query_tool(state: AgentState) -> AgentState:
    result = tool_query_vinwonders(state["tool_args"].get("query", state["user_query"]))
    return {**state, "observation": result}

def run_weather_tool(state: AgentState) -> AgentState:
    args = state["tool_args"]
    result = tool_get_weather(args.get("location", ""), args.get("date", "today"))
    return {**state, "observation": result}

def run_ticket_tool(state: AgentState) -> AgentState:
    args = state["tool_args"]
    result = tool_get_ticket_price(args.get("location", ""), args.get("ticket_type", "người lớn"))
    return {**state, "observation": result}

def fallback_tool(state: AgentState) -> AgentState:
    return {**state, "observation": f"Không tìm thấy tool: {state['tool_name']}"}

# --- Hàm chọn node tiếp theo ---
def select_tool(state: AgentState) -> Literal["query_db", "weather", "ticket", "fallback"]:
    mapping = {
        "query_vinwonders": "query_db",
        "get_weather":      "weather",
        "get_ticket_price": "ticket",
    }
    return mapping.get(state["tool_name"], "fallback")

# --- Xây graph ---
graph = StateGraph(AgentState)
graph.add_node("router",   route_tool)
graph.add_node("query_db", run_query_tool)
graph.add_node("weather",  run_weather_tool)
graph.add_node("ticket",   run_ticket_tool)
graph.add_node("fallback", fallback_tool)

graph.set_entry_point("router")
graph.add_conditional_edges("router", select_tool)
graph.add_edge("query_db", END)
graph.add_edge("weather",  END)
graph.add_edge("ticket",   END)
graph.add_edge("fallback", END)

tool_graph = graph.compile()
```

---

### Định dạng Observation trả về cho Agent

Mỗi tool phải trả về chuỗi theo định dạng chuẩn để ReAct Agent (Thành viên 5) parse được:

```python
def format_observation(tool_name: str, result: str) -> str:
    return f"[Observation from {tool_name}]\n{result}"

# Ví dụ gọi toàn bộ flow
def execute_tool(tool_name: str, tool_args: dict, user_query: str) -> str:
    state = {
        "user_query": user_query,
        "tool_name": tool_name,
        "tool_args": tool_args,
        "observation": "",
        "next": "",
    }
    result_state = tool_graph.invoke(state)
    return format_observation(tool_name, result_state["observation"])
```

**Ví dụ sử dụng:**

```python
# ReAct Agent gửi action: tool_name="get_weather", args={"location": "Phú Quốc", "date": "cuối tuần"}
obs = execute_tool("get_weather", {"location": "Phú Quốc"}, "thời tiết Phú Quốc cuối tuần")
print(obs)
# [Observation from get_weather]
# Thời tiết tại Phú Quốc:
#   2026-06-07: 26°C – 33°C, mưa 5.2mm
#   ...

obs = execute_tool("get_ticket_price", {"location": "Wave Park", "ticket_type": "trẻ em"}, "giá vé trẻ em Wave Park")
print(obs)
# [Observation from get_ticket_price]
# Giá vé trẻ em tại VinWonders Wave Park: 350,000 VNĐ
```

---

### Sơ đồ luồng LangGraph

```
[ReAct Agent (TV5)]
        │
        │  Action: {tool_name, args}
        ▼
   ┌─────────┐
   │ router  │  ← entry point
   └────┬────┘
        │ conditional_edge (dựa trên tool_name)
   ┌────┴──────────────────┐
   │                       │
   ▼                       ▼                    ▼
[query_db]           [weather]            [ticket]
retrieve_info()   open-meteo API     TICKET_PRICES dict
   │                   │                    │
   └───────────────────┴────────────────────┘
                        │
                        ▼
                  format_observation()
                        │
                        ▼
              [ReAct Agent (TV5)] nhận Observation
```

---

### Tích hợp vào Agent (cho Thành viên 4)

Dùng hàm `retrieve_info()` từ `db_accessor.py`:

```python
from data.db_accessor import retrieve_info

# Lấy context từ Vector DB trước khi gọi LLM
chunks = retrieve_info(user_query, n_results=3)
context = "\n\n".join([c["page_content"] for c in chunks])

# Đưa context vào prompt
prompt = f"""Dựa vào thông tin sau:\n{context}\n\nTrả lời câu hỏi: {user_query}"""
```

---

## Xử lý lỗi thường gặp

| Lỗi | Nguyên nhân | Cách sửa |
|-----|-------------|----------|
| `UnicodeEncodeError` | Console Windows không hỗ trợ tiếng Việt | Thêm `$env:PYTHONIOENCODING = "utf-8"` |
| `ModuleNotFoundError: chromadb` | Chưa cài | `pip install chromadb` |
| `[ERROR] Khong tim thay Vector DB` | Chưa chạy ingest | Chạy `ingest.py` trước |
| `[ERROR] Khong tim thay raw_data.json` | Chưa chạy crawler | Chạy `crawler.py` trước |
| `UniqueConstraintError` / duplicate ID | Chạy ingest lần 2 | Xoá `data/vector_db/` rồi chạy lại |
| HTTP 404 khi crawl | URL đã đổi | Cập nhật danh sách URL trong `crawler.py` dòng 112 |

---

## Thứ tự chạy tóm tắt

```
1. pip install chromadb sentence-transformers langchain-text-splitters pdfplumber requests beautifulsoup4
2. python data/crawler.py          →  tạo data/raw_data.json
3. python data/ingest.py           →  tạo data/vector_db/
4. python data/retrieval_service.py  →  kiểm tra retrieval hoạt động
```

---

## Hướng dẫn commit lên GitHub

### Lần đầu — Cấu hình git (nếu chưa làm)

```bash
git config --global user.name "Tên của bạn"
git config --global user.email "email@example.com"
```

### Quy trình commit chuẩn

**Bước 1 — Kiểm tra file nào thay đổi:**
```bash
git status
```

**Bước 2 — Thêm file cần commit** (chỉ thêm file cần thiết, không dùng `git add .` để tránh commit `venv/`):
```bash
# Thêm từng file cụ thể
git add data/crawler.py
git add data/Intruction.md

# Hoặc thêm cả thư mục data (an toàn vì venv/ nằm ngoài)
git add data/
```

**Bước 3 — Kiểm tra lại trước khi commit:**
```bash
git diff --staged
```

**Bước 4 — Tạo commit:**
```bash
git commit -m "mô tả ngắn gọn thay đổi"
```

Ví dụ commit message theo từng loại thay đổi:
```bash
# Cập nhật URL crawler
git commit -m "fix: update crawler URLs to working VinWonders pages"

# Thêm dữ liệu mới
git commit -m "data: add raw_data.json from VinWonders crawl"

# Sửa lỗi
git commit -m "fix: resolve Unicode encoding error on Windows"
```

**Bước 5 — Push lên GitHub:**
```bash
git push origin main
```

---

### Những file KHÔNG nên commit

Thêm vào `.gitignore` nếu chưa có:

```
venv/
data/vector_db/
data/raw_data.json
__pycache__/
*.pyc
.env
```

> `vector_db/` và `raw_data.json` là file sinh ra tự động khi chạy pipeline — không cần commit, mỗi người tự chạy lại trên máy của mình.

---

### Kiểm tra sau khi push

```bash
# Xem lịch sử commit
git log --oneline -5

# Xem trạng thái so với remote
git status
```
