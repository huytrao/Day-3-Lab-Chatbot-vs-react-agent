from typing import Any, Dict, List


def run_vinwonders_agent(
    user_message: str,
    user_profile: dict,
    chat_history: list,
) -> Dict[str, Any]:
    """
    Mock connector for the VinWonders Travel AI Agent.

    Later, the AI team can replace the body of this function with the real
    agent call while keeping the same input and output contract.
    """
    text = user_message.lower()
    preferences = user_profile.get("preferences", [])
    age_group = user_profile.get("age_group", "general")
    travel_group = user_profile.get("travel_group", "group")
    budget = user_profile.get("budget", "medium")
    priority = user_profile.get("priority", "")

    agent_trace = [
        {
            "type": "thought",
            "content": "User asks for VinWonders travel advice, combine profile, chat history, and demo knowledge.",
        },
        {
            "type": "action",
            "tool": "search_vinwonders_info",
            "parameters": {"query": user_message},
        },
        {
            "type": "observation",
            "content": "Demo data includes kid-friendly rides, water park options, weather fallback, dining, ticket ranges, and one-day itinerary.",
        },
    ]

    itinerary = [
        {
            "time": "09:00",
            "place": "Check-in",
            "description": "Vao cong, lay ban do khu vui choi va thong nhat diem hen cho ca nhom.",
        },
        {
            "time": "09:30",
            "place": "Khu vui choi nhe / ho boi tre em",
            "description": "Phu hop voi gia dinh, tre nho va khach muon han che di bo.",
        },
        {
            "time": "12:00",
            "place": "Nha hang gia dinh",
            "description": "An trua, nghi mat va nap nuoc truoc khi tiep tuc lich trinh.",
        },
        {
            "time": "14:00",
            "place": "Thuy cung / show trong nha",
            "description": "Phuong an tot khi troi nang gat hoac co mua.",
        },
        {
            "time": "16:00",
            "place": "Cong vien nuoc",
            "description": "Chon khu vuc nhe neu co tre em, tranh cac tro cam giac manh neu khong phu hop.",
        },
    ]

    if any(keyword in text for keyword in ["be", "bé", "tre", "trẻ", "5 tuoi", "5 tuổi", "children"]):
        reply = (
            "Voi be nho, ban nen uu tien ho boi tre em, bai bien nhan tao, khu vui choi nhe "
            "va cac show trong nha. Neu be khoang 5 tuoi, hay tranh tro cam giac manh, chia lich "
            "thanh cac chang ngan va nghi trua som. Profile cua ban cho thay nhom di la "
            f"{travel_group}, do tuoi {age_group}, nen minh de xuat lich trinh nhe va it di bo."
        )
    elif any(keyword in text for keyword in ["mua", "mưa", "nang", "nắng", "thoi tiet", "thời tiết"]):
        reply = (
            "Neu troi mua, hay chuyen sang thuy cung, show trong nha, khu am thuc va cac diem co mai che. "
            "Neu troi nang, nen vao cong som, choi ngoai troi truoc 10:30, nghi trua lau hon va de cong vien nuoc "
            "vao cuoi chieu. Voi uu tien "
            f"'{priority}', lich trinh nen giam di bo va tang cac diem nghi mat."
        )
    elif any(keyword in text for keyword in ["gia", "giá", "ve", "vé", "ticket"]):
        reply = (
            "Gia ve demo co the chia thanh 3 muc: tieu chuan, combo vui choi + am thuc, va goi gia dinh. "
            f"Voi ngan sach '{budget}', minh goi y chon ve tieu chuan neu chi di 1 ngay, sau do du tru them "
            "chi phi an trua, nuoc uong va do dung ca nhan. Day la du lieu demo, khong phai gia ban thuc te."
        )
    elif any(keyword in text for keyword in ["an", "ăn", "nha hang", "nhà hàng", "food"]):
        reply = (
            "Diem an uong nen uu tien nha hang gia dinh gan khu trung tam de de nghi ngoi va quay lai vui choi. "
            "Neu co tre em, chon mon de an, tranh xep hang gio cao diem va dat moc an trua khoang 11:30-12:00."
        )
    else:
        reply = (
            "Minh goi y lich trinh 1 ngay theo huong nhe: check-in som, choi khu phu hop voi so thich "
            f"{preferences or ['family friendly']}, nghi trua tai nha hang gia dinh, chuyen sang thuy cung/show trong nha "
            "luc nang nong, va ket thuc bang cong vien nuoc hoac khu check-in cuoi chieu."
        )

    return {
        "reply": reply,
        "agent_trace": agent_trace,
        "itinerary": itinerary,
    }
