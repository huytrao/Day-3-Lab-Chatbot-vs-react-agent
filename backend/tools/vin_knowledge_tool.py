from typing import Any, Callable


def _load_retrieve_info() -> Callable[[str], Any] | None:
    candidates = (
        "data.retrieval_service.retrieve_info",
        "backend.retrieval_service.retrieve_info",
        "backend.retriever.retrieve_info",
        "src.retrieval_service.retrieve_info",
    )
    for dotted_path in candidates:
        module_name, function_name = dotted_path.rsplit(".", 1)
        try:
            module = __import__(module_name, fromlist=[function_name])
            retrieve_info = getattr(module, function_name)
            if callable(retrieve_info):
                return retrieve_info
        except Exception:
            continue
    return None


def _format_retrieval_result(result: Any) -> str:
    if not result:
        return ""
    if isinstance(result, str):
        return result
    if isinstance(result, list):
        chunks: list[str] = []
        for item in result[:3]:
            if isinstance(item, dict):
                content = item.get("page_content") or item.get("content") or str(item)
                chunks.append(str(content))
            else:
                chunks.append(str(item))
        return " ".join(chunks)
    return str(result)


def _mock_knowledge(query: str) -> str:
    text = query.lower()
    if any(keyword in text for keyword in ["be", "tre", "children", "5 tuoi", "choi gi", "tro gi"]):
        return "Tim thay thong tin phu hop: ho boi tre em, bai bien nhan tao, khu vui choi nhe, nha hang gia dinh."
    if any(keyword in text for keyword in ["mua", "nang", "thoi tiet"]):
        return "Tim thay thong tin phu hop: neu mua nen uu tien thuy cung, show trong nha va khu an uong; neu nang nen nghi trua trong nha."
    if any(keyword in text for keyword in ["an", "nha hang", "nghi chan"]):
        return "Tim thay thong tin phu hop: nha hang gia dinh, khu nghi chan co mai che, quan nuoc gan khu vui choi trong nha."
    return "Tim thay thong tin phu hop: cong vien nuoc, khu vui choi gia dinh, thuy cung, show bieu dien va lich trinh 1 ngay."


def search_vin_knowledge(query: str) -> str:
    """Search VinWonders/Vinpearl knowledge for a user query.

    Args:
        query: User question or search phrase, for example "tro choi cho be
            5 tuoi", "nha hang gia dinh", or "phuong an neu troi mua".

    Returns:
        Vietnamese text containing retrieved knowledge. The function tries to
        call Member 3's `retrieve_info(query)` when available. If importing or
        retrieval fails, it returns a built-in mock knowledge response. It never
        raises exceptions to callers.
    """
    safe_query = (query or "").strip()
    if not safe_query:
        return "Khong co cau truy van de tim kiem thong tin VinWonders."

    retrieve_info = _load_retrieve_info()
    if retrieve_info:
        try:
            result = _format_retrieval_result(retrieve_info(safe_query))
            if result:
                return f"Tim thay thong tin phu hop: {result}"
        except Exception:
            pass

    return _mock_knowledge(safe_query)
