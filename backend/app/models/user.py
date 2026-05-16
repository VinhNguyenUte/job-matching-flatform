from sqlalchemy import Column, DateTime, String, text
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.base import uuid_pk_column


class User(Base):
    __tablename__ = "users"

    id = uuid_pk_column()
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    phone = Column(String(20))
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))

    cvs = relationship("CV", back_populates="user", cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="user", cascade="all, delete-orphan")
