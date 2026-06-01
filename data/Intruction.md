# Hướng dẫn chạy thử Data Pipeline VinWonders

## Yêu cầu môi trường

- Python 3.12+
- Virtual environment đã kích hoạt

---

## Bước 0 — Cài đặt thư viện còn thiếu

Kiểm tra nhanh: hai thư viện `chromadb` và `sentence-transformers` **chưa được cài** trong venv hiện tại.

```bash
# Kích hoạt venv (chạy từ thư mục gốc project)
.\venv\Scripts\activate

# Cài các thư viện còn thiếu
pip install chromadb sentence-transformers
```

> Lưu ý: `sentence-transformers` nặng ~500MB do tải model `all-MiniLM-L6-v2` lần đầu. Cần kết nối internet.

Kiểm tra lại sau khi cài:

```bash
pip show chromadb sentence-transformers
```

---

## Bước 1 — Chạy Crawler (Thu thập dữ liệu)

```bash
# Đứng từ thư mục gốc project
python data/crawler.py
```

**Kết quả mong đợi:**

```
[INFO] Dang cao du lieu tu URL: https://vinwonders.com/vi/bai-viet-huong-dan-vui-choi/
[INFO] Dang cao du lieu tu URL: https://vinwonders.com/vi/ve-tham-quan/
...
[SUCCESS] Da luu X nguon du lieu vao file: data/raw_data.json
```

**Kiểm tra output:**

```bash
# Xem file JSON tạo ra (Windows PowerShell)
Get-Content data\raw_data.json | python -m json.tool | Select-Object -First 40
```

> Nếu một số URL trả về lỗi HTTP (403/404), bình thường — VinWonders có thể chặn crawler.
> Miễn file `raw_data.json` được tạo ra với ít nhất 1 nguồn là thành công.

**Nếu có file PDF bảng giá:** đặt vào thư mục `data/` với tên:
- `bang_gia_ve_vinwonders.pdf`
- `quy_dinh_cong_vien_nuoc.pdf`

rồi chạy lại `crawler.py` — script sẽ tự nhận.

---

## Bước 2 — Chạy Ingest (Nhúng vào Vector DB)

```bash
python data/ingest.py
```

**Kết quả mong đợi:**

```
[INFO] Bat dau qua trinh ingest tu file: .../data/raw_data.json
[INFO] Dang khoi tao mo hinh Embedding (all-MiniLM-L6-v2)...
[INFO] Dang nap XX doan vao ChromaDB tai '.../data/vector_db'...
[INFO] Da nap thanh cong lô du lieu tu 0 den XX
[SUCCESS] Hoan thanh qua trinh ingest vao: .../data/vector_db
```

**Kiểm tra thư mục vector DB tạo ra:**

```bash
# Kiểm tra thư mục vector_db đã tồn tại
Test-Path data\vector_db
# Kết quả: True

# Xem cấu trúc bên trong
Get-ChildItem data\vector_db -Recurse | Select-Object Name, Length
```

**Thông số chunk hiện tại:**
| Tham số | Giá trị |
|---------|---------|
| `chunk_size` | 500 ký tự |
| `chunk_overlap` | 50 ký tự |
| Embedding model | `all-MiniLM-L6-v2` |
| Vector DB | ChromaDB (persistent local) |

---

## Bước 3 — Chạy thử hàm `retrieve_info()`

### Cách 1 — Chạy nhanh qua `db_accessor.py`

```bash
python data/db_accessor.py
```

Kết quả mong đợi:
```
[INFO] Kiem tra thu nghiem truy xuat cua db_accessor.py...
[INFO] So luong doan trich xuat duoc: 2
```

### Cách 2 — Test trực tiếp trong Python REPL

```bash
python
```

```python
import sys
sys.path.insert(0, "data")
from db_accessor import retrieve_info

# Test query 1 — Giá vé
results = retrieve_info("giá vé vào cửa VinWonders Water Park")
for i, r in enumerate(results):
    print(f"\n--- Chunk {i+1} ---")
    print(r["page_content"][:300])
    print(f"Nguon: {r['metadata'].get('source_title')}")

# Test query 2 — Quy định
results = retrieve_info("quy định mang đồ ăn vào công viên nước")
for i, r in enumerate(results):
    print(f"\n--- Chunk {i+1} ---")
    print(r["page_content"][:300])
```

### Cách 3 — Chạy `retrieval_service.py` với logging đầy đủ

```bash
python data/retrieval_service.py
```

---

## Kiểm tra chất lượng RAG (Tiêu chí đề bài)

Chạy 3 query kiểm tra sau, mỗi query phải trả về **3 chunks có nội dung liên quan**:

```python
from db_accessor import retrieve_info

test_queries = [
    "giá vé người lớn VinWonders Wave Park",
    "quy định mang đồ ăn vào công viên nước",
    "thời gian mở cửa VinWonders",
]

for q in test_queries:
    results = retrieve_info(q, n_results=3)
    print(f"\nQuery: {q}")
    print(f"So chunks tra ve: {len(results)}")
    for i, r in enumerate(results):
        print(f"  [{i+1}] {r['page_content'][:100]}...")
```

**Đạt yêu cầu khi:** mỗi query trả về đúng 3 chunks, nội dung chunk liên quan trực tiếp đến câu hỏi.

---

## Xử lý lỗi thường gặp

| Lỗi | Nguyên nhân | Cách sửa |
|-----|-------------|----------|
| `ModuleNotFoundError: chromadb` | Chưa cài | `pip install chromadb` |
| `ModuleNotFoundError: sentence_transformers` | Chưa cài | `pip install sentence-transformers` |
| `[ERROR] Khong tim thay thu muc Vector DB` | Chưa chạy ingest | Chạy `python data/ingest.py` trước |
| `[ERROR] Khong tim thay raw_data.json` | Chưa chạy crawler | Chạy `python data/crawler.py` trước |
| `HTTP 403` khi crawl | VinWonders chặn bot | Dùng file PDF thay thế hoặc copy nội dung thủ công vào JSON |
| `collection does not exist` | Tên collection sai | Đảm bảo `COLLECTION_NAME = "vinwonders_knowledge_base"` ở tất cả file |

---

## Thứ tự chạy tóm tắt

```
1. pip install chromadb sentence-transformers
2. python data/crawler.py        →  tạo data/raw_data.json
3. python data/ingest.py         →  tạo data/vector_db/
4. python data/db_accessor.py    →  kiểm tra retrieve_info() hoạt động
```
