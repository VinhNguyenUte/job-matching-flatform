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
    Sá»­ dá»¥ng toÃ¡n tá»­ hÃ¬nh há»c Cosine Distance (<=>) cá»§a pgvector 
    Ä‘á»ƒ tÃ¬m kiáº¿m cÃ¡c Job sÃ¡t nháº¥t vá»›i Vector nÄƒng lá»±c cá»§a CV.
    """
    target_cv = db.query(CV).filter(CV.id == cv_id).first()
    if not target_cv or target_cv.embedding is None:
        raise HTTPException(
            status_code=400, 
            detail="CV chÆ°a tá»“n táº¡i hoáº·c Ä‘ang trong quÃ¡ trÃ¬nh phÃ¢n tÃ¡ch Vector AI."
        )

    # Thá»±c hiá»‡n cÃ¢u lá»‡nh Native SQL truy váº¥n Vector khoáº£ng cÃ¡ch
    # ThÆ° viá»‡n pgvector há»— trá»£ toÃ¡n tá»­ <=> cho Cosine Distance
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
