from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl


class CVExperience(BaseModel):
    company: str = Field("", description="Ten cong ty hoac to chuc")
    role: str = Field("", description="Vi tri, chuc vu lam viec")
    duration: str = Field("", description="Thoi gian lam viec")
    description: Optional[str] = Field(None, description="Mo ta ngan gon cong viec hoac du an da lam")


class CVEducation(BaseModel):
    school: str = Field("", description="Ten truong hoc hoac trung tam")
    major: str = Field("", description="Chuyen nganh hoc")
    duration: str = Field("", description="Thoi gian hoc")


class CVParsedData(BaseModel):
    full_name: str = Field("", description="Ho va ten day du cua ung vien")
    email: Optional[str] = Field(None, description="Dia chi email lien he")
    phone: Optional[str] = Field(None, description="So dien thoai lien he")
    skills: list[str] = Field(default_factory=list, description="Danh sach cac ky nang")
    experience: list[CVExperience] = Field(default_factory=list, description="Danh sach kinh nghiem lam viec")
    education: list[CVEducation] = Field(default_factory=list, description="Danh sach lich su hoc tap")
    summary: Optional[str] = Field(None, description="Tom tat ngan gon ve muc tieu nghe nghiep hoac gioi thieu ban than")


class CVImagePayload(BaseModel):
    url: HttpUrl
    mime_type: str = "image/jpeg"


class CVExtractRequest(BaseModel):
    user_id: UUID
    images: list[CVImagePayload] = Field(..., min_length=1)
    title: Optional[str] = None
    is_primary: bool = False
    persist: bool = True


class CVExtractResponse(BaseModel):
    id: Optional[UUID] = None
    user_id: UUID
    title: str
    raw_text: str
    parsed_data: dict
    embedding_created: bool
    is_primary: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
