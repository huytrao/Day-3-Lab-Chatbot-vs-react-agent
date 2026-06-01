# Hướng dẫn sử dụng: VinWonders AI Advisor 🎢

Chào mừng bạn đến với hệ thống Trợ lý ảo AI của VinWonders (phiên bản ReAct Agent). Tài liệu này sẽ hướng dẫn bạn cách cài đặt, khởi động và sử dụng giao diện web của hệ thống.

---

## 🚀 1. Cài đặt và Khởi động

Để trang web hoạt động với đầy đủ tính năng AI, bạn cần khởi chạy hệ thống Backend trước khi mở UI.

### Cài đặt môi trường
Truy cập terminal tại thư mục gốc của dự án và cài đặt các thư viện cần thiết:
```bash
pip install -r requirements.txt
```

### Khởi động Backend (FastAPI)
Mở terminal và chạy lệnh sau để khởi động máy chủ API nội bộ (Backend sẽ mặc định chạy ở cổng 8000):
```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

### Mở Giao diện Frontend (Giao diện người dùng)
Sau khi Backend báo khởi chạy thành công, bạn có 2 cách để mở giao diện:
- **Cách 1**: Mở trực tiếp file `demo.html` bằng trình duyệt web (Chrome, Edge, Cốc Cốc,...).
- **Cách 2**: Mở file `demo.html` trong VS Code và sử dụng **Live Server**.

---

## 📖 2. Hướng dẫn sử dụng Giao diện Web

### Bước 1: Màn hình Khởi tạo Thông tin (Init User)
Ngay khi vừa mở trang web, hệ thống sẽ hiển thị một biểu mẫu yêu cầu cung cấp thông tin để **cá nhân hóa trải nghiệm** tư vấn của AI:
- **Tên của quý khách:** Giúp AI xưng hô thân thiện và tự nhiên hơn.
- **Mức ngân sách dự kiến:** Ưu tiên Tiết kiệm hay Cao cấp.
- **Số người tham gia chuyến đi:** Hỗ trợ tính toán giá vé.
- **Trẻ em đi cùng:** Để AI tự động lọc và gợi ý các trò chơi nhẹ nhàng, an toàn cho trẻ em.
- **Sở thích / Yêu cầu đặc biệt:** Ví dụ như "Thích cảm giác mạnh" hoặc "Không thích đi bộ".

👉 *Sau khi điền đủ thông tin, hãy nhấn nút Bắt đầu để vào giao diện chat.*

![Màn hình Khởi tạo thông tin](images/setup_screen.png)

### Bước 2: Trải nghiệm Giao diện Chat
Thành công khởi tạo, bạn sẽ được chuyển đến giao diện chat chính thức. AI Advisor sẽ gửi một tin nhắn chào mừng, tóm tắt lại các yêu cầu cá nhân hóa vừa được bạn nhập vào.

![Giao diện Chat](images/chat_screen.png)

**Một số mẫu câu hỏi bạn có thể thử nghiệm độ thông minh của ReAct Agent:**
- 🌤️ "Thời tiết cuối tuần này ở VinWonders có thích hợp để đi chơi nước không?" (Agent sẽ kích hoạt tool gọi API Thời tiết).
- 💰 "Tính giúp mình chi phí đi 2 người lớn và 1 trẻ em theo ngân sách tiết kiệm nhé." (Agent sẽ dùng tool máy tính giá vé chuẩn xác 100%, không dự đoán sai).
- 🗺️ "Sắp xếp cho mình một lịch trình vui chơi trong ngày nhưng ít phải đi bộ." (Agent sẽ kết hợp Vector DB để chọn lọc trò chơi theo ngữ cảnh).

### ✨ Các tính năng kỹ thuật nổi bật
- **Lưu lịch sử liền mạch:** Hệ thống được nối với Backend Database. Nếu bạn vô tình làm mới (F5) trang web, lịch sử đoạn chat vẫn được lưu giữ đầy đủ theo Session.
- **Tư duy đa bước tự động (ReAct Loop):** AI sử dụng suy luận *Thought -> Action -> Observation* trực tiếp ở Backend để lấy dữ liệu thực tế trước khi hiển thị câu trả lời cuối cùng.
