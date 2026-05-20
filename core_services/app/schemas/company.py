from datetime import datetime
from pydantic import HttpUrl, Field, field_validator
from uuid import UUID
from typing import Optional
from app.schemas.base import BaseSchema

class CompanyBase(BaseSchema):
    name: str = Field(..., max_length=255)
    parent_company_id: Optional[UUID] = None
    website: Optional[str] = None
    logo_url: Optional[str] = None
    industry: Optional[str] = Field(None, max_length=100)
    mission: Optional[str] = None
    size_range: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    is_global: bool = False

    @field_validator("is_global", mode="before")
    @classmethod
    def default_is_global(cls, value):
        return False if value is None else value

class CompanyCreate(CompanyBase):
    pass

class CompanyResponse(CompanyBase):
    id: UUID
    created_at: datetime
