import json
import os
import uuid
from datetime import datetime, timezone
from typing import List, Optional
from google import genai
from google.genai import types
from PIL import Image
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import Json

load_dotenv()
# Hỗ trợ tự động tìm và nạp file .env ở thư mục gốc của dự án nếu chạy từ Read_CV
parent_env = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
if os.path.exists(parent_env):
    load_dotenv(parent_env)


# ---------------------------------------------------------------------------
# Pydantic schemas – dùng để cấu trúc phản hồi từ Gemini
# ---------------------------------------------------------------------------

class Experience(BaseModel):
    company: str = Field(description="Tên công ty hoặc tổ chức")
    role: str = Field(description="Vị trí, chức vụ làm việc")
    duration: str = Field(description="Thời gian làm việc, ví dụ: 05/2024 - Hiện tại")
    description: Optional[str] = Field(description="Mô tả ngắn gọn công việc hoặc dự án đã làm")


class Education(BaseModel):
    school: str = Field(description="Tên trường học hoặc trung tâm")
    major: str = Field(description="Chuyên ngành học")
    duration: str = Field(description="Thời gian học")


class CVData(BaseModel):
    full_name: str = Field(description="Họ và tên đầy đủ của ứng viên")
    email: Optional[str] = Field(description="Địa chỉ email liên hệ")
    phone: Optional[str] = Field(description="Số điện thoại liên hệ")
    skills: List[str] = Field(description="Danh sách các kỹ năng (kỹ thuật, ngôn ngữ, mềm...)")
    experience: List[Experience] = Field(description="Danh sách kinh nghiệm làm việc")
    education: List[Education] = Field(description="Danh sách lịch sử học tập")
    summary: Optional[str] = Field(description="Tóm tắt ngắn gọn về mục tiêu nghề nghiệp hoặc giới thiệu bản thân")


# ---------------------------------------------------------------------------
# Kết nối PostgreSQL
# ---------------------------------------------------------------------------

def get_db_connection():
    """Tạo kết nối tới PostgreSQL từ biến môi trường."""
    # Hỗ trợ cả 2 bộ biến môi trường (của dự án gốc POSTGRES_* và của script cũ DB_*)
    host = os.environ.get("POSTGRES_HOST") or os.environ.get("DB_HOST") or "localhost"
    port = os.environ.get("POSTGRES_PORT") or os.environ.get("DB_PORT") or 5432
    dbname = os.environ.get("POSTGRES_DB") or os.environ.get("DB_NAME") or "job_matching_db"
    user = os.environ.get("POSTGRES_USER") or os.environ.get("DB_USER") or "postgres"
    password = os.environ.get("POSTGRES_PASSWORD") or os.environ.get("DB_PASSWORD") or "postgres"
    
    try:
        port = int(port)
    except ValueError:
        port = 5432
        
    return psycopg2.connect(
        host=host,
        port=port,
        dbname=dbname,
        user=user,
        password=password,
    )


# ---------------------------------------------------------------------------
# Hàm chính
# ---------------------------------------------------------------------------

def extract_cv_to_db(
    image_paths: List[str],          # 1 hoặc nhiều ảnh CV
    user_id: str,                    # UUID của user trong hệ thống
    image_urls: List[str],           # URL công khai của từng ảnh (S3, CDN, …)
    title: Optional[str] = None,     # Tiêu đề CV (tuỳ chọn, tự sinh nếu để None)
    is_primary: bool = False,        # Đây có phải CV chính của user không?
    output_json_path: Optional[str] = None,  # Ghi thêm ra file JSON để debug
):
    # --- Kiểm tra API key ---
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("[LỖI] Không tìm thấy biến môi trường 'GEMINI_API_KEY'.")
        return

    client = genai.Client(api_key=api_key)

    # --- Mở tất cả ảnh ---
    cv_images = []
    for path in image_paths:
        if not os.path.exists(path):
            print(f"[LỖI] Không tìm thấy file ảnh: {path}")
            return
        try:
            cv_images.append(Image.open(path))
        except Exception as e:
            print(f"[LỖI] Không mở được ảnh {path}: {e}")
            return

    prompt = """
    Bạn là một chuyên gia tuyển dụng và hệ thống ATS chuyên nghiệp.
    Hãy phân tích ảnh CV được cung cấp, trích xuất chính xác tất cả các thông tin quan trọng.
    Nếu thông tin nào không có trong CV, hãy để giá trị null hoặc mảng rỗng.
    Tuyệt đối không tự bịa ra thông tin.
    """

    print("Đang phân tích CV bằng Gemini...")

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[*cv_images, prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=CVData,
                temperature=0.1,
            ),
        )

        json_text = response.text
        parsed: dict = json.loads(json_text)

    except Exception as e:
        print(f"[LỖI] Gọi Gemini API thất bại: {e}")
        return

    # --- Chuẩn bị raw_text (toàn bộ JSON thô dạng chuỗi để full-text search) ---
    raw_text = json.dumps(parsed, ensure_ascii=False)

    # --- Tiêu đề CV (fallback: tên ứng viên + ngày tạo) ---
    if not title:
        title = f"CV - {parsed.get('full_name', 'Không rõ')} - {datetime.now().strftime('%Y-%m-%d')}"

    # --- parsed_data: toàn bộ dữ liệu có cấu trúc, kèm image_urls ---
    parsed_data = {
        **parsed,
        "image_urls": image_urls,   # URL ảnh CV (1 hoặc nhiều trang)
    }

    now = datetime.now(timezone.utc)

    # --- Lưu vào DB ---
    # Bỏ trường 'id' khỏi SQL Insert vì trong Schema DB, 'id' là kiểu BigInteger AUTO-INCREMENT.
    # Nếu cố gắng chèn chuỗi UUID sẽ gây lỗi sai kiểu dữ liệu (InvalidTextRepresentation).
    insert_sql = """
        INSERT INTO public.cvs (
            user_id,
            title,
            raw_text,
            parsed_data,
            embedding,
            is_primary,
            created_at,
            updated_at
        ) VALUES (
            %s, %s, %s, %s,
            NULL,
            %s, %s, %s
        )
        RETURNING id;
    """

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(insert_sql, (
            user_id,
            title,
            raw_text,
            Json(parsed_data),
            is_primary,
            now,
            now,
        ))

        conn.commit()
        returned_id = cur.fetchone()[0]
        cur.close()
        conn.close()

        print(f"✅ Đã lưu vào DB thành công! ID bản ghi: {returned_id}")

    except Exception as e:
        print(f"[LỖI] Lưu vào DB thất bại: {e}")
        return

    # --- Ghi ra file JSON để debug (tuỳ chọn) ---
    if output_json_path:
        with open(output_json_path, "w", encoding="utf-8") as f:
            json.dump(parsed_data, f, ensure_ascii=False, indent=4)
        print(f"📄 Đã xuất file debug: {output_json_path}")

    return returned_id


# ---------------------------------------------------------------------------
# Chạy thử
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    extract_cv_to_db(
        image_paths=["cv_mau.jpg"],          # Thay bằng đường dẫn thật (nhiều trang: ["p1.jpg", "p2.jpg"])
        user_id="00000000-0000-0000-0000-000000000001",  # UUID user thật trong DB
        image_urls=[
            "https://your-storage.com/cvs/cv_mau.jpg",  # URL công khai ảnh CV
        ],
        title=None,          # Để None → tự sinh từ tên ứng viên
        is_primary=False,
        output_json_path="cv_extracted.json",  # Đặt None nếu không cần debug
    )