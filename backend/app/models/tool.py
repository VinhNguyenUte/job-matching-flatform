from sqlalchemy import BigInteger, Column, ForeignKey, SmallInteger, String, Text

from app.core.database import Base
from app.models.base import public_id_column


class Tool(Base):
    __tablename__ = "tools"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    public_id = public_id_column()
    name = Column(String(255), unique=True, nullable=False)


class JobTool(Base):
    __tablename__ = "job_tools"

    job_id = Column(BigInteger, ForeignKey("jobs.id", ondelete="CASCADE"), primary_key=True)
    tool_id = Column(BigInteger, ForeignKey("tools.id", ondelete="CASCADE"), primary_key=True)
    priority_level = Column(SmallInteger, default=1)
    note = Column(Text)
