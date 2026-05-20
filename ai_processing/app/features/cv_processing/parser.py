import json

import httpx
from google.genai import types

from app.common.clients.ai_retry import call_ai_with_retry
from app.common.clients.gemini import gemini_client
from app.common.config import settings
from app.features.cv_processing.schemas import CVImagePayload, CVParsedData


class CVParserService:
    @staticmethod
    async def parse_images(images: list[CVImagePayload]) -> CVParsedData:
        contents = [await CVParserService._build_part(image) for image in images]
        contents.append(CVParserService._prompt())

        response = await call_ai_with_retry(
            "cv_parser.generate_content",
            lambda: gemini_client.models.generate_content(
                model=settings.AI_GENERATION_MODEL,
                contents=contents,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=CVParsedData,
                    temperature=0.1,
                ),
            ),
            rate_limit_key="generate_content",
            min_interval_seconds=settings.AI_GENERATION_MIN_INTERVAL_SECONDS,
        )
        return CVParsedData.model_validate(json.loads(response.text))

    @staticmethod
    async def _build_part(image: CVImagePayload):
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(str(image.url))
            response.raise_for_status()
            return types.Part.from_bytes(data=response.content, mime_type=image.mime_type)

    @staticmethod
    def _prompt() -> str:
        return """
Ban la mot chuyen gia tuyen dung va he thong ATS chuyen nghiep.
Hay phan tich anh hoac tai lieu CV duoc cung cap, trich xuat chinh xac tat ca cac thong tin quan trong.
Neu thong tin nao khong co trong CV, hay de gia tri null hoac mang rong.
Tuyet doi khong tu bia ra thong tin.
"""
