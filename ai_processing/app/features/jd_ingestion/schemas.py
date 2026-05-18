from typing import Any, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.common.schemas.job import JobParsedSchema


class IngestJobRequest(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = ""
    post_time: Optional[str] = ""
    link: Optional[str] = ""
    description: Optional[str] = None
    post_id: Optional[str] = None
    author: Optional[str] = None
    text: Optional[str] = None
    timestamp: Optional[str] = ""
    url: Optional[str] = ""
    scraped_at: Optional[str] = ""
    likes: Optional[int] = None
    comments_count: Optional[int] = None
    shares: Optional[int] = None
    comments: list[Any] = Field(default_factory=list)


class NormalizedJobInput(BaseModel):
    raw_text: str
    source_type: str
    source_url: Optional[str] = None
    posted_at: Optional[str] = None
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    source_author: Optional[str] = None
    external_id: Optional[str] = None
    source_metadata: dict[str, Any] = Field(default_factory=dict)


class NamedEntity(BaseModel):
    name: str
    entity_type: str
    label: Optional[str] = None
    confidence: float = Field(1.0, ge=0, le=1)


class NERResult(BaseModel):
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    skills: List[NamedEntity] = Field(default_factory=list)
    tools: List[NamedEntity] = Field(default_factory=list)
    languages: List[NamedEntity] = Field(default_factory=list)
    benefits: List[NamedEntity] = Field(default_factory=list)
    locations: List[NamedEntity] = Field(default_factory=list)
    mindsets: List[NamedEntity] = Field(default_factory=list)
    salary: Optional[str] = None
    experience: Optional[str] = None
    education: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class KnowledgeGraphEdge(BaseModel):
    source: str
    relation: str
    target: str


class KnowledgeGraphContext(BaseModel):
    nodes: List[NamedEntity] = Field(default_factory=list)
    edges: List[KnowledgeGraphEdge] = Field(default_factory=list)
    context_text: str = ""


class JobIngestItemResult(BaseModel):
    title: str
    status: str
    job_id: Optional[UUID] = None
    detail: Optional[str] = None


class JobIngestSummary(BaseModel):
    total: int
    success: int
    skipped: int
    errors: int


class JobIngestResponse(BaseModel):
    success: bool
    summary: JobIngestSummary
    results: List[JobIngestItemResult]
