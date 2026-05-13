from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector  
from app.core.database import Base

class CV(Base):
    __tablename__ = "cvs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    file_path = Column(String, nullable=False)
    original_filename = Column(String)
    parsed_text = Column(Text)
    entities = Column(JSON)
    embedding = Column(Vector(768))           # Gemini embedding size thường là 768 hoặc 1024
    status = Column(String, default="pending")
    match_score = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())