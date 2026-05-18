from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
import uuid

from app.core.database import get_db
from app.models import CV, User
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
    # Kiá»ƒm tra Ä‘á»‹nh dáº¡ng file sinh viÃªn / á»©ng viÃªn
    if not file.filename.endswith(('.pdf', '.docx')):
        raise HTTPException(status_code=400, detail="Há»‡ thá»‘ng chá»‰ cháº¥p nháº­n file .pdf hoáº·c .docx")

    # MOCK_USER: Láº¥y user Ä‘áº§u tiÃªn trong DB Ä‘á»ƒ test (VÃ¬ User.id sá»­ dá»¥ng UUID)
    current_user = db.query(User).first()
    if not current_user:
        raise HTTPException(status_code=404, detail="Cáº§n táº¡o mock user báº±ng UUID trong DB trÆ°á»›c.")

    try:
        file_bytes = await file.read()
        unique_filename = f"cvs/{current_user.id}/{uuid.uuid4()}_{file.filename}"
        storage_path = minio_service.upload_cv(file_bytes, unique_filename, file.content_type)
        # 2. Ghi nháº­n thÃ´ng tin thá»±c thá»ƒ vÃ o PostgreSQL
        # TrÆ°á»ng raw_text vÃ  embedding sáº½ do Worker AI Ä‘iá»n sau khi xá»­ lÃ½ async
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
        
        # 3. KÃ­ch hoáº¡t Worker á»Ÿ Táº§ng 4 xá»­ lÃ½ AI thÃ´ng qua RabbitMQ
        rabbitmq_service.publish_cv_uploaded(
            cv_id=new_cv.id, 
            user_id=current_user.id, 
            storage_path=storage_path
        )
        
        # Inject táº¡m status Ä‘á»ƒ khá»›p schema response
        new_cv.status = "processing"
        return new_cv

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Lá»—i há»‡ thá»‘ng: {str(e)}")

@router.get("/{cv_id}", response_model=CVResponse)
def get_cv_detail(cv_id: int, db: Session = Depends(get_db)):
    cv_record = db.query(CV).filter(CV.id == cv_id).first()
    if not cv_record:
        raise HTTPException(status_code=404, detail="KhÃ´ng tÃ¬m tháº¥y báº£n ghi CV")
    
    cv_record.status = "completed" if cv_record.parsed_data else "processing"
    return cv_record
