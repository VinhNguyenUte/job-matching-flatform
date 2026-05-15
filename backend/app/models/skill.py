from sqlalchemy import BigInteger, Column, ForeignKey, SmallInteger, String

from app.core.database import Base
from app.models.base import public_id_column


class Skill(Base):
    __tablename__ = "skills"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    public_id = public_id_column()
    name = Column(String(255), unique=True, nullable=False)


class JobSkill(Base):
    __tablename__ = "job_skills"

    job_id = Column(BigInteger, ForeignKey("jobs.id", ondelete="CASCADE"), primary_key=True)
    skill_id = Column(BigInteger, ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True)
    priority_level = Column(SmallInteger, default=1)
