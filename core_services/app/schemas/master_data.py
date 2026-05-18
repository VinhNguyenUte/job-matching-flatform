from pydantic import Field
from uuid import UUID
from typing import Optional
from app.schemas.base import BaseSchema

# --- SKILL ---
class SkillSchema(BaseSchema):
    id: int
    public_id: UUID
    name: str

class JobSkillResponse(BaseSchema):
    skill: SkillSchema
    priority_level: int

# --- TOOL ---
class ToolSchema(BaseSchema):
    id: int
    public_id: UUID
    name: str

class JobToolResponse(BaseSchema):
    tool: ToolSchema
    priority_level: int
    note: Optional[str] = None

# --- BENEFIT ---
class BenefitSchema(BaseSchema):
    id: int
    public_id: UUID
    name: str
    category: Optional[str] = None

class JobBenefitResponse(BaseSchema):
    benefit: BenefitSchema
    note: Optional[str] = None

# --- LANGUAGE ---
class LanguageSchema(BaseSchema):
    id: int
    public_id: UUID
    name: str

class JobLanguageResponse(BaseSchema):
    language: LanguageSchema
    proficiency_level: Optional[str] = None
    priority_level: int

# --- MINDSET ---
class MindsetSchema(BaseSchema):
    id: int
    public_id: UUID
    name: str