import json
import os
import re
import chromadb
from chromadb.utils import embedding_functions
from langchain_text_splitters import RecursiveCharacterTextSplitter


def clean_text(text):
    """Làm sạch văn bản thô."""
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def run_ingestion(input_file, db_path, collection_name):
    """Đọc dữ liệu thô, làm sạch, tách đoạn, nhúng embedding và nạp vào DB."""
    print(f"[INFO] Bat dau qua trinh ingest tu file: {input_file}")

    if not os.path.exists(input_file):
        print(
            f"[ERROR] Khong tim thay {input_file}. Can chay file crawler.py truoc."
        )
        return

    try:
        with open(input_file, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
    except Exception as e:
        print(f"[ERROR] Khong the doc file JSON: {str(e)}")
        return

    # Khởi tạo bộ chia văn bản (Chunk size: 800, Overlap: 100)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        length_function=len,
        separators=["\n\n", "\n", " ", ""],
    )

    documents = []
    metadatas = []
    ids = []

    for item in raw_data:
        source_title = item.get("title", "No Title")
        source_url = item.get("source_url", item.get("source_path", "Unknown"))
        source_type = item.get("source_type", "Unknown")
        cleaned_content = clean_text(item.get("content", ""))

        if not cleaned_content:
            continue

        chunks = text_splitter.split_text(cleaned_content)

        for index, chunk_text in enumerate(chunks):
            documents.append(chunk_text)
            metadatas.append(
                {
                    "source_title": source_title,
                    "source_url_or_path": source_url,
                    "source_type": source_type,
                    "chunk_index": index,
                }
            )
            ids.append(
                f"{source_type}_{index}_{hash(source_url + str(index))}"
            )

    if not documents:
        print("[WARNING] Khong co doan van ban nao hop le de nap.")
        return

    # Khởi tạo Vector DB lưu trữ vật lý tại thư mục chỉ định
    os.makedirs(db_path, exist_ok=True)
    client = chromadb.PersistentClient(path=db_path)

    print("[INFO] Dang khoi tao mo hinh Embedding (all-MiniLM-L6-v2)...")
    sentence_transformer_ef = (
        embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
    )

    collection = client.get_or_create_collection(
        name=collection_name, embedding_function=sentence_transformer_ef
    )

    # Tiến hành nạp dữ liệu theo lô (Batch)
    batch_size = 100
    total_docs = len(documents)
    print(f"[INFO] Dang nap {total_docs} doan vao ChromaDB tại '{db_path}'...")

    for i in range(0, total_docs, batch_size):
        end_idx = min(i + batch_size, total_docs)
        try:
            collection.add(
                documents=documents[i:end_idx],
                metadatas=metadatas[i:end_idx],
                ids=ids[i:end_idx],
            )
            print(f"[INFO] Da nap thanh cong lô du lieu tu {i} den {end_idx}")
        except Exception as e:
            print(f"[ERROR] Loi tai lô du lieu tu {i} den {end_idx}: {str(e)}")

    print(f"[SUCCESS] Hoan thanh qua trinh ingest vao: {db_path}")


if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    run_ingestion(
        input_file=os.path.join(script_dir, "raw_data.json"),
        db_path=os.path.join(script_dir, "vector_db"),
        collection_name="vinwonders_knowledge_base",
    )