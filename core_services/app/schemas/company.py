from datetime import datetime
from pydantic import HttpUrl, Field
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

class CompanyCreate(CompanyBase):
    pass

class CompanyResponse(CompanyBase):
    id: UUID
    created_at: datetime