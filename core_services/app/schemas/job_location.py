from uuid import UUID
from typing import Optional
from app.schemas.base import BaseSchema

class JobLocationBase(BaseSchema):
    building: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: str = "Vietnam"

class JobLocationResponse(JobLocationBase):
    id: UUID
    job_id: UUID