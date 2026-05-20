from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import Field

from app.schemas.base import BaseSchema
from app.schemas.job import JobResponse
from app.schemas.cv import CVResponse


class ApplicationBase(BaseSchema):
    job_id: UUID
    cv_id: UUID
    status: str = "applied"


class ApplicationCreate(ApplicationBase):
    pass


class ApplicationUpdateStatus(BaseSchema):
    status: str = Field(..., max_length=30)


class ApplicationResponse(BaseSchema):
    id: int
    user_id: UUID
    job_id: UUID
    cv_id: UUID
    status: str
    applied_at: datetime
    updated_at: datetime
    job: Optional[JobResponse] = None
    cv: Optional[CVResponse] = None
