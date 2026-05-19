from google.genai import types

from app.common.clients.ai_retry import call_ai_with_retry
from app.common.clients.gemini import gemini_client
from app.common.config import settings
from app.features.cv_processing.schemas import CVParsedData


class CVEmbeddingPipeline:
    @staticmethod
    def build_embedding_text(parsed: CVParsedData) -> str:
        roles = ", ".join(item.role for item in parsed.experience if item.role)
        education = ", ".join(
            f"{item.school} {item.major}".strip()
            for item in parsed.education
            if item.school or item.major
        )
        return "\n".join(
            [
                f"Name: {parsed.full_name}",
                f"Summary: {parsed.summary or ''}",
                f"Roles: {roles}",
                f"Skills: {', '.join(parsed.skills)}",
                f"Education: {education}",
            ]
        ).strip()

    @staticmethod
    async def generate_embedding(text: str) -> list[float] | None:
        if not text:
            return None
        response = await call_ai_with_retry(
            "cv_embedding.embed_content",
            lambda: gemini_client.models.embed_content(
                model=settings.embedding_model,
                contents=text,
                config=types.EmbedContentConfig(output_dimensionality=768),
            ),
        )
        return response.embeddings[0].values
