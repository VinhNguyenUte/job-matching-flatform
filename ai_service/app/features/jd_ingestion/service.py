from app.common.schemas.job import JobLocationSchema, JobParsedSchema
from app.features.jd_ingestion.embedder import JDEmbeddingService
from app.features.jd_ingestion.parser import JDParsingService
from app.features.jd_ingestion.schemas import IngestJobRequest


class JDProcessingService:
    @staticmethod
    async def preview_jobs(payload: list[IngestJobRequest]) -> list[JobParsedSchema]:
        previews = []
        for item in payload:
            previews.append(await JDProcessingService.parse_job(item))
        return previews

    @staticmethod
    async def process_job(item: IngestJobRequest) -> dict:
        parsed = await JDProcessingService.parse_job(item)
        embedding_text = JDEmbeddingService.contextualize_job(parsed)
        embedding = await JDEmbeddingService.generate_embedding(embedding_text)
        return {
            "parsed_data": parsed.model_dump(mode="json"),
            "embedding_text": embedding_text,
            "embedding": embedding,
        }

    @staticmethod
    async def parse_job(item: IngestJobRequest) -> JobParsedSchema:
        parsed = await JDParsingService.parse_job_description(item.description)
        parsed.title = item.title
        parsed.company.name = item.company
        parsed.description_raw = item.description
        parsed.application_url = parsed.application_url or item.link or None
        if item.location and not parsed.locations:
            parsed.locations = [JobLocationSchema(city=item.location, country="Vietnam")]
        parsed.extended_attributes = {
            **parsed.extended_attributes,
            "payload_location": item.location or None,
            "payload_post_time": item.post_time or None,
            "payload_link": item.link or None,
        }
        return parsed
