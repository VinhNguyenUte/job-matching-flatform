from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
import uuid

from app.core.database import get_db
from app.models.domain import CV, User
from app.schemas.cv import CVResponse, CVCreate
from app.services.minio_service import minio_service
from app.services.rabbitmq_service import rabbitmq_service
from app.api.v1.auth import get_current_user

router = APIRouter()

@router.post("/upload", response_model=CVResponse, status_code=201)
async def upload_user_cv(
    title: str = Form("My Resume"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Kiểm tra định dạng file sinh viên / ứng viên
    if not file.filename.endswith(('.pdf', '.docx')):
        raise HTTPException(status_code=400, detail="Hệ thống chỉ chấp nhận file .pdf hoặc .docx")

    # MOCK_USER: Lấy user đầu tiên trong DB để test (Vì User.id sử dụng UUID)
    current_user = db.query(User).first()
    if not current_user:
        raise HTTPException(status_code=404, detail="Cần tạo mock user bằng UUID trong DB trước.")

    try:
        file_bytes = await file.read()
        unique_filename = f"cvs/{current_user.id}/{uuid.uuid4()}_{file.filename}"
        storage_path = minio_service.upload_cv(file_bytes, unique_filename, file.content_type)
        # 2. Ghi nhận thông tin thực thể vào PostgreSQL
        # Trường raw_text và embedding sẽ do Worker AI điền sau khi xử lý async
        new_cv = CV(
            user_id=current_user.id,
            title=title,
            raw_text=None,
            parsed_data=None,
            embedding=None,
            is_primary=False
        )
        db.add(new_cv)
        db.commit()
        db.refresh(new_cv)
        
        # 3. Kích hoạt Worker ở Tầng 4 xử lý AI thông qua RabbitMQ
        rabbitmq_service.publish_cv_uploaded(
            cv_id=new_cv.id, 
            user_id=current_user.id, 
            storage_path=storage_path
        )
        
        # Inject tạm status để khớp schema response
        new_cv.status = "processing"
        return new_cv

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Lỗi hệ thống: {str(e)}")

@router.get("/{cv_id}", response_model=CVResponse)
def get_cv_detail(cv_id: int, db: Session = Depends(get_db)):
    cv_record = db.query(CV).filter(CV.id == cv_id).first()
    if not cv_record:
        raise HTTPException(status_code=404, detail="Không tìm thấy bản ghi CV")
    
    cv_record.status = "completed" if cv_record.parsed_data else "processing"
    return cv_record