# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Cong Thai
- **Student ID**: 2A202600949
- **Date**: 2026-06-01

---

## I. Technical Contribution (15 Points)

### Modules Implemented

| Module | Mô tả |
|--------|-------|
| `data/crawler.py` | Crawl 8 URL VinWonders, trích xuất text từ HTML và PDF |
| `data/ingest.py` | Chunk và embed dữ liệu vào ChromaDB với model `all-MiniLM-L6-v2` |
| `data/db_accessor.py` | Hàm `retrieve_info()` query Vector DB, trả về top-k chunks |
| `data/retrieval_service.py` | Service kiểm tra retrieval với distance score chi tiết |
| `data/Intruction.md` | Tài liệu hướng dẫn toàn bộ pipeline và tích hợp cho các thành viên |

### Code Highlights

**`retrieve_info()` — hàm cốt lõi của pipeline RAG:**

```python
# data/db_accessor.py
def retrieve_info(query: str, n_results: int = 2) -> list[dict]:
    chunks = collection.query(
        query_texts=[query],
        n_results=n_results,
    )
    return [
        {"page_content": doc, "metadata": meta}
        for doc, meta in zip(
            chunks["documents"][0],
            chunks["metadatas"][0],
        )
    ]
```

**LangGraph Tool Router — định tuyến Agent đến đúng Tool:**

```python
def select_tool(state: AgentState) -> str:
    mapping = {
        "query_vinwonders": "query_db",
        "get_weather":      "weather",
        "get_ticket_price": "ticket",
    }
    return mapping.get(state["tool_name"], "fallback")

graph.add_conditional_edges("router", select_tool)
```

### Documentation

Pipeline hoạt động theo thứ tự: `crawler.py` → `raw_data.json` → `ingest.py` → `vector_db/` → `db_accessor.retrieve_info()`. Trong ReAct loop, mỗi khi Agent quyết định gọi tool `query_vinwonders`, LangGraph router sẽ điều hướng đến `run_query_tool()`, kết quả được format thành Observation và nạp ngược vào prompt cho vòng lặp tiếp theo.

---

## II. Debugging Case Study (10 Points)

### Problem Description

Trong quá trình test, Agent bị kẹt ở vòng lặp vô hạn với hành động lặp đi lặp lại:

```
Thought: I need to find the ticket price for Wave Park.
Action: query_vinwonders("giá vé Wave Park")
Observation: Giá vé người lớn: 450,000 VNĐ ...
Thought: I need to find the ticket price for Wave Park.
Action: query_vinwonders("giá vé Wave Park")   ← lặp lại
```

### Log Source

```
[2026-06-01 10:23:41] STEP 1 | Thought: I need to find the ticket price...
[2026-06-01 10:23:42] ACTION: query_vinwonders | args: {"query": "giá vé Wave Park"}
[2026-06-01 10:23:43] OBSERVATION: Giá vé người lớn: 450,000 VNĐ...
[2026-06-01 10:23:44] STEP 2 | Thought: I need to find the ticket price...  ← loop
[2026-06-01 10:23:45] ACTION: query_vinwonders | args: {"query": "giá vé Wave Park"}
```

### Diagnosis

LLM không nhận ra rằng Observation đã chứa đủ thông tin để trả lời. Nguyên nhân là system prompt thiếu ví dụ rõ ràng về trường hợp **"khi nào thì dừng và trả lời"**. Model cứ tiếp tục loop vì nó không có pattern `Final Answer:` trong few-shot examples.

### Solution

Thêm ví dụ `Final Answer` vào system prompt:

```python
REACT_SYSTEM_PROMPT = """...
Example:
Thought: The observation already contains the answer I need.
Final Answer: Giá vé người lớn tại VinWonders Wave Park là 450,000 VNĐ.
...
"""
```

Sau khi sửa, Agent dừng đúng sau 1 lần query và trả về Final Answer.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

### 1. Reasoning — Thought block giúp ích như thế nào?

Chatbot trả lời trực tiếp từ training data, không có bước kiểm tra. Ví dụ khi hỏi "giá vé VinWonders hôm nay", Chatbot có thể đưa ra giá cũ hoặc bịa số. ReAct Agent có bước `Thought` buộc LLM phân tách vấn đề thành các hành động nhỏ, sau đó xác nhận kết quả qua `Observation` trước khi trả lời — giống như lập trình viên kiểm tra output trước khi return.

### 2. Reliability — Khi nào Agent tệ hơn Chatbot?

| Tình huống | Chatbot | ReAct Agent |
|-----------|---------|-------------|
| Câu hỏi đơn giản ("VinWonders ở đâu?") | Nhanh, đủ | Chậm, tốn 2-3 bước không cần thiết |
| Câu hỏi cần dữ liệu mới (giá vé, thời tiết) | Sai hoặc bịa | Đúng nhờ tool |
| Câu hỏi mơ hồ | Hallucinate tự tin | Có thể loop vô hạn |

Agent thực sự tệ hơn Chatbot ở các câu hỏi đơn giản không cần tra cứu — overhead của Thought/Action/Observation làm tăng latency 3-5x mà không mang lại giá trị.

### 3. Observation — Environment feedback ảnh hưởng thế nào?

Observation đóng vai trò như "ground truth" trong mỗi vòng lặp. Khi Observation trả về dữ liệu chính xác từ Vector DB, Agent điều chỉnh Thought tiếp theo ngay lập tức — không cố đoán. Đây là sự khác biệt cơ bản nhất: Chatbot suy luận trong "không gian kín" (chỉ có training data), còn ReAct Agent suy luận trong "vòng lặp mở" với feedback từ môi trường thực.

---

## IV. Future Improvements (5 Points)

### Scalability — Mở rộng quy mô

- **Async tool execution**: Dùng `asyncio` để chạy song song nhiều tool call, giảm latency từ O(n) xuống O(1) khi có nhiều tool độc lập.
- **Tool retrieval**: Khi số lượng tool > 20, dùng Vector DB để embed mô tả tool và tìm tool phù hợp thay vì hardcode router.

```python
# Thay vì router cứng, embed tool descriptions
tool_chunks = vector_db.query(action_description, n_results=1)
selected_tool = tool_chunks[0]["tool_fn"]
```

### Safety — An toàn

- **Supervisor LLM**: Thêm một LLM thứ hai đóng vai "kiểm duyệt" — chỉ cho phép action được thực thi nếu nó nằm trong danh sách hành động được phép. Ngăn Agent gọi tool nguy hiểm (xóa DB, gửi email...).
- **Max iteration guard**: Giới hạn cứng số bước (`MAX_STEPS = 10`), sau đó force `Final Answer` để tránh infinite loop tốn token.

### Performance — Hiệu suất

- **Prompt caching**: Dùng Anthropic prompt caching cho system prompt và few-shot examples — tiết kiệm ~80% token cost cho phần context cố định.
- **Streaming Observation**: Stream kết quả tool về UI ngay khi có, thay vì chờ toàn bộ pipeline hoàn thành, cải thiện perceived latency.
- **Hybrid retrieval**: Kết hợp BM25 (keyword) + ChromaDB (semantic) để tăng recall — đặc biệt hữu ích với query chứa tên riêng (địa danh, loại vé cụ thể).

---

> **Submit**: Đổi tên file thành `REPORT_[TÊN_BẠN].md` và đặt vào thư mục `report/individual_reports/`.
