# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: [Điền tên của bạn]
- **Student ID**: [Điền MSSV]
- **Role**: Thành viên 2 - Backend API & Database (FastAPI/Postgres)
- **Date**: [Điền ngày tháng]

---

## I. Technical Contribution (15 Points)

Là người đảm nhiệm vị trí Backend API & Database, tôi đóng vai trò "người điều phối giao thông", đảm bảo hệ thống lưu trữ dữ liệu người dùng chuẩn xác, duy trì lịch sử phiên chat và cung cấp tốc độ phản hồi nội bộ cực thấp so với thời gian suy luận của AI (< 50ms). Tôi đã thiết lập cầu nối ổn định giữa giao diện (Frontend) và luồng xử lý ReAct Agent.

- **Modules Implemented**: 
  - `backend/main.py`: Khởi tạo ứng dụng FastAPI, cấu hình Middleware xử lý CORS giúp Frontend ở cross-origin gọi API không bị gián đoạn hay dính lỗi bảo mật.
  - `backend/database.py` & `backend/schemas.py`: Thiết kế CSDL chuẩn hóa (sử dụng SQLAlchemy) với các model/bảng chính: `User` (lưu profile, khảo sát ban đầu), `Session` (quản lý phiên chat), và `Message` (lưu trữ từng lượt hội thoại của người dùng và AI).
  - `backend/crud.py`: Viết các logic truy vấn (CRUD operations) xử lý tương tác lấy/thêm dữ liệu nhanh vào Database.

- **Code Highlights**:
  - API `POST /api/init_user`: Khởi tạo User mới, tiếp nhận và lưu trữ thông tin độ tuổi, sở thích khảo sát từ giao diện vào DB.
  - API `GET /api/history/{session_id}`: Trích xuất lịch sử hội thoại trước đó. Điều này giúp hệ thống lưu trữ trạng thái người dùng (Stateful), do vậy Frontend có hiện tượng F5 (reload) lại trang cũng sẽ không bị mất lịch sử chat.
  - API `POST /api/chat`: Điểm kết nối trung tâm - tiếp nhận JSON request (`{"user_id": "123", "session_id": "abc", "text": "Có trò gì cho bé 5 tuổi?"}`). Logic sẽ gộp lịch sử chat lấy ra từ bảng Message, thông tin User từ DB kết hợp với câu hỏi mới -> Ném vào `run_react_loop` của Agent xử lý -> Nhận lại `Final Answer` text -> Bổ sung đáp án vào bảng Message -> Trả Result JSON về cho Frontend theo chuẩn.

- **Documentation**: 
  - Việc đưa Profile người dùng làm dữ liệu ngữ cảnh (Context Injection) được thực hiện ở Backend trước khi chuyển sang cho Agent. Module giúp tách biệt vai trò tổ chức trạng thái API với luồng logic LLM, đảm bảo mã nguồn sáng sủa.

---

## II. Debugging Case Study (10 Points)

*Analyze a specific failure event you encountered during the lab using the logging system.*

- **Problem Description**: 
  Agent gặp hiện tượng bị quá tải giới hạn token (Max Token Exceeded/OOM) sau khi người dùng trò chuyện kéo dài liên tục trên 6 lượt. Request bị treo sau đó Backend báo lỗi 500 do API model gọi thất bại không sinh ra được text (Crash phía LLM provider).
- **Log Source**: 
  Dựa trên log ghi nhận từ hệ thống (FastAPI error trace):
  ```
  [ERROR] fastapi.exceptions: HTTPException 500: Prompt length exceeded context window size.
  [INFO] ReAct Loop - User 123 (Session abc): Received history length -> 6500 tokens.
  ```
- **Diagnosis**: 
  Lúc đầu, API `POST /api/chat` truy vấn *toàn bộ* lịch sử tin nhắn trong `Message Table` theo `session_id` và trực tiếp biến thành chuỗi (string) gắn vào input của Agent. Mỗi lượt ReAct Agent suy luận đều bao gồm các track "Thought, Action, Observation" rất dài và hệ thống có gắn cả knowledge text. Khi tịnh tiến lịch sử toàn bộ các câu hỏi dài, kích thước prompt đã vượt qua giới hạn độ dài của Model gây sập bộ nhớ.
