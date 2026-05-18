from datetime import datetime
from pydantic import Field
from uuid import UUID
from typing import Any, Optional
from app.schemas.base import BaseSchema

class CVBase(BaseSchema):
    title: Optional[str] = Field(None, max_length=150)
    is_primary: bool = False

class CVCreate(CVBase):
    pass

class CVResponse(CVBase):
    id: int
    user_id: UUID
    raw_text: Optional[str] = None
    parsed_data: Optional[Any] = None  # Nhận dữ liệu JSONB từ AI Worker
    # Không expose trường embedding ra API Response để tối ưu băng thông
    created_at: datetime
    updated_at: datetime