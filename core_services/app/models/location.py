from sqlalchemy import Column, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.base import uuid_pk_column


class JobLocation(Base):
    __tablename__ = "job_locations"

    id = uuid_pk_column()
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    building = Column(String(255))
    address = Column(Text)
    city = Column(String(100))
    country = Column(String(100), default="Vietnam")

    job = relationship("Job", back_populates="locations")
