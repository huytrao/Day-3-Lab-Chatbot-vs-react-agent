# Group Report: Lab 3 - Production-Grade Agentic System

- **Team Name**: VinWonders AI Team
- **Team Members**:
  Công Thái - 2A202600949
  Lê Hữu Đạt - 2A202600630
  Nguyễn Đông Anh - 2A202600760
  Lê Trí Nguyên - 2A202600651
  Trảo An Huy - 2A202600819
- **Deployment Date**: 2026-06-01

---

## 1. Executive Summary

Mục tiêu của dự án là nâng cấp từ một Chatbot LLM cơ bản lên hệ thống **ReAct Agent** (Reasoning and Acting) có khả năng giải quyết các truy vấn phức tạp của khách du lịch VinWonders (đòi hỏi nhiều bước như: tra cứu thời tiết, tìm giá vé, tính tổng tiền).

- **Key Outcome**: Agent của nhóm đã giải quyết được **55%** số lượng truy vấn đa bước (multi-step queries) mà Chatbot baseline hoàn toàn thất bại (Chatbot baseline thường xuyên bị ảo giác giá vé hoặc không thể kết hợp thời tiết và lịch trình). Chúng tôi đã triển khai thành công 4 công cụ (Tools) với cơ chế tự phục hồi (Self-healing/Retry) khi parse lỗi.

---

## 2. System Architecture & Tooling

### 2.1 ReAct Loop Implementation & Flowchart

Kiến trúc hệ thống được xây dựng theo mô hình vòng lặp **Thought-Action-Observation**. Backend (FastAPI) nhận request từ UI, duy trì trạng thái ngữ cảnh từ Database và đưa cho Agent xử lý.

### 2.2 Tool Definitions & Evolution (Inventory)

Nhóm đã phát triển 4 công cụ chính và liên tục nâng cấp đặc tả (Spec Evolution) từ V1 lên V2 để LLM dễ hiểu hơn:

| Tool Name              | Input Format                                                 | Use Case                                             | Evolution from v1 to v2                                                                                      |
| :--------------------- | :----------------------------------------------------------- | :--------------------------------------------------- | :----------------------------------------------------------------------------------------------------------- |
| `search_vin_knowledge` | `{"query": "string"}`                                        | Tra cứu thông tin vé, địa điểm từ Vector DB (Chroma) | **V2**: Thêm chỉ dẫn rõ ràng cấm LLM tự bịa giá nếu không tìm thấy.                                          |
| `get_weather`          | `{"location": "str", "date": "str"}`                         | Lấy thời tiết thực tế                                | **V2**: Định dạng chuẩn `YYYY-MM-DD` thay vì text tự do.                                                     |
| `calc_price`           | `{"ticket_type": "str", "adult_count": 0, "child_count": 0}` | Tính tổng tiền vé                                    | **V2**: Tách biệt rõ `adult_count` và `child_count` thành kiểu _Integer_, chặn tính toán sai do LLM tự cộng. |
| `itinerary_tool`       | `{"preferences": "str", "duration_hours": 0}`                | Lên lịch trình tự động                               | **Bonus Tool**: Sinh lịch trình dựa trên độ tuổi (lấy từ User Profile).                                      |

### 2.3 LLM Providers Used

- **Primary**: Cấu hình chạy Local Model `Phi-3-mini-4k-instruct` (cho phép dev cục bộ không tốn phí).
- **Secondary (Backup/Polish)**: `Gemini 1.5 Flash` (Sử dụng Provider Pattern để chuyển đổi linh hoạt, dùng để đánh bóng câu trả lời cuối cùng).

---

## 3. Telemetry & Performance Dashboard (Extra Monitoring Bonus)

Hệ thống được tích hợp monitor sâu (Telemetry Logging) giúp đo đếm hiệu suất xử lý thực tế:

- **Average Latency (P50)**: 1450ms (Cho các câu hỏi đơn giản, không gọi tool).
- **Max Latency (P99)**: 6200ms (Cho các truy vấn đa bước gọi tool 3 vòng lặp).
- **Average Tokens per Task**: ~850 tokens (đã tối ưu bằng Sliding Window giữ 5 lượt hội thoại).
- **Tool Success Ratio**: 92% (Tỉ lệ tool parse chuẩn JSON ngay từ lần đầu).
- **Cost Metrics**: Hoàn toàn miễn phí khi dùng Local Phi-3. Chi phí API Gemini mô phỏng < $0.01 cho 100 requests.

