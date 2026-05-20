from datetime import datetime
from pydantic import Field
from uuid import UUID
from typing import Optional
from app.schemas.base import BaseSchema

class JobRawLogBase(BaseSchema):
    source_url: Optional[str] = None
    raw_content: Optional[str] = None
    processing_status: str = "pending"
    content_hash: Optional[str] = Field(None, max_length=64)

class JobRawLogCreate(JobRawLogBase):
    pass

class JobRawLogResponse(JobRawLogBase):
    id: int
    public_id: UUID
    scraped_at: datetime