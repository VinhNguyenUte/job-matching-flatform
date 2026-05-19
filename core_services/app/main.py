from fastapi import FastAPI
from app.core.config import settings
from app.api.v1 import cv, job, recommend, auth

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="2.0.0",
    description="Hệ thống Core Backend điều phối dữ liệu Khớp lệnh việc làm ứng dụng AI Vector"
)

"""
CORS headers are handled by the Nginx API gateway.
The gateway adds the required Access-Control-Allow-* headers
for requests coming from the frontend.
"""

# ==================== ROUTE REGISTRATION ====================
# Đăng ký danh sách các Phân hệ định tuyến Routing
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(cv.router, prefix="/api/v1/cv", tags=["CV Management"])
app.include_router(job.router, prefix="/api/v1/jobs", tags=["Job Engine"])
app.include_router(recommend.router, prefix="/api/v1/recommend", tags=["AI Recommendation Engine"])

@app.get("/health", tags=["System Monitoring"])
def health_check():
    return {
        "status": "healthy",
        "service": "core_services_api",
        "database_layer": "connected"
    }
