from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.v1.auth import get_current_user
from app.clients.ai_processing_client import ai_processing_client
from app.core.database import get_db
from app.models import CV, User
from app.schemas.cv import CVCreate, CVResponse, CVUploadResponse

router = APIRouter()


@router.post("/upload", response_model=CVUploadResponse, status_code=201)
async def upload_user_cv(
    payload: CVCreate,
    current_user: User = Depends(get_current_user),
):
    ai_payload = {
        "user_id": str(current_user.id),
        "persist": True,
        "images": [
            {
                "url": str(payload.url),
                "mime_type": "image/jpeg",
            }
        ],
    }
    return await ai_processing_client.extract_cv(ai_payload)


@router.get("/{cv_id}", response_model=CVResponse)
def get_cv_detail(cv_id: UUID, db: Session = Depends(get_db)):
    cv_record = db.query(CV).filter(CV.id == cv_id).first()
    if not cv_record:
        raise HTTPException(status_code=404, detail="CV not found")
    return cv_record
