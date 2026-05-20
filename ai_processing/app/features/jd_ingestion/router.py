from fastapi import APIRouter

from app.common.schemas.job import JobParsedSchema
from app.features.jd_ingestion.schemas import IngestJobRequest, JobIngestResponse
from app.features.jd_ingestion.service import JDProcessingService

router = APIRouter()


@router.post("/preview", response_model=list[JobParsedSchema])
async def preview_jobs(payload: list[IngestJobRequest]):
    return await JDProcessingService.preview_jobs(payload)


@router.post("/ingest", response_model=JobIngestResponse)
async def ingest_jobs(payload: list[IngestJobRequest]):
    return await JDProcessingService.ingest_jobs(payload)
