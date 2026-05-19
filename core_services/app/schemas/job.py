from datetime import date, datetime
from pydantic import Field, EmailStr, field_validator
from uuid import UUID
from typing import Any, List, Optional
from decimal import Decimal
from app.schemas.base import BaseSchema
from app.schemas.company import CompanyResponse
from app.schemas.job_location import JobLocationResponse
from app.schemas.master_data import (
    JobSkillResponse, JobToolResponse, JobBenefitResponse, 
    JobLanguageResponse, MindsetSchema
)

class JobBase(BaseSchema):
    title: str = Field(..., max_length=255)
    business_unit: Optional[str] = Field(None, max_length=100)
    department: Optional[str] = Field(None, max_length=100)
    job_level: Optional[str] = Field(None, max_length=50)
    status: str = "active"
    work_mode: Optional[str] = Field(None, max_length=50)
    job_type: Optional[str] = Field(None, max_length=50)
    vacancy_count: int = 1
    min_experience: Optional[Decimal] = None
    target_majors: Optional[Any] = None  # JSONB
    education_level_required: Optional[str] = Field(None, max_length=100)
    academic_support: bool = False
    working_hours: Optional[str] = None
    salary_min: Optional[Decimal] = None
    salary_max: Optional[Decimal] = None
    salary_unit: str = "Month"
    currency: str = "VND"
    salary_description: Optional[str] = None
    performance_review_frequency: Optional[str] = Field(None, max_length=255)
    uses_ai_in_hiring: bool = False
    is_equal_opportunity: bool = True
    application_deadline: Optional[date] = None
    description_raw: Optional[str] = None
    contact_person_name: Optional[str] = Field(None, max_length=255)
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = Field(None, max_length=50)
    contact_phone_ext: Optional[str] = Field(None, max_length=10)
    application_url: Optional[str] = None
    hiring_process: Optional[Any] = None   # JSONB
    training_details: Optional[Any] = None # JSONB
    extended_attributes: Optional[Any] = None # JSONB
    source_url: Optional[str] = None

    @field_validator("status", mode="before")
    @classmethod
    def default_status(cls, value):
        return value or "active"

    @field_validator("contact_email", mode="before")
    @classmethod
    def normalize_contact_email(cls, value):
        if value is None:
            return None
        if isinstance(value, str) and value.strip().lower() in {"", "null", "none", "n/a"}:
            return None
        return value

class JobCreate(JobBase):
    company_id: Optional[UUID] = None

class JobResponse(JobBase):
    id: UUID
    company_id: Optional[UUID] = None
    posted_at: Optional[datetime] = None
    created_at: datetime
    
    # Các quan hệ kết nối (Sử dụng property hoặc joined load từ DB)
    company: Optional[CompanyResponse] = None
    locations: List[JobLocationResponse] = []


class JobRecommendationResponse(JobResponse):
    match_score: float


class JobDetailResponse(JobResponse):
    """Schema mở rộng chứa toàn bộ ma trận dữ liệu đã bóc tách từ AI phục vụ màn hình chi tiết job"""
    skills: List[JobSkillResponse] = []
    tools: List[JobToolResponse] = []
    benefits: List[JobBenefitResponse] = []
    languages: List[JobLanguageResponse] = []
    mindsets: List[MindsetSchema] = []
class JobIngestRequest(BaseSchema):
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = ""
    post_time: Optional[str] = ""
    link: Optional[str] = ""
    description: Optional[str] = None
    post_id: Optional[str] = None
    author: Optional[str] = None
    text: Optional[str] = None
    timestamp: Optional[str] = ""
    url: Optional[str] = ""
    scraped_at: Optional[str] = ""
    likes: Optional[int] = None
    comments_count: Optional[int] = None
    shares: Optional[int] = None
    comments: List[Any] = []


class JobIngestItemResult(BaseSchema):
    title: str
    status: str
    job_id: Optional[UUID] = None
    detail: Optional[str] = None


class JobIngestSummary(BaseSchema):
    total: int
    success: int
    skipped: int
    errors: int


class JobIngestResponse(BaseSchema):
    success: bool
    summary: JobIngestSummary
    results: List[JobIngestItemResult]
