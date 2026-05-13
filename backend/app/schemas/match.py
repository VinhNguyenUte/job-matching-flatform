from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict

class MatchResponse(BaseModel):
    id: int
    user_id: int
    cv_id: int
    status: str
    message: str

class MatchDetailResponse(BaseModel):
    id: int
    original_filename: str
    status: str
    match_score: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True