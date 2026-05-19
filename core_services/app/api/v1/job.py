from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.clients.ai_processing_client import ai_processing_client
from app.core.database import get_db
from app.models import Application, CV, Job, User
from app.schemas.job import JobIngestRequest, JobIngestResponse, JobResponse
from app.api.v1.auth import get_current_user

router = APIRouter()


@router.get("/search", response_model=List[JobResponse])
def search_jobs(
    q: str = Query(None, description="Keyword search by job title"),
    city: str = Query(None, description="Filter by city"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of jobs to return"),
    db: Session = Depends(get_db),
):
    query = db.query(Job)

    if q:
        query = query.filter(Job.title.ilike(f"%{q}%"))

    if city:
        query = query.join(Job.locations).filter(Job.locations.any(city=city))

    return query.limit(limit).all()


@router.get("/{job_id}", response_model=JobResponse)
def get_job_detail(job_id: UUID, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return job


@router.post("/{job_id}/apply", status_code=status.HTTP_201_CREATED)
def apply_to_job(
    job_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    existing_application = (
        db.query(Application)
        .filter(Application.job_id == job_id, Application.user_id == current_user.id)
        .first()
    )
    if existing_application:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already applied to this job.",
        )

    cv = (
        db.query(CV)
        .filter(CV.user_id == current_user.id)
        .order_by(CV.is_primary.desc())
        .first()
    )
    if not cv:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No CV found. Upload a CV before applying.",
        )

    application = Application(
        user_id=current_user.id,
        job_id=job.id,
        cv_id=cv.id,
        status="applied",
    )
    db.add(application)
    db.commit()
    db.refresh(application)

    return {
        "success": True,
        "message": "Your application was submitted successfully.",
        "application_id": application.id,
    }


@router.post("/preview")
async def preview_jobs(payload: list[JobIngestRequest]):
    return await ai_processing_client.preview_jobs([item.model_dump(mode="json") for item in payload])


@router.post("/ingest", response_model=JobIngestResponse)
async def ingest_jobs(payload: list[JobIngestRequest]):
    return await ai_processing_client.ingest_jobs([item.model_dump(mode="json") for item in payload])
