import httpx
from fastapi import HTTPException

from app.core.config import settings


class AIServiceClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    async def preview_jobs(self, payload):
        return await self._request("POST", "/api/jobs/preview", json=payload)

    async def process_job(self, payload):
        return await self._request("POST", "/api/jobs/process", json=payload)

    async def _request(self, method: str, path: str, **kwargs):
        try:
            async with httpx.AsyncClient(base_url=self.base_url, timeout=180.0) as client:
                response = await client.request(method, path, **kwargs)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text
            try:
                detail = exc.response.json().get("detail", detail)
            except ValueError:
                pass
            raise HTTPException(status_code=exc.response.status_code, detail=detail) from exc
        except httpx.RequestError as exc:
            raise HTTPException(status_code=503, detail=f"AI service unavailable: {exc}") from exc


ai_service_client = AIServiceClient(settings.AI_SERVICE_URL)
