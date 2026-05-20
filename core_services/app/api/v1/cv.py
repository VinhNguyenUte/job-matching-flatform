import uuid
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.v1.auth import get_current_user
from app.core.database import get_db
from app.models import CV, User
from app.schemas.cv import CVResponse, CVUploadQueuedResponse
from app.services.cloudinary_service import cloudinary_service
from app.services.rabbitmq_service import rabbitmq_service

router = APIRouter()


def _status_for(cv_record: CV) -> str:
    parsed_data = cv_record.parsed_data or {}
    return parsed_data.get("status") or ("completed" if cv_record.parsed_data else "processing")


def _validate_image(file: UploadFile):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CV images are accepted for this endpoint.",
        )


@router.post("/upload-images-smoke", status_code=status.HTTP_202_ACCEPTED)
async def upload_cv_images_smoke(
    user_id: str = Form("dev-user"),
    files: list[UploadFile] = File(...),
):
    if not files:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="At least one CV image is required.")

    for file in files:
        _validate_image(file)

    cv_urls: list[str] = []
    try:
        for file in files:
            file_bytes = await file.read()
            extension = (file.filename.rsplit(".", 1)[-1] if file.filename and "." in file.filename else "jpg").lower()
            object_name = f"smoke-tests/{user_id}/{uuid.uuid4()}.{extension}"
            cv_urls.append(
                await cloudinary_service.upload_file(
                    file_data=file_bytes,
                    object_name=object_name,
                    content_type=file.content_type or "image/jpeg",
                )
            )

        published = rabbitmq_service.publish_task(
            {
                "type": "cv_image_upload_smoke_test",
                "smoke_test": True,
                "user_id": user_id,
                "cv_urls": cv_urls,
            }
        )

        if not published:
            raise HTTPException(status_code=503, detail="Uploaded to Cloudinary, but RabbitMQ publish failed.")

        return {
            "success": True,
            "message": "Image uploaded to Cloudinary and smoke-test message published to RabbitMQ.",
            "user_id": user_id,
            "cv_urls": cv_urls,
            "queue": rabbitmq_service.queue_name,
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Smoke upload failed: {exc}") from exc


@router.post("/upload-images", response_model=CVUploadQueuedResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_cv_images(
    title: str = Form("My Resume"),
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not files:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="At least one CV image is required.")

    for file in files:
        _validate_image(file)

    cv_record = CV(
        user_id=current_user.id,
        title=title,
        raw_text=None,
        parsed_data={"status": "queued", "source": "image_upload"},
        embedding=None,
        is_primary=False,
    )
    db.add(cv_record)
    db.commit()
    db.refresh(cv_record)

    try:
        cv_urls: list[str] = []
        for file in files:
            file_bytes = await file.read()
            extension = (file.filename.rsplit(".", 1)[-1] if file.filename and "." in file.filename else "jpg").lower()
            object_name = f"cvs/{current_user.id}/{cv_record.id}/{uuid.uuid4()}.{extension}"
            cv_urls.append(
                    await cloudinary_service.upload_file(
                    file_data=file_bytes,
                    object_name=object_name,
                    content_type=file.content_type or "image/jpeg",
                )
            )

        cv_record.parsed_data = {
            "status": "queued",
            "source": "image_upload",
            "cv_urls": cv_urls,
        }
        db.commit()

        published = rabbitmq_service.publish_task(
            {
                "type": "cv_image_uploaded",
                "cv_id": cv_record.id,
                "user_id": str(current_user.id),
                "cv_urls": cv_urls,
            }
        )
        if not published:
            cv_record.parsed_data = {
                **(cv_record.parsed_data or {}),
                "status": "queue_failed",
            }
            db.commit()
            raise HTTPException(status_code=503, detail="Could not enqueue CV processing task.")

        return CVUploadQueuedResponse(
            message="CV images were uploaded and queued for AI processing.",
            cv_id=cv_record.id,
            user_id=current_user.id,
            cv_urls=cv_urls,
        )
    except HTTPException:
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"CV upload failed: {exc}") from exc


@router.post("/upload", response_model=CVUploadQueuedResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_user_cv(
    title: str = Form("My Resume"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not file.filename or not file.filename.lower().endswith((".pdf", ".docx")):
        raise HTTPException(status_code=400, detail="Only .pdf or .docx CV files are accepted.")

    try:
        file_bytes = await file.read()
        unique_filename = f"cvs/{current_user.id}/{uuid.uuid4()}_{file.filename}"
        content_type = file.content_type or "application/octet-stream"
        storage_path = await cloudinary_service.upload_cv(file_bytes, unique_filename, content_type)

        new_cv = CV(
            user_id=current_user.id,
            title=title,
            raw_text=None,
            parsed_data={
                "status": "queued",
                "source": "document_upload",
                "cv_urls": [storage_path],
                "mime_types": [content_type],
            },
            embedding=None,
            is_primary=False,
        )
        db.add(new_cv)
        db.commit()
        db.refresh(new_cv)

        published = rabbitmq_service.publish_task(
            {
                "type": "cv_document_uploaded",
                "cv_id": new_cv.id,
                "user_id": str(current_user.id),
                "cv_urls": [storage_path],
                "cv_files": [
                    {
                        "url": storage_path,
                        "mime_type": content_type,
                    }
                ],
            }
        )
        if not published:
            new_cv.parsed_data = {
                **(new_cv.parsed_data or {}),
                "status": "queue_failed",
            }
            db.commit()
            raise HTTPException(status_code=503, detail="Could not enqueue CV processing task.")

        return CVUploadQueuedResponse(
            message="CV document was uploaded and queued for AI processing.",
            cv_id=new_cv.id,
            user_id=current_user.id,
            cv_urls=[storage_path],
        )
    except HTTPException:
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"CV upload failed: {exc}") from exc


@router.get("/{cv_id}", response_model=CVResponse)
def get_cv_detail(cv_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    cv_record = db.query(CV).filter(CV.id == cv_id, CV.user_id == current_user.id).first()
    if not cv_record:
        raise HTTPException(status_code=404, detail="CV was not found.")

    parsed_data = cv_record.parsed_data or {}
    cv_record.parsed_data = {**parsed_data, "status": _status_for(cv_record)}
    return cv_record

