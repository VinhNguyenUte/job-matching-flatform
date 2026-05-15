from typing import List, Optional

from pydantic import BaseModel

from app.common.schemas.job import JobParsedSchema


class IngestJobRequest(BaseModel):
    title: str
    company: str
    location: Optional[str] = ""
    post_time: Optional[str] = ""
    link: Optional[str] = ""
    description: str


class ProcessJobResponse(BaseModel):
    parsed_data: JobParsedSchema
    embedding_text: str
    embedding: List[float]
