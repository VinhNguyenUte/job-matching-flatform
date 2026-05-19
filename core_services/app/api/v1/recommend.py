from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import CV, Job
from app.schemas.job import JobRecommendationResponse

router = APIRouter()


def _vector_literal(value) -> str:
    return "[" + ",".join(str(float(item)) for item in value) + "]"


@router.get("/match-cv/{cv_id}", response_model=List[JobRecommendationResponse])
def recommend_jobs_for_cv(
    cv_id: UUID,
    limit: int = Query(5, ge=1, le=50),
    db: Session = Depends(get_db),
):
    target_cv = db.query(CV).filter(CV.id == cv_id).first()
    if not target_cv or target_cv.embedding is None:
        raise HTTPException(
            status_code=400,
            detail="CV does not exist or has not been embedded yet.",
        )

    raw_query = text("""
        SELECT
            id,
            1 - (embedding <=> CAST(:cv_embed AS vector)) AS match_score
        FROM jobs
        WHERE embedding IS NOT NULL
          AND COALESCE(status, 'active') = 'active'
        ORDER BY embedding <=> CAST(:cv_embed AS vector)
        LIMIT :limit
    """)

    matches = db.execute(
        raw_query,
        {
            "cv_embed": _vector_literal(target_cv.embedding),
            "limit": limit,
        },
    ).mappings().all()
    if not matches:
        return []

    score_by_job_id = {row["id"]: float(row["match_score"]) for row in matches}
    job_ids = list(score_by_job_id.keys())
    jobs = db.query(Job).filter(Job.id.in_(job_ids)).all()
    job_by_id = {job.id: job for job in jobs}

    recommendations = []
    for job_id in job_ids:
        job = job_by_id.get(job_id)
        if not job:
            continue
        job.match_score = score_by_job_id[job_id]
        recommendations.append(job)

    return recommendations
