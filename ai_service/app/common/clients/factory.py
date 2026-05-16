from app.common.clients.gemini_client import create_gemini_client
from app.common.clients.vertex_client import create_vertex_client
from app.common.config import settings


def create_genai_client():
    provider = settings.normalized_ai_provider

    if provider == "gemini":
        return create_gemini_client()

    if provider == "vertex":
        return create_vertex_client()

    raise RuntimeError("AI_PROVIDER must be either 'gemini' or 'vertex'.")


ai_client = create_genai_client()
