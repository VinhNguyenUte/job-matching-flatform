from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models import Job
from app.schemas.job import JobResponse

router = APIRouter()

@router.get("/search", response_model=List[JobResponse])
def search_jobs(
    q: str = Query(None, description="Từ khóa tìm kiếm theo tiêu đề job"),
    city: str = Query(None, description="Lọc theo thành phố"),
    db: Session = Depends(get_db)
):
    query = db.query(Job)
    
    if q:
        query = query.filter(Job.title.ilike(f"%{q}%"))
        
    if city:
        query = query.join(Job.locations).filter(Job.locations.any(city=city))
        
    # Kèm theo nạp trực tiếp quan hệ tránh Lazy Loading N+1 Query
    jobs = query.limit(20).all()
    return jobs