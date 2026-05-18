from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.base import uuid_pk_column


class Company(Base):
    __tablename__ = "companies"

    id = uuid_pk_column()
    parent_company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="SET NULL"), nullable=True)
    name = Column(String(255), nullable=False)
    website = Column(Text)
    logo_url = Column(Text)
    industry = Column(String(100))
    mission = Column(Text)
    size_range = Column(String(50))
    description = Column(Text)
    is_global = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))

    jobs = relationship("Job", back_populates="company")
