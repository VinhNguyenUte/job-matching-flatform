from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.features.jd_ingestion.router import router as jd_ingestion_router

app = FastAPI(title="JobMatch AI Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(jd_ingestion_router, prefix="/api/jobs", tags=["jobs"])


@app.get("/")
def root():
    return {"message": "JobMatch AI service is running"}


@app.get("/health")
def health():
    return {"status": "ok", "service": "ai_service"}