---

## 4. Root Cause Analysis (RCA) - Failure Traces

### Case Study 1: [Hallucinated JSON Format & Infinite Loop] (Agent v1)

- **Input**: "Tính tổng tiền 2 vé người lớn và 1 vé trẻ em đi Wave Park."
- **Observation / Trace**: LLM sinh ra `{"tool": "calc_price", "params": "2 người lớn 1 trẻ em"}` thay vì JSON chuẩn `{"adult_count": 2, "child_count": 1}`.
- **Root Cause**: Prompt V1 chưa có ví dụ (Few-Shot Prompting) cụ thể về cấu trúc JSON param của tool `calc_price`, dẫn đến Parser bị sập. LLM nhận về `"Error: Invalid JSON"`, sau đó hoảng loạn và tiếp tục ném ra dữ liệu sai, ngốn sạch Max Tokens (Infinite Loop).
- **Agent v2 Fix (Failure Handling Bonus)**:
  - Cập nhật System Prompt với cấu trúc _Few-Shot_.
  - Thêm Guardrail: Nếu JSON parse lỗi, hệ thống tự động chèn Observation: `Error: Params must be valid JSON exact to {"adult_count": int, "child_count": int}. Please try again.` vào Prompt.

### Case Study 2: [Knowledge Hallucination]

- **Input**: "Công viên có mở cửa lúc 3h sáng không?"
- **Observation**: `search_vin_knowledge` trả về kết quả rỗng. LLM tự động trả lời: `"Dạ công viên mở cửa 24/24"`.
- **Root Cause**: Thiếu chỉ thị "Say I don't know if not in Observation".
- **Fix**: Thêm ràng buộc cứng vào Prompt và Gemni Polish step: `"Chỉ sử dụng thông tin từ file context. Cấm bịa đặt."`.

---

## 5. Ablation Studies & Experiments (Bonus)

### Experiment 1: Prompt v1 (Zero-Shot) vs Prompt v2 (Few-Shot)

- **Diff**: Thêm 2 ví dụ minh họa cách tư duy (Thought) trước khi gọi Action.
- **Result**: Giảm hẳn lỗi cú pháp. Tỉ lệ gọi Tool thành công ngay lần đầu tăng từ **45% lên 92%**.

### Experiment 2: Baseline LLM Chatbot vs ReAct Agent

Đánh giá trên bộ 20 câu hỏi tổ hợp (Complex Queries):
| Case Type | Chatbot Baseline Result | ReAct Agent Result | Winner |
| :--- | :--- | :--- | :--- |
| Simple Q (Chào hỏi, hỏi giá lẻ) | Trả lời nhanh (1s) | Trả lời hơi chậm (3s) | **Chatbot** (vì UX nhanh) |
| Multi-step (Thời tiết mai + lịch trình) | Bịa thời tiết, lịch trình bất hợp lý | Gọi API Thời tiết -> Tạo lịch trình thực tế | **ReAct Agent** |
| Math (Tính tiền 5 lớn, 3 nhỏ ghép combo) | Sai toán học (Hallucination) | Gọi `calc_price` -> Chính xác 100% | **ReAct Agent** |

---

## 6. Production Readiness Review

Để đưa hệ thống Agent này triển khai cho chuỗi thực tế của VinWonders (Production), nhóm đề xuất:

1. **Security**:
   - Đầu vào (Prompt Injection): Cần cơ chế lọc input của người dùng trước khi đưa vào LLM để tránh các câu lệnh ép agent lộ System Prompt.
   - Database / CORS: Đã được xử lý ở mức backend API, chặn query SQL Injection từ phía Frontend.
2. **Guardrails**:
   - Limit số vòng lặp: Đã thiết lập MAX_LOOPS = 5. Nếu quá 5 bước mà Agent chưa ra Final Answer, buộc phải dừng và xin lỗi khách để tránh bill tiền API tăng vô hạn.
3. **Scaling**:
   - Nâng cấp lưu trữ bộ nhớ (Memory): Sử dụng Redis để quản lý session tốc độ cao, thay vì query DB Postgres liên tục.
   - Kiến trúc Graph: Rời khỏi vòng lặp `while` cơ bản của Python và chuyển sang dùng _LangGraph_ cho phép rẽ nhánh, có trạng thái (Stateful) mạnh mẽ hơn.
