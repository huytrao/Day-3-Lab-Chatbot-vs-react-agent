import os
import chromadb
from chromadb.utils import embedding_functions

# Đường dẫn tuyệt đối tới vector_db nằm cùng thư mục với file này
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vector_db")
COLLECTION_NAME = "vinwonders_knowledge_base"


def retrieve_info(query, n_results=3):
    """
    Hàm cung cấp giao diện truy xuất dữ liệu từ Vector DB cho Thanh vien 4.
    
    Tham số:
        query (str): Câu hỏi ngữ nghĩa từ phía khách hàng/người dùng.
        n_results (int): Số lượng phân đoạn kết quả trả về tối đa (mặc định là 3).
        
    Trả về:
        list: Mảng chứa các dict gồm 'page_content' và 'metadata'. Trả về mảng rỗng nếu lỗi.
    """
    if not os.path.exists(DB_PATH):
        print(f"[ERROR] Khong tim thay thu muc Vector DB tai: {DB_PATH}")
        return []

    try:
        client = chromadb.PersistentClient(path=DB_PATH)
        sentence_transformer_ef = (
            embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="all-MiniLM-L6-v2"
            )
        )

        collection = client.get_collection(
            name=COLLECTION_NAME, embedding_function=sentence_transformer_ef
        )

        results = collection.query(query_texts=[query], n_results=n_results)

        if not results or not results["documents"] or len(results["documents"][0]) == 0:
            return []

        retrieved_chunks = []
        for idx in range(len(results["documents"][0])):
            chunk_data = {
                "page_content": results["documents"][0][idx],
                "metadata": results["metadatas"][0][idx],
            }
            retrieved_chunks.append(chunk_data)

        return retrieved_chunks

    except Exception as e:
        print(f"[ERROR] Loi trong qua trinh thuc thi retrieve_info: {str(e)}")
        return []


if __name__ == "__main__":
    # Test nhanh kiểm tra tính khả dụng của hàm
    print("[INFO] Kiem tra thu nghiem truy xuat cua db_accessor.py...")
    test_query = "Thời gian mở cửa và giá vé"
    results = retrieve_info(test_query, n_results=2)
    print(f"[INFO] So luong doan trich xuat duoc: {len(results)}")