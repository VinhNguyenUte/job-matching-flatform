from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.job import JobCatalogItem, JobIngestRequest, JobIngestResponse, JobParsedSchema
from app.services.jd_ingestion import JDIngestionService

router = APIRouter()
ingestion_router = APIRouter()


@router.get("/", response_model=list[JobCatalogItem])
async def get_jobs(skip: int = 0, limit: int = 50, db: AsyncSession = Depends(get_db)):
    return await JDIngestionService.list_jobs(session=db, skip=skip, limit=limit)


@router.get("/search", response_model=list[JobCatalogItem])
async def search_jobs(q: str = "", limit: int = 20, db: AsyncSession = Depends(get_db)):
    return await JDIngestionService.search_jobs(session=db, q=q, limit=limit)


@ingestion_router.post("/preview", response_model=list[JobParsedSchema])
async def preview_jobs(payload: list[JobIngestRequest]):
    return await JDIngestionService.preview_jobs(payload)


@ingestion_router.post("/ingest", response_model=JobIngestResponse)
async def ingest_jobs(payload: list[JobIngestRequest], db: AsyncSession = Depends(get_db)):
    return await JDIngestionService.ingest_jobs(payload, db)
