from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List
from app.core.database import get_db
from app.models import CV, Job
from app.schemas.job import JobResponse

router = APIRouter()

@router.get("/match-cv/{cv_id}", response_model=List[JobResponse])
def recommend_jobs_for_cv(cv_id: int, db: Session = Depends(get_db)):
    """
    Sử dụng toán tử hình học Cosine Distance (<=>) của pgvector 
    để tìm kiếm các Job sát nhất với Vector năng lực của CV.
    """
    target_cv = db.query(CV).filter(CV.id == cv_id).first()
    if not target_cv or target_cv.embedding is None:
        raise HTTPException(
            status_code=400, 
            detail="CV chưa tồn tại hoặc đang trong quá trình phân tách Vector AI."
        )

    # Thực hiện câu lệnh Native SQL truy vấn Vector khoảng cách
    # Thư viện pgvector hỗ trợ toán tử <=> cho Cosine Distance
    raw_query = text("""
        SELECT id FROM jobs 
        WHERE embedding IS NOT NULL 
        ORDER BY embedding <=> :cv_embed 
        LIMIT 5
    """)
    
    result = db.execute(raw_query, {"cv_embed": target_cv.embedding}).fetchall()
    job_ids = [row[0] for row in result]

    recommended_jobs = db.query(Job).filter(Job.id.in_(job_ids)).all()
    return recommended_jobs