- **Solution**: 
  Tôi đã cập nhật lại file `backend/crud.py` và tối ưu router `api/chat`. Tôi áp dụng kĩ thuật **Sliding Window (Cửa sổ trượt)** - thiết lập để Backend chỉ trích xuất **5 cặp hỏi-đáp gần nhất** từ DB để lưu thành mảng `chat_history` chuyển vào Agent. Lịch sử cũ hơn vẫn được lưu ở Database để xem lại trên UI nhưng bỏ qua khỏi ReAct Prompt. Vấn đề "quá tải context" được triệt tiêu hoàn toàn.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

*Reflect on the reasoning capability difference.*

1. **Reasoning**: 
   Dưới góc nhìn kiểm soát dữ liệu: Một Chatbot thông thường nhận một chuỗi text tĩnh từ DB và trả lời thẳng, thường dẫn đến ảo giác (ảo giá vé). Nhưng với ReAct Agent, khi tôi cung cấp Profile người dùng lấy từ DB (VD: Lập hồ sơ khách có trẻ nhỏ 5 tuổi), chuỗi `Thought` giúp ReAct chia nhỏ tư duy lập luận rõ rệt: "Khách có con nhỏ -> Phải tìm tool giá vé trẻ em/trò chơi cho trẻ sơ sinh -> Action". Khả năng quy nạp dữ liệu từ Backend thành hành động thực tế là điểm ăn đứt LLM thuần túy.
2. **Reliability**: 
   Dù thông minh nhưng ReAct Agent *kém ổn định* về thì giờ phản hồi. Tốc độ API trả về với Chatbot thuần có thể chỉ dưới 1-2 giây. Trong khi đó, Frontend nhiều lúc gặp Timeout do request POST đến `/api/chat` phải chờ ReAct Agent chạy vòng lặp suy luận đôi khi lên đến 15 giây. Khi quá nhiều `chat_history` bị nhiễu, ReAct thỉnh thoảng sẽ dự đoán sai tên Tool gây ra vòng lặp vô tận.
3. **Observation**: 
   Quan sát (Observation) chính là mấu chốt để Agent chốt kết luận. Tuy nhiên, nó bị phụ thuộc vào cách Backend bắt lỗi. Nếu tool từ chối trả kết quả sạch mà quăng ra một chuỗi "Timeout from Database" hay "500 Internal Error", Agent đôi lúc sẽ lấy lỗi đó làm nguyên liệu tư duy và thật thà trả về cho FE câu trả lời khuyên người dùng hãy "Fix DB Error", gây trải nghiệm UX rất tệ.

---

## IV. Future Improvements (5 Points)

*How would you scale this for a production-level AI agent system?*

Trải qua Lab này, nếu đưa dự án lên Production, tôi đánh giá kiến trúc CSDL và API nên được mở rộng:
- **Scalability (Mở rộng)**: Việc phải gọi DB (Postgres/SQLite) quá nhiều lần tại bảng `Message Table` theo từng câu chat mới sẽ làm sập Server khi có lượng truy cập lớn (Concurrent Users). Tôi sẽ sử dụng hệ thống **Redis Cache** để lưu tạm `Session History` trên RAM, cho phép truy xuất trong bộ nhớ nhanh hơn hàng trăm lần. Thêm hàng đợi (Message Queue như RabbitMQ/Celery) để giữ request khi lượng gọi ReAct Agent đổ dồn.
- **Safety (Bảo mật)**: Triển khai Middleware phân quyền **Rate Limiting** để chặn User F5 spam API hoặc DDoSing `/api/chat`, giúp bảo vệ chi phí token của LLM Provider.
- **Performance (Tốc độ)**: Nâng cấp luồng lưu lịch sử vào Vector Database. Thay vì dùng Cửa sổ trượt (Sliding Window) ngây ngô để bỏ bớt chat, ta có thể Search theo ngữ nghĩa: AI chỉ tự động truy vấn tìm lại những câu chat trong Database có độ trùng khớp với context hiện tại, tiết kiệm prompt token mà vẫn đáp ứng được ReAct dài hạn.
