from sqlalchemy import BigInteger, Column, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.base import public_id_column


class JobLocation(Base):
    __tablename__ = "job_locations"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    public_id = public_id_column()
    job_id = Column(BigInteger, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    building = Column(String(255))
    address = Column(Text)
    city = Column(String(100))
    country = Column(String(100), default="Vietnam")

    job = relationship("Job", back_populates="locations")
