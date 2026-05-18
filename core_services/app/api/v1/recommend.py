from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List
from uuid import UUID

from app.core.database import get_db
from app.models import CV, Job
from app.schemas.job import JobResponse

router = APIRouter()


@router.get("/match-cv/{cv_id}", response_model=List[JobResponse])
def recommend_jobs_for_cv(cv_id: UUID, db: Session = Depends(get_db)):
    target_cv = db.query(CV).filter(CV.id == cv_id).first()
    if not target_cv or target_cv.embedding is None:
        raise HTTPException(
            status_code=400,
            detail="CV does not exist or has not been embedded yet.",
        )

    raw_query = text("""
        SELECT id FROM jobs
        WHERE embedding IS NOT NULL
        ORDER BY embedding <=> :cv_embed
        LIMIT 5
    """)

    result = db.execute(raw_query, {"cv_embed": target_cv.embedding}).fetchall()
    job_ids = [row[0] for row in result]

    return db.query(Job).filter(Job.id.in_(job_ids)).all()
