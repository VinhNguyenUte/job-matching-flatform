from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.utils.minio_client import minio_client
from app.models.cv import CV
from app.models.user import User
from app.schemas.cv import CVUploadResponse, CVResponse
from app.api.v1.auth import get_current_user
from app.tasks.cv_tasks import process_cv_task  # Sẽ làm sau

router = APIRouter()

@router.post("/upload", response_model=CVUploadResponse)
async def upload_cv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Kiểm tra định dạng file
    allowed_types = ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail="Only PDF and DOCX files are allowed"
        )

    # Upload lên MinIO
    try:
        file_path = minio_client.upload_cv(file, current_user.id)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to upload file to storage")

    # Lưu thông tin vào database
    cv = CV(
        user_id=current_user.id,
        file_path=file_path,
        original_filename=file.filename,
        status="pending"
    )
    
    db.add(cv)
    db.commit()
    db.refresh(cv)

    # Push task xử lý CV (Celery)
    process_cv_task.delay(cv.id)

    return CVUploadResponse(
        cv_id=cv.id,
        status="pending",
        message="CV uploaded successfully. Processing with AI..."
    )


@router.get("/my-cvs", response_model=list[CVResponse])
def get_my_cvs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    cvs = db.query(CV).filter(CV.user_id == current_user.id).order_by(CV.created_at.desc()).all()
    return cvs