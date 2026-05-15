from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class JobBase(BaseModel):
    title: str
    company: str
    location: Optional[str] = None
    salary: Optional[str] = None
    description: Optional[str] = None


class JobResponse(JobBase):
    id: int
    source: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class JobIngestRequest(BaseModel):
    title: str
    company: str
    location: Optional[str] = ""
    post_time: Optional[str] = ""
    link: Optional[str] = ""
    description: str


class ParsedCompanySchema(BaseModel):
    name: str = Field(description="Hiring company name")
    website: Optional[str] = None
    industry: Optional[str] = None


class ParsedSkillSchema(BaseModel):
    name: str
    priority_level: int = 1


class ParsedToolSchema(BaseModel):
    name: str
    priority_level: int = 1
    note: Optional[str] = None


class ParsedLanguageSchema(BaseModel):
    name: str
    proficiency_level: Optional[str] = None
    priority_level: int = 1


class ParsedBenefitSchema(BaseModel):
    name: str
    category: Optional[str] = None
    note: Optional[str] = None


class ParsedLocationSchema(BaseModel):
    building: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: str = "Vietnam"


class JobParsedSchema(BaseModel):
    title: str
    company: ParsedCompanySchema
    business_unit: Optional[str] = None
    department: Optional[str] = None
    job_level: Optional[str] = None
    work_mode: Optional[str] = None
    job_type: Optional[str] = None
    vacancy_count: int = 1
    min_experience: Optional[float] = None
    target_majors: List[str] = Field(default_factory=list)
    education_level_required: Optional[str] = None
    academic_support: bool = False
    working_hours: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_unit: str = "Month"
    currency: str = "VND"
    salary_description: Optional[str] = None
    performance_review_frequency: Optional[str] = None
    description_raw: Optional[str] = None
    requirements_summary: Optional[str] = None
    uses_ai_in_hiring: bool = False
    is_equal_opportunity: bool = True
    application_deadline: Optional[str] = None
    contact_person_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_phone_ext: Optional[str] = None
    application_url: Optional[str] = None
    hiring_process: List[str] = Field(default_factory=list)
    training_details: List[str] = Field(default_factory=list)
    extended_attributes: Dict[str, Any] = Field(default_factory=dict)
    skills: List[ParsedSkillSchema] = Field(default_factory=list)
    tools: List[ParsedToolSchema] = Field(default_factory=list)
    languages: List[ParsedLanguageSchema] = Field(default_factory=list)
    mindsets: List[str] = Field(default_factory=list)
    benefits: List[ParsedBenefitSchema] = Field(default_factory=list)
    locations: List[ParsedLocationSchema] = Field(default_factory=list)


class JobCatalogItem(BaseModel):
    id: int
    title: str
    company_name: str
    city: Optional[str] = None
    job_level: Optional[str] = None
    work_mode: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    currency: Optional[str] = None
    source_url: Optional[str] = None
    posted_at: Optional[datetime] = None
    created_at: datetime


class JobIngestItemResult(BaseModel):
    title: str
    status: str
    job_id: Optional[int] = None
    detail: Optional[str] = None


class JobIngestSummary(BaseModel):
    total: int
    success: int
    skipped: int
    errors: int


class JobIngestResponse(BaseModel):
    success: bool
    summary: JobIngestSummary
    results: List[JobIngestItemResult]


class JobAIProcessingResponse(BaseModel):
    parsed_data: JobParsedSchema
    embedding_text: str
    embedding: List[float]
