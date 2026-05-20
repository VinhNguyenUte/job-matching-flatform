import os

from google import genai

from app.common.config import settings


def create_vertex_client():
    if settings.vertex_api_key:
        return genai.Client(
            vertexai=True,
            api_key=settings.vertex_api_key,
        )

    if not settings.vertex_project_id:
        raise RuntimeError("GOOGLE_CLOUD_PROJECT or VERTEX_PROJECT_ID is required when AI_PROVIDER=vertex.")

    if settings.GOOGLE_APPLICATION_CREDENTIALS:
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = settings.GOOGLE_APPLICATION_CREDENTIALS

    return genai.Client(
        vertexai=True,
        project=settings.vertex_project_id,
        location=settings.vertex_location,
    )
