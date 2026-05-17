import json
import os
from typing import List, Optional
from google import genai
from google.genai import types
from PIL import Image
from pydantic import BaseModel, Field
# 1. Thêm import dotenv ở đây
from dotenv import load_dotenv

# 2. Tự động load biến môi trường từ file .env khi ứng dụng khởi chạy
load_dotenv()

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

def extract_cv_to_json(image_path: str, output_json_path: str):
    # Lấy API key sau khi đã chạy load_dotenv()
    api_key = os.environ.get("GEMINI_API_KEY")
    
    if not api_key:
        print("[LỖI] Vẫn không tìm thấy biến môi trường 'GEMINI_API_KEY'.")
        print("Hãy chắc chắn bạn đã tạo file .env đúng định dạng và điền key.")
        return

    client = genai.Client(api_key=api_key)

    if not os.path.exists(image_path):
        print(f"Lỗi: Không tìm thấy file ảnh tại {image_path}")
        return
        
    try:
        cv_image = Image.open(image_path)
    except Exception as e:
        print(f"Lỗi khi mở ảnh: {e}")
        return

    prompt = """
    Bạn là một chuyên gia tuyển dụng và hệ thống ATS chuyên nghiệp. 
    Hãy phân tích ảnh CV được cung cấp, trích xuất chính xác tất cả các thông tin quan trọng.
    Nếu thông tin nào không có trong CV, hãy để giá trị null hoặc mảng rỗng, tuyệt đối không tự bịa ra thông tin.
    """

    print("Đang gửi dữ liệu và phân tích CV bằng Gemini...")
    
    try:
        response = client.models.generate_content(
            model='gemini-3-flash-preview', 
            contents=[cv_image, prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=CVData, 
                temperature=0.1 
            ),
        )

        json_text = response.text
        parsed_json = json.loads(json_text)

        with open(output_json_path, 'w', encoding='utf-8') as f:
            json.dump(parsed_json, f, ensure_ascii=False, indent=4)
            
        print(f"Thành công! Dữ liệu đã được xuất ra file: {output_json_path}")
        
    except Exception as e:
        print(f"Có lỗi xảy ra trong quá trình gọi API hoặc ghi file: {e}")

if __name__ == "__main__":
    # Nhớ chuẩn bị 1 file ảnh CV thật đặt vào đây để test nhé
    INPUT_IMAGE = "cv_mau.jpg"  # Thay bằng đường dẫn đến file ảnh CV của bạn
    OUTPUT_JSON = "cv_extracted.json"
    
    extract_cv_to_json(INPUT_IMAGE, OUTPUT_JSON)