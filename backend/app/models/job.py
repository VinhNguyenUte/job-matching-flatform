from sqlalchemy import BigInteger, Boolean, Column, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector

from app.core.database import Base
from app.models.base import public_id_column


class Job(Base):
    __tablename__ = "jobs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    public_id = public_id_column()
    company_id = Column(BigInteger, ForeignKey("companies.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(255), nullable=False)
    business_unit = Column(String(100))
    department = Column(String(100))
    job_level = Column(String(50))
    status = Column(String(20), default="active")
    work_mode = Column(String(50))
    job_type = Column(String(50))
    vacancy_count = Column(Integer, default=1)
    min_experience = Column(Numeric)
    target_majors = Column(JSONB)
    education_level_required = Column(String(100))
    academic_support = Column(Boolean, default=False)
    working_hours = Column(Text)
    salary_min = Column(Numeric)
    salary_max = Column(Numeric)
    salary_unit = Column(String(20), default="Month")
    currency = Column(String(10), default="VND")
    salary_description = Column(Text)
    performance_review_frequency = Column(String(255))
    uses_ai_in_hiring = Column(Boolean, default=False)
    is_equal_opportunity = Column(Boolean, default=True)
    application_deadline = Column(Date)
    description_raw = Column(Text)
    embedding = Column(Vector(768))
    contact_person_name = Column(String(255))
    contact_email = Column(String(255))
    contact_phone = Column(String(50))
    contact_phone_ext = Column(String(10))
    application_url = Column(Text)
    hiring_process = Column(JSONB)
    training_details = Column(JSONB)
    extended_attributes = Column(JSONB)
    source_url = Column(Text, unique=True)
    posted_at = Column(DateTime)
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))

    company = relationship("Company", back_populates="jobs")
    locations = relationship("JobLocation", back_populates="job", cascade="all, delete-orphan")
