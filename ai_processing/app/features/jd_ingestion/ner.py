from google.genai import types

from app.common.clients.ai_retry import call_ai_with_retry
from app.common.clients.gemini import gemini_client
from app.common.config import settings
from app.features.jd_ingestion.schemas import NERResult


class JDNERService:
    @staticmethod
    async def extract_entities(raw_content: str) -> NERResult:
        prompt = f"""
Extract named entities from this job description.

Return only JSON matching the schema. Focus on entities that help job matching:
skills, tools, languages, benefits, locations, mindsets, salary, experience, education.

Job description:
{raw_content}
"""
        response = await call_ai_with_retry(
            "jd_ner.generate_content",
            lambda: gemini_client.models.generate_content(
                model=settings.AI_GENERATION_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=NERResult,
                    temperature=0.1,
                ),
            ),
            rate_limit_key="generate_content",
            min_interval_seconds=settings.AI_GENERATION_MIN_INTERVAL_SECONDS,
        )
        return NERResult.model_validate_json(response.text)
