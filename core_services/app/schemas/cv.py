from datetime import datetime
from typing import Any, List, Optional
from uuid import UUID

from pydantic import Field

from app.schemas.base import BaseSchema


class CVBase(BaseSchema):
    title: Optional[str] = Field(None, max_length=150)
    is_primary: bool = False


class CVCreate(CVBase):
    pass


class CVResponse(CVBase):
    id: UUID
    user_id: UUID
    raw_text: Optional[str] = None
    parsed_data: Optional[Any] = None
    created_at: datetime
    updated_at: datetime


class CVUploadQueuedResponse(BaseSchema):
    success: bool = True
    message: str
    cv_id: UUID
    user_id: UUID
    cv_urls: List[str]
    status: str = "processing"
