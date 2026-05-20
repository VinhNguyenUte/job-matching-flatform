from fastapi import APIRouter

from app.features.cv_processing.schemas import CVExtractRequest, CVExtractResponse
from app.features.cv_processing.service import CVProcessingService

router = APIRouter()


@router.post("/extract", response_model=CVExtractResponse)
async def extract_cv(payload: CVExtractRequest):
    return await CVProcessingService.extract_cv(payload)
