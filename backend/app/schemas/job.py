from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class JobBase(BaseModel):
    title: str
    company: str
    location: Optional[str] = None
    salary: Optional[str] = None
    description: Optional[str] = None

class JobResponse(JobBase):
    id: int
    source: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True