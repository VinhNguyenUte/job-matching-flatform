from sqlalchemy import BigInteger, Column, ForeignKey, String

from app.core.database import Base
from app.models.base import public_id_column


class Mindset(Base):
    __tablename__ = "mindsets"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    public_id = public_id_column()
    name = Column(String(255), unique=True, nullable=False)


class JobMindset(Base):
    __tablename__ = "job_mindsets"

    job_id = Column(BigInteger, ForeignKey("jobs.id", ondelete="CASCADE"), primary_key=True)
    mindset_id = Column(BigInteger, ForeignKey("mindsets.id", ondelete="CASCADE"), primary_key=True)
