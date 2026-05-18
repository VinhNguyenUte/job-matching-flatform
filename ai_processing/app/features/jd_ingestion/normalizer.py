from google.genai import types

from app.common.clients.gemini import gemini_client
from app.common.config import settings
from app.common.schemas.job import JobParsedSchema
from app.features.jd_ingestion.schemas import KnowledgeGraphContext, NERResult


class JDNormalizerService:
    @staticmethod
    async def normalize(
        raw_content: str,
        ner: NERResult,
        graph: KnowledgeGraphContext,
        embedding_text: str,
    ) -> JobParsedSchema:
        prompt = f"""
You are a job description data normalization service.

Use the raw job description, extracted entities, and temporary knowledge graph context to produce
one normalized JSON object matching the requested schema.

Rules:
- Return only valid JSON matching the schema.
- Missing fields must use null, empty string, false, or empty arrays as appropriate.
- min_experience must be a float number of years. Example: 6 months = 0.5.
- Carefully normalize locations, skills, tools, languages, benefits, mindsets.
- requirements_summary should be a concise summary of the core requirements.
- Do not include the knowledge graph itself in extended_attributes.

Extracted entities:
{ner.model_dump_json()}

Temporary knowledge graph context:
{graph.context_text}

Embedding context text:
{embedding_text}

Raw job description:
{raw_content}
"""
        response = gemini_client.models.generate_content(
            model=settings.AI_GENERATION_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=JobParsedSchema,
                temperature=0.1,
            ),
        )
        return JobParsedSchema.model_validate_json(response.text)
