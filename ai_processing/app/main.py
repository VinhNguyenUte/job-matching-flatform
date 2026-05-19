from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.features.cv_processing.router import router as cv_processing_router
from app.features.jd_ingestion.router import router as jd_ingestion_router
from app.workers.cv_worker import cv_worker
from app.workers.jd_worker import jd_worker


@asynccontextmanager
async def lifespan(app: FastAPI):
    cv_worker.start()
    jd_worker.start()
    try:
        yield
    finally:
        cv_worker.stop()
        jd_worker.stop()


app = FastAPI(title="JobMatch AI Processing", version="1.0.0", lifespan=lifespan)

app.include_router(jd_ingestion_router, prefix="/api/jobs", tags=["jd-ingestion"])
app.include_router(cv_processing_router, prefix="/api/cvs", tags=["cv-processing"])


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "ai_processing"}
