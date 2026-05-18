from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class CompanySchema(BaseModel):
    name: str = Field(description="Name of the company hiring")
    website: Optional[str] = Field(None, description="Company website URL if available")
    industry: Optional[str] = Field(None, description="Industry category of the company")


class SkillSchema(BaseModel):
    name: str = Field(description="Skill name")
    priority_level: int = Field(1, description="1: required, 2: preferred, 3: bonus, 4: optional")


class ToolSchema(BaseModel):
    name: str = Field(description="Tool or tech name")
    priority_level: int = Field(1, description="1: required, 2: preferred, 3: bonus, 4: optional")
    note: Optional[str] = Field(None, description="Note on how the tool is used")


class LanguageSchema(BaseModel):
    name: str = Field(description="Language name")
    proficiency_level: Optional[str] = Field(None, description="Proficiency like IELTS 6.5, N2, etc.")
    priority_level: int = Field(1, description="1: required, 2: preferred, 3: bonus, 4: optional")


class BenefitSchema(BaseModel):
    name: str = Field(description="Benefit name")
    category: Optional[str] = Field(None, description="Benefit category")
    note: Optional[str] = Field(None, description="Special policy notes")


class JobLocationSchema(BaseModel):
    building: Optional[str] = Field(None, description="Building name")
    address: Optional[str] = Field(None, description="Specific address")
    city: Optional[str] = Field(None, description="City")
    country: str = Field("Vietnam", description="Country")


class JobParsedSchema(BaseModel):
    title: str = Field(description="Job title")
    company: CompanySchema = Field(description="Hiring company details")
    business_unit: Optional[str] = Field(None, description="Business unit")
    department: Optional[str] = Field(None, description="Department name")
    job_level: Optional[str] = Field(None, description="Intern, Fresher, Junior, Senior, Lead, Manager, etc.")
    work_mode: Optional[str] = Field(None, description="Remote, Hybrid, On-site")
    job_type: Optional[str] = Field(None, description="Full-time, Internship, Freelance")
    vacancy_count: int = Field(1, description="Number of vacancies")
    min_experience: Optional[float] = Field(None, description="Minimum years of experience required")
    target_majors: List[str] = Field(default_factory=list, description="Target majors")
    education_level_required: Optional[str] = Field(None, description="Education required")
    academic_support: bool = Field(False, description="Does the company support academic growth?")
    working_hours: Optional[str] = Field(None, description="Working hours")
    salary_min: Optional[float] = Field(None, description="Minimum salary")
    salary_max: Optional[float] = Field(None, description="Maximum salary")
    salary_unit: str = Field("Month", description="Month, Year, Hour, etc.")
    currency: str = Field("VND", description="VND, USD, etc.")
    salary_description: Optional[str] = Field(None, description="Text describing the salary package")
    performance_review_frequency: Optional[str] = Field(None, description="Frequency of performance or salary review")
    description_raw: Optional[str] = Field(None, description="The raw detailed job description text")
    requirements_summary: Optional[str] = Field(None, description="Short summary of the main requirements")
    uses_ai_in_hiring: bool = Field(False, description="Does the company use AI in the hiring process?")
    is_equal_opportunity: bool = Field(True, description="Equal opportunity statement exists")
    application_deadline: Optional[str] = Field(None, description="Application deadline date in YYYY-MM-DD format")
    contact_person_name: Optional[str] = Field(None, description="Contact person's name")
    contact_email: Optional[str] = Field(None, description="Contact email")
    contact_phone: Optional[str] = Field(None, description="Contact phone")
    contact_phone_ext: Optional[str] = Field(None, description="Contact phone extension")
    application_url: Optional[str] = Field(None, description="Application URL")
    hiring_process: List[str] = Field(default_factory=list, description="Hiring process steps")
    training_details: List[str] = Field(default_factory=list, description="Training details")
    extended_attributes: Dict[str, Any] = Field(default_factory=dict, description="Extra parsed attributes")
    skills: List[SkillSchema] = Field(default_factory=list, description="Skills required or preferred")
    tools: List[ToolSchema] = Field(default_factory=list, description="Tools required or preferred")
    languages: List[LanguageSchema] = Field(default_factory=list, description="Languages required or preferred")
    mindsets: List[str] = Field(default_factory=list, description="Mindsets requested")
    benefits: List[BenefitSchema] = Field(default_factory=list, description="Benefits provided")
    locations: List[JobLocationSchema] = Field(default_factory=list, description="Job locations")
