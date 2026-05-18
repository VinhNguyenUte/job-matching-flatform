from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import Field, HttpUrl

from app.schemas.base import BaseSchema


class CVBase(BaseSchema):
    title: Optional[str] = Field(None, max_length=150)
    is_primary: bool = False


class CVCreate(BaseSchema):
    url: HttpUrl


class CVUploadResponse(CVBase):
    id: UUID
    user_id: UUID
    raw_text: Optional[str] = None
    parsed_data: Optional[Any] = None
    embedding_created: bool = False
    created_at: datetime
    updated_at: datetime


class CVResponse(CVBase):
    id: UUID
    user_id: UUID
    raw_text: Optional[str] = None
    parsed_data: Optional[Any] = None
    created_at: datetime
    updated_at: datetime
