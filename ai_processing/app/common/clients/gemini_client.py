from google import genai

from app.common.config import settings


def create_gemini_client():
    if not settings.GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is required when AI_PROVIDER=gemini.")
    return genai.Client(api_key=settings.GEMINI_API_KEY)
