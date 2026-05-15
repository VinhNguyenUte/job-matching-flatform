from sqlalchemy import BigInteger, Column, ForeignKey, String, Text

from app.core.database import Base
from app.models.base import public_id_column


class Benefit(Base):
    __tablename__ = "benefits"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    public_id = public_id_column()
    name = Column(String(255), unique=True, nullable=False)
    category = Column(String(50))


class JobBenefit(Base):
    __tablename__ = "job_benefits"

    job_id = Column(BigInteger, ForeignKey("jobs.id", ondelete="CASCADE"), primary_key=True)
    benefit_id = Column(BigInteger, ForeignKey("benefits.id", ondelete="CASCADE"), primary_key=True)
    note = Column(Text)
