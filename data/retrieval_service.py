import os
import chromadb
from chromadb.utils import embedding_functions

# Đường dẫn tuyệt đối tới vector_db nằm cùng thư mục với file này
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vector_db")
COLLECTION_NAME = "vinwonders_knowledge_base"


def retrieve_info(query, n_results=3):
    """
    Tìm kiếm và truy xuất các đoạn văn bản liên quan nhất từ Vector DB.
    
    Tham số:
        query (str): Câu hỏi hoặc chuỗi tìm kiếm từ người dùng.
        n_results (int): Số lượng kết quả liên quan nhất cần trả về (Mặc định là 3, có thể chỉnh lên 5).
        
    Trả về:
        list: Danh sách các dict chứa nội dung văn bản (page_content) và thông tin nguồn (metadata).
    """
    if not os.path.exists(DB_PATH):
        print(f"[ERROR] Thu muc Vector DB khong ton tai tai: {DB_PATH}. Can chay Giai doan 3 truoc.")
        return []

    try:
        # Kết nối tới cơ sở dữ liệu ChromaDB đã lưu trên ổ đĩa
        client = chromadb.PersistentClient(path=DB_PATH)

        # Sử dụng lại mô hình Embedding đồng nhất với Giai đoạn 3
        sentence_transformer_ef = (
            embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="all-MiniLM-L6-v2"
            )
        )

        # Lấy collection lưu trữ tri thức VinWonders
        collection = client.get_collection(
            name=COLLECTION_NAME, embedding_function=sentence_transformer_ef
        )

        # Thực hiện truy vấn kiểm tra độ tương đồng vector
        results = collection.query(query_texts=[query], n_results=n_results)

        # Kiểm tra nếu không tìm thấy kết quả phù hợp
        if not results or not results["documents"] or len(results["documents"][0]) == 0:
            print(f"[WARNING] Khong tim thay thong tin lien quan cho truy van: '{query}'")
            return []

        # Cấu trúc lại dữ liệu trả về để Thành viên 4 dễ dàng đưa vào Prompt của LLM
        retrieved_chunks = []
        for idx in range(len(results["documents"][0])):
            chunk_data = {
                "page_content": results["documents"][0][idx],
                "metadata": results["metadatas"][0][idx],
                "distance": results["distances"][0][idx] if "distances" in results else None
            }
            retrieved_chunks.append(chunk_data)

        print(f"[SUCCESS] Da truy xuat thanh cong {len(retrieved_chunks)} doan thong tin phu hop.")
        return retrieved_chunks

    except Exception as e:
        print(f"[ERROR] Loi trong qua trình truy xuat du lieu: {str(e)}")
        return []


if __name__ == "__main__":
    # Phần mã nguồn này dùng để chạy thử nghiệm độc lập hàm truy xuất
    test_query = "Quy định về việc mang đồ ăn vào công viên nước như thế nào"
    
    print(f"[INFO] Chay thu nghiem ham retrieve_info voi cau hoi: '{test_query}'")
    
    # Thiết lập lấy 3 đoạn văn bản liên quan nhất (có thể đổi thành 4 hoặc 5 tùy thuộc yêu cầu tối ưu Prompt)
    search_results = retrieve_info(query=test_query, n_results=3)
    
    print("\n--- KET QUA DUOC TRUY XUAT DE CHUYEN CHO THANH VIEN 4 ---")
    for i, res in enumerate(search_results):
        print(f"\n[Doan thong tin {i+1}]")
        print(f"Noi dung: {res['page_content']}")
        print(f"Nguon: {res['metadata'].get('source_title')} | URL/Duong dan: {res['metadata'].get('source_url_or_path')}")
        print(f"Do sai lech Vector (Distance): {res['distance']}")