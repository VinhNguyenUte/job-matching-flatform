from fastapi import FastAPI

from app.features.jd_ingestion.router import router as jd_ingestion_router
from app.features.cv_processing.router import router as cv_processing_router

app = FastAPI(title="JobMatch AI Processing", version="1.0.0")

app.include_router(jd_ingestion_router, prefix="/api/jobs", tags=["jd-ingestion"])
app.include_router(cv_processing_router, prefix="/api/cvs", tags=["cv-processing"])


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "ai_processing"}

