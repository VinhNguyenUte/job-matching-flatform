import hashlib
from datetime import datetime
from decimal import Decimal
from typing import Iterable

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.clients.ai_service_client import ai_service_client
from app.models import (
    Benefit,
    Company,
    Job,
    JobBenefit,
    JobLanguage,
    JobLocation,
    JobMindset,
    JobRawLog,
    JobSkill,
    JobTool,
    Language,
    Mindset,
    Skill,
    Tool,
)
from app.schemas.job import JobIngestRequest, JobParsedSchema


class JDIngestionService:
    @staticmethod
    async def list_jobs(session: AsyncSession, skip: int, limit: int):
        stmt = (
            select(Job)
            .options(selectinload(Job.company), selectinload(Job.locations))
            .order_by(Job.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await session.execute(stmt)
        return [JDIngestionService._map_job(job) for job in result.scalars().all()]

    @staticmethod
    async def search_jobs(session: AsyncSession, q: str, limit: int):
        if not q.strip():
            return await JDIngestionService.list_jobs(session=session, skip=0, limit=limit)

        stmt = (
            select(Job)
            .join(Company, Job.company_id == Company.id, isouter=True)
            .options(selectinload(Job.company), selectinload(Job.locations))
            .where(or_(Job.title.ilike(f"%{q}%"), Company.name.ilike(f"%{q}%")))
            .order_by(Job.created_at.desc())
            .limit(limit)
        )
        result = await session.execute(stmt)
        return [JDIngestionService._map_job(job) for job in result.scalars().all()]

    @staticmethod
    async def preview_jobs(payload: list[JobIngestRequest]):
        return await ai_service_client.preview_jobs([item.model_dump(mode="json") for item in payload])

    @staticmethod
    async def ingest_jobs(payload: list[JobIngestRequest], session: AsyncSession):
        results = []
        success_count = 0
        skipped_count = 0
        error_count = 0

        for item in payload:
            content_hash = hashlib.sha256(item.description.encode("utf-8")).hexdigest()
            try:
                outcome = await JDIngestionService._ingest_one(
                    session=session,
                    item=item,
                    content_hash=content_hash,
                )
                results.append(outcome)
                if outcome["status"] == "success":
                    success_count += 1
                else:
                    skipped_count += 1
            except Exception as exc:
                await session.rollback()
                await JDIngestionService._mark_failed(session, item, content_hash)
                error_count += 1
                results.append({"title": item.title, "status": "failed", "detail": str(exc)})

        return {
            "success": True,
            "summary": {
                "total": len(payload),
                "success": success_count,
                "skipped": skipped_count,
                "errors": error_count,
            },
            "results": results,
        }

    @staticmethod
    async def _ingest_one(session: AsyncSession, item: JobIngestRequest, content_hash: str):
        async with session.begin():
            if item.link:
                existing_job = await session.scalar(select(Job).where(Job.source_url == item.link))
                if existing_job:
                    return {
                        "title": item.title,
                        "status": "skipped",
                        "job_id": int(existing_job.id),
                        "detail": "Job nay da ton tai theo source_url.",
                    }

            raw_log = await session.scalar(select(JobRawLog).where(JobRawLog.content_hash == content_hash))
            if raw_log and raw_log.processing_status == "completed":
                return {
                    "title": item.title,
                    "status": "skipped",
                    "detail": "JD nay da duoc xu ly truoc do.",
                }

            if raw_log is None:
                raw_log = JobRawLog(
                    source_url=item.link or None,
                    raw_content=item.description,
                    content_hash=content_hash,
                    processing_status="processing",
                )
                session.add(raw_log)
            else:
                raw_log.source_url = item.link or raw_log.source_url
                raw_log.raw_content = item.description
                raw_log.processing_status = "processing"
            await session.flush()

            ai_response = await ai_service_client.process_job(item.model_dump(mode="json"))
            parsed = JobParsedSchema.model_validate(ai_response["parsed_data"])
            embedding = ai_response["embedding"]

            company = await JDIngestionService._get_or_create_company(session, parsed)
            job = Job(
                company_id=company.id,
                title=parsed.title,
                business_unit=parsed.business_unit,
                department=parsed.department,
                job_level=parsed.job_level,
                work_mode=parsed.work_mode,
                job_type=parsed.job_type,
                vacancy_count=parsed.vacancy_count,
                min_experience=parsed.min_experience,
                target_majors=parsed.target_majors,
                education_level_required=parsed.education_level_required,
                academic_support=parsed.academic_support,
                working_hours=parsed.working_hours,
                salary_min=parsed.salary_min,
                salary_max=parsed.salary_max,
                salary_unit=parsed.salary_unit,
                currency=parsed.currency,
                salary_description=parsed.salary_description,
                performance_review_frequency=parsed.performance_review_frequency,
                uses_ai_in_hiring=parsed.uses_ai_in_hiring,
                is_equal_opportunity=parsed.is_equal_opportunity,
                application_deadline=JDIngestionService._parse_date(parsed.application_deadline),
                description_raw=parsed.description_raw,
                embedding=embedding,
                contact_person_name=parsed.contact_person_name,
                contact_email=parsed.contact_email,
                contact_phone=parsed.contact_phone,
                contact_phone_ext=parsed.contact_phone_ext,
                application_url=parsed.application_url or item.link or None,
                hiring_process=parsed.hiring_process,
                training_details=parsed.training_details,
                extended_attributes=parsed.extended_attributes,
                source_url=item.link or None,
                posted_at=JDIngestionService._parse_datetime(item.post_time),
            )
            session.add(job)
            await session.flush()

            await JDIngestionService._attach_skills(session, job.id, parsed)
            await JDIngestionService._attach_tools(session, job.id, parsed)
            await JDIngestionService._attach_languages(session, job.id, parsed)
            await JDIngestionService._attach_mindsets(session, job.id, parsed)
            await JDIngestionService._attach_benefits(session, job.id, parsed)
            await JDIngestionService._attach_locations(session, job.id, parsed)

            raw_log.processing_status = "completed"
            return {"title": item.title, "status": "success", "job_id": int(job.id)}

    @staticmethod
    async def _mark_failed(session: AsyncSession, item: JobIngestRequest, content_hash: str):
        async with session.begin():
            raw_log = await session.scalar(select(JobRawLog).where(JobRawLog.content_hash == content_hash))
            if raw_log is None:
                raw_log = JobRawLog(
                    source_url=item.link or None,
                    raw_content=item.description,
                    content_hash=content_hash,
                )
                session.add(raw_log)
            raw_log.processing_status = "failed"

    @staticmethod
    async def _get_or_create_company(session: AsyncSession, parsed: JobParsedSchema):
        company = await session.scalar(select(Company).where(Company.name == parsed.company.name))
        if company is None:
            company = Company(
                name=parsed.company.name,
                website=parsed.company.website,
                industry=parsed.company.industry,
            )
            session.add(company)
            await session.flush()
            return company

        if not company.website and parsed.company.website:
            company.website = parsed.company.website
        if not company.industry and parsed.company.industry:
            company.industry = parsed.company.industry
        return company

    @staticmethod
    async def _get_or_create_named(session: AsyncSession, model, name: str, **defaults):
        normalized = name.strip()
        entity = await session.scalar(select(model).where(model.name == normalized))
        if entity is None:
            entity = model(name=normalized, **defaults)
            session.add(entity)
            await session.flush()
        return entity

    @staticmethod
    async def _attach_skills(session: AsyncSession, job_id: int, parsed: JobParsedSchema):
        for skill_item in JDIngestionService._dedupe_by_name(parsed.skills):
            skill = await JDIngestionService._get_or_create_named(session, Skill, skill_item.name)
            session.add(JobSkill(job_id=job_id, skill_id=skill.id, priority_level=skill_item.priority_level))

    @staticmethod
    async def _attach_tools(session: AsyncSession, job_id: int, parsed: JobParsedSchema):
        for tool_item in JDIngestionService._dedupe_by_name(parsed.tools):
            tool = await JDIngestionService._get_or_create_named(session, Tool, tool_item.name)
            session.add(
                JobTool(
                    job_id=job_id,
                    tool_id=tool.id,
                    priority_level=tool_item.priority_level,
                    note=tool_item.note,
                )
            )

    @staticmethod
    async def _attach_languages(session: AsyncSession, job_id: int, parsed: JobParsedSchema):
        for lang_item in JDIngestionService._dedupe_by_name(parsed.languages):
            language = await JDIngestionService._get_or_create_named(session, Language, lang_item.name)
            session.add(
                JobLanguage(
                    job_id=job_id,
                    language_id=language.id,
                    proficiency_level=lang_item.proficiency_level,
                    priority_level=lang_item.priority_level,
                )
            )

    @staticmethod
    async def _attach_mindsets(session: AsyncSession, job_id: int, parsed: JobParsedSchema):
        for mindset_name in JDIngestionService._dedupe_strings(parsed.mindsets):
            mindset = await JDIngestionService._get_or_create_named(session, Mindset, mindset_name)
            session.add(JobMindset(job_id=job_id, mindset_id=mindset.id))

    @staticmethod
    async def _attach_benefits(session: AsyncSession, job_id: int, parsed: JobParsedSchema):
        for benefit_item in JDIngestionService._dedupe_by_name(parsed.benefits):
            benefit = await JDIngestionService._get_or_create_named(
                session,
                Benefit,
                benefit_item.name,
                category=benefit_item.category,
            )
            if benefit.category is None and benefit_item.category:
                benefit.category = benefit_item.category
            session.add(JobBenefit(job_id=job_id, benefit_id=benefit.id, note=benefit_item.note))

    @staticmethod
    async def _attach_locations(session: AsyncSession, job_id: int, parsed: JobParsedSchema):
        seen = set()
        for location in parsed.locations:
            key = (
                (location.building or "").strip().lower(),
                (location.address or "").strip().lower(),
                (location.city or "").strip().lower(),
                (location.country or "Vietnam").strip().lower(),
            )
            if key in seen:
                continue
            seen.add(key)
            session.add(
                JobLocation(
                    job_id=job_id,
                    building=location.building,
                    address=location.address,
                    city=location.city,
                    country=location.country,
                )
            )

    @staticmethod
    def _dedupe_by_name(items: Iterable):
        seen = set()
        deduped = []
        for item in items:
            key = item.name.strip().lower()
            if not key or key in seen:
                continue
            seen.add(key)
            deduped.append(item)
        return deduped

    @staticmethod
    def _dedupe_strings(items: Iterable[str]):
        seen = set()
        deduped = []
        for item in items:
            key = item.strip().lower()
            if not key or key in seen:
                continue
            seen.add(key)
            deduped.append(item.strip())
        return deduped

    @staticmethod
    def _parse_datetime(value: str | None):
        if not value:
            return None
        normalized = value.strip().replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(normalized)
        except ValueError:
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
                try:
                    return datetime.strptime(normalized, fmt)
                except ValueError:
                    continue
        return None

    @staticmethod
    def _parse_date(value: str | None):
        parsed = JDIngestionService._parse_datetime(value)
        return parsed.date() if parsed else None

    @staticmethod
    def _decimal_to_float(value):
        if value is None:
            return None
        if isinstance(value, Decimal):
            return float(value)
        return value

    @staticmethod
    def _map_job(job: Job):
        city = job.locations[0].city if job.locations else None
        return {
            "id": int(job.id),
            "title": job.title,
            "company_name": job.company.name if job.company else "Unknown",
            "city": city,
            "job_level": job.job_level,
            "work_mode": job.work_mode,
            "salary_min": JDIngestionService._decimal_to_float(job.salary_min),
            "salary_max": JDIngestionService._decimal_to_float(job.salary_max),
            "currency": job.currency,
            "source_url": job.source_url,
            "posted_at": job.posted_at,
            "created_at": job.created_at,
        }
