from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from app.core.database import Base

class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    company = Column(String, index=True)
    location = Column(String)
    salary = Column(String)
    description = Column(Text)
    requirements = Column(Text)
    source = Column(String)
    external_id = Column(String, unique=True)
    raw_data = Column(JSON)
    embedding = Column(Vector(768))
    created_at = Column(DateTime(timezone=True), server_default=func.now())