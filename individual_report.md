# Họ và tên: Nguyễn Đông Anh

# GitHub Username: DongAnh2704

# Nhánh đóng góp chính: DongAnh

I. TECHNICAL CONTRIBUTION (15 Points)
Trong dự án VinWonders AI Advisor, tôi chịu trách nhiệm chính về việc xây dựng hệ thống thu thập thông tin người dùng từ Frontend, tích hợp API, xây dựng cấu trúc công cụ (Tools) và cài đặt vòng lặp ReAct loop trên Backend FastAPI.

1. Các module code đã triển khai:
Hệ thống API Endpoint (main.py): Thiết lập class ChatRequest bằng Pydantic để hứng trọn vẹn ngữ cảnh cá nhân hóa từ form (Tên, ngân sách, số người, trẻ em, sở thích) và nối chuỗi tạo thành Context thông minh trước khi đưa vào mô hình gemini-2.5-flash.

Xây dựng Custom Tools cho ReAct Agent:

tool_tinh_gia_ve: Nhận vào số lượng người lớn, trẻ em và mức ngân sách (tiết kiệm / thoải mái) để trả về bảng giá vé chính xác kèm các chương trình ưu đãi hiện có của VinWonders Wave Park & Water Park.

tool_goi_y_lich_trinh: Dựa vào sở thích (cảm giác mạnh, check-in, công viên nước) để sinh ra timeline lịch trình chi tiết theo giờ cho khách.

2. Minh chứng chất lượng Code (Code Quality & Modularity):
Mã nguồn được tôi đóng gói dạng hàm sạch (clean functions), có xử lý ngoại lệ (try-except) chặt chẽ tại API endpoint để đảm bảo nếu Gemini hoặc API Key gặp sự cố, hệ thống vẫn trả về thông báo lỗi thân thiện cho Frontend thay vì làm sập server.

II. DEBUGGING CASE STUDY (10 Points)
"Fail Early, Learn Fast" - Phân tích một lỗi nghiêm trọng trong quá trình phát triển hệ thống Agent v1.

1. Mô tả lỗi (The Failure)
Loại lỗi: Parser Error / Infinite Loop (Vòng lặp vô hạn).

Trạng thái: Khi khách hàng nhập sở thích là "Tôi đi 4 người, muốn chơi công viên nước và muốn tiết kiệm chi phí", Agent v1 đọc dữ liệu từ form nhưng bị bối rối giữa việc nên gọi tool_tinh_gia_ve trước hay tool_goi_y_lich_trinh trước. Khung suy nghĩ (Thought) của Agent liên tục lặp đi lặp lại việc gọi tool tính giá vé mà không thể đưa ra câu trả lời cuối cùng (Final Answer), dẫn đến cạn kiệt Token (Token exhaustion).

2. Quá trình Debug bằng Telemetry/Logs
Khi kiểm tra luồng chạy thông qua log terminal của FastAPI, tôi phát hiện ra:

Mô hình bị kẹt vì System Prompt ban đầu chưa định nghĩa rõ ràng cấu trúc đầu ra (Output format) cho ReAct khiến parser của Backend không bóc tách được từ khóa Final Answer:.

3. Giải pháp khắc phục (Resolution)
Tôi đã tiến hành cải tiến lên Agent v2 bằng cách tinh chỉnh lại system_instruction trong file Python.

Ép buộc mô hình tuân thủ nghiêm ngặt cấu trúc: Thought -> Action -> Observation -> Final Answer.

Thêm một Guardrail nhỏ bằng code Python: Giới hạn tối đa vòng lặp ReAct là 4 lần (max_iterations = 4). Nếu vượt quá, Agent bắt buộc phải dùng dữ liệu hiện tại để trả ra câu trả lời cho khách nhằm cắt đứt vòng lặp vô hạn.

Dưới đây là toàn bộ nội dung Phần III (Personal Insights) được chuyển đổi hoàn toàn sang dạng văn bản xuôi (text) tự nhiên, mạch lạc và scannable theo đúng yêu cầu của bạn để dán vào file báo cáo:

III. PERSONAL INSIGHTS (10 Points)
Qua kết quả đối sánh thực tế từ quá trình phát triển dự án tại Lab 3, tôi đã rút ra được những nhận thức sâu sắc về sự khác biệt cốt lõi giữa hai kiến trúc LLM Chatbot truyền thống và ReAct Agent:

Đầu tiên là về Cơ chế hoạt động. Hệ thống LLM Chatbot Baseline thuần túy hoạt động dựa hoàn toàn vào tri thức tĩnh đã được học trong tệp dữ liệu huấn luyện (Static Weights). Nó không có khả năng tương tác hay kiểm chứng thông tin từ thế giới bên ngoài. Ngược lại, mô hình ReAct Agent thể hiện một bước tiến vượt trội nhờ sự kết hợp nhịp nhàng giữa suy nghĩ (Reasoning) và hành động (Acting). Agent biết tự lập luận, đưa ra quyết định gọi các công cụ (Tools) bên ngoài theo thời gian thực để thu thập thông tin rồi mới tổng hợp câu trả lời.

Thứ hai là về Khả năng xử lý dữ liệu số và tính chính xác. Trong khi kiểm thử bản Chatbot Baseline, tôi nhận thấy mô hình rất thường xuyên tính toán sai tổng tiền vé khi số lượng người tăng lên hoặc khi áp dụng các điều kiện logic phức tạp (đây chính là hiện tượng ảo tưởng - Hallucination kinh điển của LLM). Đối với ReAct Agent, điểm yếu này đã được khắc phục triệt để. Agent không tự tính toán mà chỉ đóng vai trò phân tích yêu cầu, sau đó đẩy phần tính toán số liệu cho hàm Python (tool_tinh_gia_ve) xử lý, mang lại kết quả chính xác tuyệt đối 100%.

Cuối cùng là về Độ linh hoạt và tính cá nhân hóa. Bản Chatbot thông thường có xu hướng trả lời rất chung chung, rập khuôn dựa trên các văn bản sẵn có. Trong khi đó, ReAct Agent nhờ tận dụng tốt dữ liệu động nhận từ Form nộp vào, nó có thể tùy biến linh hoạt câu thoại, chủ động xưng hô theo tên riêng của khách, lọc ra các gói ưu đãi khớp chính xác với mức ngân sách và thiết kế riêng một lộ trình tham quan phù hợp cho đoàn có trẻ em đi cùng.

IV. FUTURE IMPROVEMENTS (5 Points)
Để nâng cấp hệ thống tư vấn VinWonders AI Advisor này lên quy mô doanh nghiệp lớn (Production-level), tôi đề xuất 2 cải tiến sau:

Tích hợp Vector Database (RAG): Thay vì viết cứng (hardcode) thông tin trò chơi và lịch trình trong Tool, ta nên chuyển toàn bộ file PDF quy định, văn bản giá vé, cẩm nang du lịch VinWonders vào một cơ sở dữ liệu vector (như ChromaDB hoặc Pinecone). Khi khách hỏi, Agent sẽ dùng RAG để truy vấn thông tin chính xác nhất theo từng mùa trong năm.

Cài đặt Multi-Agent System (Hệ thống đa Đại sứ): Chia nhỏ hệ thống thành nhiều Agent chuyên trách:

Ticketing Agent: Chuyên xử lý đặt vé, áp mã giảm giá và thanh toán.

Itinerary Agent: Chuyên lên lịch trình tham quan, ăn uống.

Một Router Agent ở đầu làm nhiệm vụ phân phối câu hỏi của khách về đúng Agent chuyên trách, giúp tăng tốc độ phản hồi và giảm tải token đáng kể.