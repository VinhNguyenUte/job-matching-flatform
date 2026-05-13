from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from app.core.database import Base

class Match(Base):
    __tablename__ = "matches"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    cv_id = Column(Integer, ForeignKey("cvs.id"))
    job_id = Column(Integer, ForeignKey("jobs.id"))
    score = Column(Float, nullable=False)
    explanation = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())