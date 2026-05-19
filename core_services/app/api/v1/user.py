from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import User, Application
from app.schemas.user import DashboardStatsResponse
from app.api.v1.auth import get_current_user

router = APIRouter(tags=["Users"])

@router.get("/dashboard-stats", response_model=DashboardStatsResponse)
def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    API lấy thông tin thống kê tổng quan cho màn hình Dashboard của ứng viên
    """
    try:
        applications_count = db.query(Application).filter(
            Application.user_id == current_user.id
        ).count()

        saved_jobs_count = 0  
        profile_views_count = 0

        return {
            "applications": applications_count,
            "saved_jobs": saved_jobs_count,
            "profile_views": profile_views_count
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi hệ thống khi tải thống kê: {str(e)}"
        )