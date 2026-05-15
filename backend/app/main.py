from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import job

app = FastAPI(title="JobMatch Backend", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(job.router, prefix="/api/v1/jobs", tags=["jobs"])
app.include_router(job.ingestion_router, prefix="/jobs", tags=["jd-ingestion"])


@app.get("/")
def root():
    return {"message": "JobMatch Backend is running"}


@app.get("/health")
def health():
    return {"status": "ok", "service": "backend"}
