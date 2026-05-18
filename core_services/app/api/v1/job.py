from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List

from app.clients.ai_processing_client import ai_processing_client
from app.core.database import get_db
from app.models import Job
from app.schemas.job import JobIngestRequest, JobIngestResponse, JobResponse

router = APIRouter()


@router.get("/search", response_model=List[JobResponse])
def search_jobs(
    q: str = Query(None, description="Keyword search by job title"),
    city: str = Query(None, description="Filter by city"),
    db: Session = Depends(get_db),
):
    query = db.query(Job)

    if q:
        query = query.filter(Job.title.ilike(f"%{q}%"))

    if city:
        query = query.join(Job.locations).filter(Job.locations.any(city=city))

    return query.limit(20).all()


@router.post("/preview")
async def preview_jobs(payload: list[JobIngestRequest]):
    return await ai_processing_client.preview_jobs([item.model_dump(mode="json") for item in payload])


@router.post("/ingest", response_model=JobIngestResponse)
async def ingest_jobs(payload: list[JobIngestRequest]):
    return await ai_processing_client.ingest_jobs([item.model_dump(mode="json") for item in payload])
