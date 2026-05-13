from celery import shared_task
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.cv import CV
from app.tasks.recommendation_tasks import recommend_jobs_for_cv 
from app.utils.minio_client import minio_client
import google.generativeai as genai
from app.core.config import settings
import json
from datetime import datetime
import traceback

genai.configure(api_key=settings.GEMINI_API_KEY)

@shared_task(name="process_cv_task", bind=True, max_retries=3)
def process_cv_task(self, cv_id: int):
    db: Session = SessionLocal()
    try:
        cv = db.query(CV).filter(CV.id == cv_id).first()
        if not cv:
            return {"status": "failed", "reason": "CV not found"}

        cv.status = "processing"
        cv.match_score = 0
        db.commit()

        print(f"🔄 Processing CV {cv_id} - {cv.original_filename}")

        # 1. Tải file từ MinIO
        file_bytes = download_file_from_minio(cv.file_path)

        # 2. Parse CV bằng Gemini (Structured Output)
        parsed_data = parse_cv_with_gemini(file_bytes, cv.original_filename)

        # 3. Tạo Embedding
        embedding_text = create_embedding_text(parsed_data)
        embedding = generate_embedding(embedding_text)

        # 4. Lưu kết quả
        cv.parsed_text = json.dumps(parsed_data, ensure_ascii=False)
        cv.entities = parsed_data
        cv.embedding = embedding
        cv.status = "success"
        cv.match_score = 85  # Sẽ tính lại sau khi match job

        db.commit()

        print(f"✅ CV {cv_id} processed successfully")

        # 5. Trigger Recommendation
        recommend_jobs_for_cv.delay(cv_id)

        return {
            "status": "success",
            "cv_id": cv_id,
            "entities_count": len(parsed_data.get("skills", [])) + len(parsed_data.get("experience", []))
        }

    except Exception as e:
        print(f"❌ Error processing CV {cv_id}: {e}")
        traceback.print_exc()
        
        if 'cv' in locals():
            cv.status = "failed"
            db.commit()
        
        # Retry nếu lỗi tạm thời
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))
        
        return {"status": "failed", "reason": str(e)}
    finally:
        db.close()


def download_file_from_minio(object_name: str) -> bytes:
    """Tải file từ MinIO"""
    try:
        response = minio_client.client.get_object(
            minio_client.bucket_name, 
            object_name
        )
        return response.read()
    except Exception as e:
        raise Exception(f"MinIO download failed: {e}")


def parse_cv_with_gemini(file_bytes: bytes, filename: str):
    """Parse CV bằng Gemini 1.5 Flash với prompt mạnh"""
    
    model = genai.GenerativeModel(
        model_name='gemini-1.5-flash',
        generation_config={
            "temperature": 0.1,
            "response_mime_type": "application/json",
        }
    )

    prompt = f"""
    Bạn là chuyên gia phân tích CV hàng đầu tại Việt Nam.
    Hãy trích xuất thông tin từ CV sau một cách chính xác và có cấu trúc.

    Yêu cầu:
    - Trả về JSON theo đúng schema bên dưới.
    - Nếu không có thông tin thì để mảng rỗng [] hoặc chuỗi rỗng "".
    - Skills và Experience phải chi tiết.
    - Hỗ trợ cả tiếng Việt và tiếng Anh.

    Schema JSON:
    {{
      "personal_info": {{
        "full_name": "",
        "email": "",
        "phone": "",
        "location": "",
        "linkedin": "",
        "github": ""
      }},
      "education": [
        {{
          "school": "",
          "degree": "",
          "major": "",
          "start_year": "",
          "end_year": ""
        }}
      ],
      "experience": [
        {{
          "company": "",
          "position": "",
          "start_date": "",
          "end_date": "",
          "description": ""
        }}
      ],
      "skills": ["Python", "Django", ...],
      "certifications": ["AWS Certified...", ...],
      "languages": ["English: Advanced", "Japanese: Intermediate"]
    }}

    CV File: {filename}
    """

    try:
        response = model.generate_content([
            prompt,
            {
                "mime_type": "application/pdf" if filename.lower().endswith('.pdf') else "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "data": file_bytes
            }
        ])

        # Parse JSON response
        result = json.loads(response.text)
        return result

    except Exception as e:
        print(f"Gemini parsing error: {e}")
        # Fallback: Trả về cấu trúc rỗng
        return {
            "personal_info": {"full_name": "", "email": "", "phone": ""},
            "education": [],
            "experience": [],
            "skills": [],
            "certifications": [],
            "languages": []
        }


def create_embedding_text(parsed_data: dict) -> str:
    """Tạo text để embedding"""
    text = f"""
    Tên: {parsed_data.get('personal_info', {}).get('full_name', '')}
    Vị trí: {', '.join([exp.get('position', '') for exp in parsed_data.get('experience', [])])}
    Kỹ năng: {', '.join(parsed_data.get('skills', []))}
    Học vấn: {', '.join([edu.get('degree', '') + ' ' + edu.get('major', '') for edu in parsed_data.get('education', [])])}
    """
    return text.strip()


def generate_embedding(text: str):
    """Tạo vector embedding"""
    try:
        result = genai.embed_content(
            model="models/text-embedding-004",
            content=text,
            task_type="retrieval_document"
        )
        return result['embedding']
    except Exception as e:
        print(f"Embedding error: {e}")
        return None  # PGVector sẽ handle null