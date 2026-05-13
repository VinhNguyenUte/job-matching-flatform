from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.job import Job
from app.schemas.job import JobResponse

router = APIRouter()

@router.get("/", response_model=list[JobResponse])
def get_jobs(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    jobs = db.query(Job).order_by(Job.created_at.desc()).offset(skip).limit(limit).all()
    return jobs

@router.get("/search")
def search_jobs(q: str = "", db: Session = Depends(get_db)):
    jobs = db.query(Job).filter(
        Job.title.ilike(f"%{q}%") | Job.company.ilike(f"%{q}%")
    ).limit(20).all()
    return jobs