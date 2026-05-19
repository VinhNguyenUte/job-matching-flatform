import json
from datetime import datetime

from app.common.database.sql_db import connect_sql_db
from app.features.cv_processing.embedding import CVEmbeddingPipeline
from app.features.cv_processing.parser import CVParserService
from app.features.cv_processing.repository import CVRepository
from app.features.cv_processing.schemas import CVExtractRequest, CVExtractResponse, CVImagePayload, CVParsedData


class CVProcessingService:
    @staticmethod
    async def parse_cv_images(cv_urls: list[str]) -> CVParsedData:
        images = [CVImagePayload(url=url) for url in cv_urls]
        return await CVParserService.parse_images(images)

    @staticmethod
    async def parse_cv_files(cv_files: list[dict]) -> CVParsedData:
        files = [CVImagePayload.model_validate(file) for file in cv_files]
        return await CVParserService.parse_images(files)

    @staticmethod
    async def generate_embedding(parsed: CVParsedData) -> list[float] | None:
        embedding_text = CVEmbeddingPipeline.build_embedding_text(parsed)
        return await CVEmbeddingPipeline.generate_embedding(embedding_text)

    @staticmethod
    async def extract_cv(payload: CVExtractRequest) -> CVExtractResponse:
        parsed = await CVParserService.parse_images(payload.images)
        parsed_dict = parsed.model_dump()
        parsed_dict["image_urls"] = [str(image.url) for image in payload.images]

        raw_text = json.dumps(parsed_dict, ensure_ascii=False)
        title = payload.title or CVProcessingService._default_title(parsed.full_name)
        embedding_text = CVEmbeddingPipeline.build_embedding_text(parsed)
        embedding = await CVEmbeddingPipeline.generate_embedding(embedding_text)

        if not payload.persist:
            return CVExtractResponse(
                user_id=payload.user_id,
                title=title,
                raw_text=raw_text,
                parsed_data=parsed_dict,
                embedding_created=embedding is not None,
                is_primary=payload.is_primary,
            )

        conn = await connect_sql_db()
        try:
            row = await CVRepository.insert_cv(
                conn=conn,
                user_id=payload.user_id,
                title=title,
                raw_text=raw_text,
                parsed_data=parsed_dict,
                embedding=embedding,
                is_primary=payload.is_primary,
            )
        finally:
            await conn.close()

        row_parsed_data = row["parsed_data"]
        if isinstance(row_parsed_data, str):
            row_parsed_data = json.loads(row_parsed_data)

        return CVExtractResponse(
            id=row["id"],
            user_id=row["user_id"],
            title=row["title"],
            raw_text=row["raw_text"],
            parsed_data=row_parsed_data,
            embedding_created=embedding is not None,
            is_primary=row["is_primary"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    @staticmethod
    def _default_title(full_name: str) -> str:
        name = full_name or "Unknown"
        return f"CV - {name} - {datetime.now().strftime('%Y-%m-%d')}"
