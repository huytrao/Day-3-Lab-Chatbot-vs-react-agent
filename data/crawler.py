import json
import os
from datetime import datetime
import pdfplumber
import requests
from bs4 import BeautifulSoup


def crawl_web_page(url):
    """Cào nội dung văn bản từ một URL VinWonders, ưu tiên khu vực nội dung chính."""
    print(f"[INFO] Dang cao du lieu tu URL: {url}")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")

            # Loại bỏ các phần không chứa nội dung hữu ích
            for tag in soup.find_all(["nav", "header", "footer", "script", "style", "aside"]):
                tag.decompose()

            title = "No Title"
            if soup.find("h1"):
                title = soup.find("h1").get_text(strip=True)
            elif soup.title and soup.title.string:
                title = soup.title.string.strip()

            # Ưu tiên lấy nội dung từ khu vực bài viết/article chính của VinWonders
            content_area = (
                soup.find("article")
                or soup.find(class_=lambda c: c and any(k in c for k in ["content", "article", "post", "entry", "main"]))
                or soup.find("main")
                or soup
            )

            # Lấy tất cả đoạn văn và heading có nội dung thực
            text_tags = content_area.find_all(["p", "h2", "h3", "h4", "li", "td", "th"])
            lines = []
            for tag in text_tags:
                text = tag.get_text(separator=" ", strip=True)
                if len(text) > 20:  # Bỏ qua các đoạn quá ngắn (menu, label)
                    lines.append(text)

            content = "\n".join(lines)

            if not content.strip():
                print(f"[WARNING] Khong trich xuat duoc noi dung chinh tu: {url}")
                return None

            return {
                "source_type": "web_page",
                "source_url": url,
                "collected_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "title": title,
                "content": content,
            }
        else:
            print(f"[ERROR] Loi HTTP {response.status_code} khi truy cap {url}")
            return None
    except Exception as e:
        print(f"[ERROR] Da xay ra loi khi cao URL {url}: {str(e)}")
        return None


def extract_pdf_data(pdf_path):
    """Trích xuất văn bản từ file PDF."""
    print(f"[INFO] Dang doc file PDF: {pdf_path}")
    if not os.path.exists(pdf_path):
        print(f"[WARNING] File PDF khong ton tai: {pdf_path}")
        return None

    try:
        full_text = []
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages):
                text = page.extract_text()
                if text:
                    full_text.append(f"--- Trang {i+1} ---\n{text}")

        return {
            "source_type": "pdf_file",
            "source_path": pdf_path,
            "collected_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "title": os.path.basename(pdf_path),
            "content": "\n\n".join(full_text),
        }
    except Exception as e:
        print(f"[ERROR] Loi khi doc file PDF {pdf_path}: {str(e)}")
        return None


def save_to_json(data, output_filename):
    """Lưu dữ liệu thô thu thập được vào file JSON."""
    os.makedirs(os.path.dirname(output_filename), exist_ok=True)
    try:
        with open(output_filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(
            f"[SUCCESS] Da luu {len(data)} nguon du lieu vao file: {output_filename}"
        )
    except Exception as e:
        print(f"[ERROR] Khong the luu file JSON: {str(e)}")


if __name__ == "__main__":
    all_collected_data = []

    # Danh sách URL VinWonders Wave Park & Water Park nhắm vào trang giá vé và quy định
    urls_to_crawl = [
        "https://vinwonders.com/vi/vinwonders-wave-park-water-park-price-regulations/",
        "https://vinwonders.com/vi/vinwonders-nha-trang-price-and-regulations/",
        "https://vinwonders.com/vi/vinwonders-phu-quoc-price-and-regulations/",
        "https://vinwonders.com/vi/vinwonders-nam-hoi-an-price-and-regulations/",
        "https://vinwonders.com/vi/diem-den/water-park/",
        "https://vinwonders.com/vi/wonderpedia/news/cong-vien-song-vinwonders-wave-park/",
        "https://vinwonders.com/vi/wonderpedia/news/kinh-nghiem-di-vinwonders-va-vinpearl-safari-phu-quoc-day-du-nhat/",
        "https://vinwonders.com/vi/bai-viet-du-lich/vinwonders-ha-noi/",
    ]

    # PDF đặt trong cùng thư mục data/
    script_dir = os.path.dirname(os.path.abspath(__file__))
    pdf_files_to_read = [
        os.path.join(script_dir, "bang_gia_ve_vinwonders.pdf"),
        os.path.join(script_dir, "quy_dinh_cong_vien_nuoc.pdf"),
    ]

    for url in urls_to_crawl:
        result = crawl_web_page(url)
        if result:
            all_collected_data.append(result)

    for pdf in pdf_files_to_read:
        if os.path.exists(pdf):
            result = extract_pdf_data(pdf)
            if result:
                all_collected_data.append(result)
        else:
            print(f"[INFO] Bo qua file {os.path.basename(pdf)} do file khong ton tai luc nay.")

    if all_collected_data:
        output_path = os.path.join(script_dir, "raw_data.json")
        save_to_json(all_collected_data, output_path)
    else:
        print("[WARNING] Khong co du lieu nao duoc thu thap.")