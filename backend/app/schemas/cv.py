from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class CVUploadResponse(BaseModel):
    cv_id: int
    status: str
    message: str

class CVResponse(BaseModel):
    id: int
    original_filename: str
    status: str
    match_score: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True