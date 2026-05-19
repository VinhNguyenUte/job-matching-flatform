from google.genai import types

from app.common.clients.ai_retry import call_ai_with_retry
from app.common.clients.gemini import gemini_client
from app.common.config import settings
from app.features.jd_ingestion.schemas import NERResult


class JDEmbeddingPipeline:
    @staticmethod
    def build_embedding_text(raw_content: str, ner: NERResult) -> str:
        parts = [
            f"Job title: {ner.job_title or ''}",
            f"Company: {ner.company_name or ''}",
            f"Experience: {ner.experience or ''}",
            f"Education: {ner.education or ''}",
            f"Salary: {ner.salary or ''}",
            "Skills: " + ", ".join(entity.name for entity in ner.skills),
            "Tools: " + ", ".join(entity.name for entity in ner.tools),
            "Languages: " + ", ".join(entity.name for entity in ner.languages),
            "Benefits: " + ", ".join(entity.name for entity in ner.benefits),
            "Locations: " + ", ".join(entity.name for entity in ner.locations),
            "Mindsets: " + ", ".join(entity.name for entity in ner.mindsets),
            f"Raw JD: {raw_content}",
        ]
        return "\n".join(part for part in parts if part.strip())

    @staticmethod
    async def generate_embedding(text: str) -> list[float]:
        response = await call_ai_with_retry(
            "jd_embedding.embed_content",
            lambda: gemini_client.models.embed_content(
                model=settings.embedding_model,
                contents=text,
                config=types.EmbedContentConfig(output_dimensionality=768),
            ),
        )
        return response.embeddings[0].values
