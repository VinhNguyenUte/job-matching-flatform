from sqlalchemy import BigInteger, Column, ForeignKey, SmallInteger, String
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base
from app.models.base import public_id_column


class Language(Base):
    __tablename__ = "languages"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    public_id = public_id_column()
    name = Column(String(100), unique=True, nullable=False)


class JobLanguage(Base):
    __tablename__ = "job_languages"

    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), primary_key=True)
    language_id = Column(BigInteger, ForeignKey("languages.id", ondelete="CASCADE"), primary_key=True)
    proficiency_level = Column(String(50))
    priority_level = Column(SmallInteger, default=1)
