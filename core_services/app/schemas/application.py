from datetime import datetime
from pydantic import Field
from uuid import UUID
from app.schemas.base import BaseSchema
from app.schemas.job import JobResponse
from app.schemas.cv import CVResponse

class ApplicationBase(BaseSchema):
    job_id: UUID
    cv_id: int
    status: str = "applied"

class ApplicationCreate(ApplicationBase):
    pass

class ApplicationUpdateStatus(BaseSchema):
    status: str = Field(..., max_length=30)

class ApplicationResponse(BaseSchema):
    id: int
    user_id: UUID
    job_id: UUID
    cv_id: int
    status: str
    applied_at: datetime
    updated_at: datetime
    
    # Nested thông tin để Frontend hiển thị trong Dashboard ứng tuyển
    job: Optional[JobResponse] = None
    cv: Optional[CVResponse] = None