from sqlalchemy import BigInteger, Column, DateTime, String, Text, text

from app.core.database import Base
from app.models.base import public_id_column


class JobRawLog(Base):
    __tablename__ = "job_raw_logs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    public_id = public_id_column()
    source_url = Column(Text)
    raw_content = Column(Text)
    scraped_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
    processing_status = Column(String(20), default="pending")
    content_hash = Column(String(64), unique=True)
