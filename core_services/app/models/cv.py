from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector

from app.core.database import Base
from app.models.base import uuid_pk_column


class CV(Base):
    __tablename__ = "cvs"

    id = uuid_pk_column()
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(150))
    raw_text = Column(Text)
    parsed_data = Column(JSONB)
    embedding = Column(Vector(768))
    is_primary = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))

    user = relationship("User", back_populates="cvs")
    applications = relationship("Application", back_populates="cv")
