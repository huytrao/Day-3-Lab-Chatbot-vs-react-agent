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

## Tích hợp vào Agent (cho Thành viên 4)

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
