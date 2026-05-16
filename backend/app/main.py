from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import engine, Base
from app.api.v1 import auth, cv, job, recommend
from fastapi.security import OAuth2PasswordBearer

# Tạo bảng (dev only)
# Base.metadata.create_all(bind=engine)

app = FastAPI(title="JobMatch AI", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Thay bằng domain frontend khi production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(cv.router, prefix="/api/v1/cv", tags=["cv"])
app.include_router(job.router, prefix="/api/v1/jobs", tags=["jobs"])
app.include_router(recommend.router, prefix="/api/v1/recommend", tags=["recommend"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


@app.get("/")
def root():
    return {"message": "JobMatch AI Backend is running"}

@app.on_event("startup")
async def startup_event():
    print("FastAPI + Celery started with RabbitMQ")

# Health check cho Celery
@app.get("/health/celery")
def celery_health():
    return {"status": "Celery worker is ready"}