import hashlib

from app.common.database.sql_db import connect_sql_db
from app.common.schemas.job import JobLocationSchema, JobParsedSchema
from app.features.jd_ingestion.embedding import JDEmbeddingPipeline
from app.features.jd_ingestion.input_adapter import JDInputAdapter
from app.features.jd_ingestion.knowledge_graph import JDTemporaryKnowledgeGraph
from app.features.jd_ingestion.ner import JDNERService
from app.features.jd_ingestion.normalizer import JDNormalizerService
from app.features.jd_ingestion.repository import JDRepository
from app.features.jd_ingestion.schemas import IngestJobRequest, JobIngestResponse, NormalizedJobInput


class JDProcessingService:
    @staticmethod
    async def preview_jobs(payload: list[IngestJobRequest]) -> list[JobParsedSchema]:
        previews = []
        for item in payload:
            normalized = JDInputAdapter.normalize(item)
            pipeline = await JDProcessingService.run_pipeline(normalized)
            previews.append(pipeline["parsed"])
        return previews

    @staticmethod
    async def ingest_jobs(payload: list[IngestJobRequest]) -> JobIngestResponse:
        results = []
        success_count = 0
        skipped_count = 0
        error_count = 0

        for item in payload:
            normalized = None
            content_hash = None
            try:
                normalized = JDInputAdapter.normalize(item)
                content_hash = hashlib.sha256(normalized.raw_text.encode("utf-8")).hexdigest()
                outcome = await JDProcessingService._ingest_one(item=normalized, content_hash=content_hash)
                results.append(outcome)
                if outcome["status"] == "success":
                    success_count += 1
                else:
                    skipped_count += 1
            except Exception as exc:
                if normalized and content_hash:
                    try:
                        await JDProcessingService._mark_failed(normalized, content_hash)
                    except Exception:
                        pass
                error_count += 1
                results.append({"title": getattr(item, "title", None) or "Unknown", "status": "failed", "detail": str(exc)})

        return JobIngestResponse(
            success=True,
            summary={
                "total": len(payload),
                "success": success_count,
                "skipped": skipped_count,
                "errors": error_count,
            },
            results=results,
        )

    @staticmethod
    async def _ingest_one(item: NormalizedJobInput, content_hash: str) -> dict:
        conn = await connect_sql_db()
        transaction = conn.transaction()
        await transaction.start()
        try:
            if item.source_url:
                existing_job = await JDRepository.find_existing_job_by_source(conn, item.source_url)
                if existing_job:
                    await transaction.commit()
                    return {
                        "title": item.title or "Unknown",
                        "status": "skipped",
                        "job_id": existing_job["id"],
                        "detail": "Job nay da ton tai theo source_url.",
                    }

            completed_raw_log = await JDRepository.find_completed_raw_log(conn, content_hash)
            if completed_raw_log:
                await transaction.commit()
                return {
                    "title": item.title or "Unknown",
                    "status": "skipped",
                    "detail": "JD nay da duoc xu ly truoc do.",
                }

            await JDRepository.upsert_processing_raw_log(conn, item, content_hash)
            pipeline = await JDProcessingService.run_pipeline(item)
            job_id = await JDRepository.insert_job_graph(
                conn=conn,
                item=item,
                parsed=pipeline["parsed"],
                embedding=pipeline["embedding"],
            )
            await JDRepository.mark_raw_log_completed(conn, content_hash)
            await transaction.commit()
            return {"title": pipeline["parsed"].title, "status": "success", "job_id": job_id}
        except Exception:
            await transaction.rollback()
            raise
        finally:
            await conn.close()

    @staticmethod
    async def _mark_failed(item: NormalizedJobInput, content_hash: str):
        conn = await connect_sql_db()
        try:
            await JDRepository.mark_raw_log_failed(conn, item, content_hash)
        finally:
            await conn.close()

    @staticmethod
    async def run_pipeline(item: NormalizedJobInput) -> dict:
        ner = await JDNERService.extract_entities(item.raw_text)
        embedding_text = JDEmbeddingPipeline.build_embedding_text(item.raw_text, ner)
        embedding = await JDEmbeddingPipeline.generate_embedding(embedding_text)
        graph = JDTemporaryKnowledgeGraph.build(ner)
        parsed = await JDNormalizerService.normalize(item.raw_text, ner, graph, embedding_text)
        if item.title:
            parsed.title = item.title
        if item.company:
            parsed.company.name = item.company
        parsed.description_raw = item.raw_text
        parsed.application_url = parsed.application_url or item.source_url or None
        if item.location and not parsed.locations:
            parsed.locations = [JobLocationSchema(city=item.location, country="Vietnam")]
        parsed.extended_attributes = {
            **parsed.extended_attributes,
            "payload_location": item.location or None,
            "payload_post_time": item.posted_at or None,
            "payload_link": item.source_url or None,
            "source_type": item.source_type,
            "source_author": item.source_author,
            "external_id": item.external_id,
            "source_metadata": item.source_metadata,
        }
        return {
            "parsed": parsed,
            "ner": ner,
            "embedding_text": embedding_text,
            "embedding": embedding,
            "knowledge_graph": graph,
        }
