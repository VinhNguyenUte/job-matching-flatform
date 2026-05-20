from datetime import datetime
from pydantic import EmailStr, Field
from uuid import UUID
from typing import Optional
from app.schemas.base import BaseSchema


class UserBase(BaseSchema):
    email: EmailStr
    full_name: str = Field(..., max_length=100)
    phone: Optional[str] = Field(None, max_length=20)

class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=255)

class UserResponse(UserBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

class DashboardStatsResponse(BaseSchema):
    applications: int
    saved_jobs: int
    profile_views: int

    class Config:
        from_attributes = True