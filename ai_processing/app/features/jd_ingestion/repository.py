import json
from datetime import datetime
from uuid import UUID

import asyncpg

from app.common.schemas.job import JobParsedSchema
from app.features.jd_ingestion.schemas import NormalizedJobInput


class JDRepository:
    @staticmethod
    async def find_existing_job_by_source(conn: asyncpg.Connection, source_url: str):
        return await conn.fetchrow("SELECT id FROM jobs WHERE source_url = $1", source_url)

    @staticmethod
    async def find_completed_raw_log(conn: asyncpg.Connection, content_hash: str):
        return await conn.fetchrow(
            "SELECT id FROM job_raw_logs WHERE content_hash = $1 AND processing_status = 'completed'",
            content_hash,
        )

    @staticmethod
    async def upsert_processing_raw_log(conn: asyncpg.Connection, item: NormalizedJobInput, content_hash: str):
        await conn.execute(
            """
            INSERT INTO job_raw_logs (source_url, raw_content, content_hash, processing_status)
            VALUES ($1, $2, $3, 'processing')
            ON CONFLICT (content_hash) DO UPDATE
            SET source_url = COALESCE(EXCLUDED.source_url, job_raw_logs.source_url),
                raw_content = EXCLUDED.raw_content,
                processing_status = 'processing'
            """,
            item.source_url or None,
            item.raw_text,
            content_hash,
        )

    @staticmethod
    async def mark_raw_log_completed(conn: asyncpg.Connection, content_hash: str):
        await conn.execute(
            "UPDATE job_raw_logs SET processing_status = 'completed' WHERE content_hash = $1",
            content_hash,
        )

    @staticmethod
    async def mark_raw_log_failed(conn: asyncpg.Connection, item: NormalizedJobInput, content_hash: str):
        await conn.execute(
            """
            INSERT INTO job_raw_logs (source_url, raw_content, content_hash, processing_status)
            VALUES ($1, $2, $3, 'failed')
            ON CONFLICT (content_hash) DO UPDATE
            SET source_url = COALESCE(EXCLUDED.source_url, job_raw_logs.source_url),
                raw_content = EXCLUDED.raw_content,
                processing_status = 'failed'
            """,
            item.source_url or None,
            item.raw_text,
            content_hash,
        )

    @staticmethod
    async def insert_job_graph(
        conn: asyncpg.Connection,
        item: NormalizedJobInput,
        parsed: JobParsedSchema,
        embedding: list[float],
    ) -> UUID:
        company_id = await JDRepository._get_or_create_company(conn, parsed)
        job_id = await conn.fetchval(
            """
            INSERT INTO jobs (
                company_id, title, business_unit, department, job_level, work_mode, job_type,
                vacancy_count, min_experience, target_majors, education_level_required,
                academic_support, working_hours, salary_min, salary_max, salary_unit, currency,
                salary_description, performance_review_frequency, uses_ai_in_hiring,
                is_equal_opportunity, application_deadline, description_raw, embedding,
                contact_person_name, contact_email, contact_phone, contact_phone_ext,
                application_url, hiring_process, training_details, extended_attributes,
                source_url, posted_at
            )
            VALUES (
                $1, $2, $3, $4, $5, $6, $7,
                $8, $9, $10::jsonb, $11,
                $12, $13, $14, $15, $16, $17,
                $18, $19, $20,
                $21, $22, $23, $24::vector,
                $25, $26, $27, $28,
                $29, $30::jsonb, $31::jsonb, $32::jsonb,
                $33, $34
            )
            RETURNING id
            """,
            company_id,
            parsed.title,
            parsed.business_unit,
            parsed.department,
            parsed.job_level,
            parsed.work_mode,
            parsed.job_type,
            parsed.vacancy_count,
            parsed.min_experience,
            JDRepository._json(parsed.target_majors),
            parsed.education_level_required,
            parsed.academic_support,
            parsed.working_hours,
            parsed.salary_min,
            parsed.salary_max,
            parsed.salary_unit,
            parsed.currency,
            parsed.salary_description,
            parsed.performance_review_frequency,
            parsed.uses_ai_in_hiring,
            parsed.is_equal_opportunity,
            JDRepository._parse_date(parsed.application_deadline),
            parsed.description_raw,
            JDRepository._vector(embedding),
            parsed.contact_person_name,
            parsed.contact_email,
            parsed.contact_phone,
            parsed.contact_phone_ext,
            parsed.application_url or item.source_url or None,
            JDRepository._json(parsed.hiring_process),
            JDRepository._json(parsed.training_details),
            JDRepository._json(parsed.extended_attributes),
            item.source_url or None,
            JDRepository._parse_datetime(item.posted_at),
        )

        await JDRepository._attach_skills(conn, job_id, parsed)
        await JDRepository._attach_tools(conn, job_id, parsed)
        await JDRepository._attach_languages(conn, job_id, parsed)
        await JDRepository._attach_mindsets(conn, job_id, parsed)
        await JDRepository._attach_benefits(conn, job_id, parsed)
        await JDRepository._attach_locations(conn, job_id, parsed)
        return job_id

    @staticmethod
    async def _get_or_create_company(conn: asyncpg.Connection, parsed: JobParsedSchema) -> UUID:
        company = await conn.fetchrow("SELECT id, website, industry FROM companies WHERE name = $1", parsed.company.name)
        if company:
            await conn.execute(
                """
                UPDATE companies
                SET website = COALESCE(website, $2),
                    industry = COALESCE(industry, $3)
                WHERE id = $1
                """,
                company["id"],
                parsed.company.website,
                parsed.company.industry,
            )
            return company["id"]

        return await conn.fetchval(
            """
            INSERT INTO companies (name, website, industry)
            VALUES ($1, $2, $3)
            RETURNING id
            """,
            parsed.company.name,
            parsed.company.website,
            parsed.company.industry,
        )

    @staticmethod
    async def _get_or_create_named(conn: asyncpg.Connection, table_name: str, name: str, **defaults):
        normalized = name.strip()
        if not normalized:
            return None

        existing_id = await conn.fetchval(f"SELECT id FROM {table_name} WHERE name = $1", normalized)
        if existing_id is not None:
            return existing_id

        if table_name == "benefits":
            return await conn.fetchval(
                """
                INSERT INTO benefits (name, category)
                VALUES ($1, $2)
                ON CONFLICT (name) DO UPDATE
                SET category = COALESCE(benefits.category, EXCLUDED.category)
                RETURNING id
                """,
                normalized,
                defaults.get("category"),
            )

        return await conn.fetchval(
            f"""
            INSERT INTO {table_name} (name)
            VALUES ($1)
            ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
            RETURNING id
            """,
            normalized,
        )

    @staticmethod
    async def _attach_skills(conn: asyncpg.Connection, job_id: UUID, parsed: JobParsedSchema):
        for item in JDRepository._dedupe_by_name(parsed.skills):
            skill_id = await JDRepository._get_or_create_named(conn, "skills", item.name)
            if skill_id:
                await conn.execute(
                    "INSERT INTO job_skills (job_id, skill_id, priority_level) VALUES ($1, $2, $3) ON CONFLICT DO NOTHING",
                    job_id,
                    skill_id,
                    item.priority_level,
                )

    @staticmethod
    async def _attach_tools(conn: asyncpg.Connection, job_id: UUID, parsed: JobParsedSchema):
        for item in JDRepository._dedupe_by_name(parsed.tools):
            tool_id = await JDRepository._get_or_create_named(conn, "tools", item.name)
            if tool_id:
                await conn.execute(
                    """
                    INSERT INTO job_tools (job_id, tool_id, priority_level, note)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT DO NOTHING
                    """,
                    job_id,
                    tool_id,
                    item.priority_level,
                    item.note,
                )

    @staticmethod
    async def _attach_languages(conn: asyncpg.Connection, job_id: UUID, parsed: JobParsedSchema):
        for item in JDRepository._dedupe_by_name(parsed.languages):
            language_id = await JDRepository._get_or_create_named(conn, "languages", item.name)
            if language_id:
                await conn.execute(
                    """
                    INSERT INTO job_languages (job_id, language_id, proficiency_level, priority_level)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT DO NOTHING
                    """,
                    job_id,
                    language_id,
                    item.proficiency_level,
                    item.priority_level,
                )

    @staticmethod
    async def _attach_mindsets(conn: asyncpg.Connection, job_id: UUID, parsed: JobParsedSchema):
        for mindset in JDRepository._dedupe_strings(parsed.mindsets):
            mindset_id = await JDRepository._get_or_create_named(conn, "mindsets", mindset)
            if mindset_id:
                await conn.execute(
                    "INSERT INTO job_mindsets (job_id, mindset_id) VALUES ($1, $2) ON CONFLICT DO NOTHING",
                    job_id,
                    mindset_id,
                )

    @staticmethod
    async def _attach_benefits(conn: asyncpg.Connection, job_id: UUID, parsed: JobParsedSchema):
        for item in JDRepository._dedupe_by_name(parsed.benefits):
            benefit_id = await JDRepository._get_or_create_named(conn, "benefits", item.name, category=item.category)
            if benefit_id:
                await conn.execute(
                    """
                    INSERT INTO job_benefits (job_id, benefit_id, note)
                    VALUES ($1, $2, $3)
                    ON CONFLICT DO NOTHING
                    """,
                    job_id,
                    benefit_id,
                    item.note,
                )

    @staticmethod
    async def _attach_locations(conn: asyncpg.Connection, job_id: UUID, parsed: JobParsedSchema):
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
            await conn.execute(
                """
                INSERT INTO job_locations (job_id, building, address, city, country)
                VALUES ($1, $2, $3, $4, $5)
                """,
                job_id,
                location.building,
                location.address,
                location.city,
                location.country,
            )

    @staticmethod
    def _dedupe_by_name(items):
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
    def _dedupe_strings(items: list[str]):
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
    def _json(value) -> str:
        return json.dumps(value, ensure_ascii=False)

    @staticmethod
    def _vector(value: list[float]) -> str:
        return "[" + ",".join(str(float(item)) for item in value) + "]"

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
        parsed = JDRepository._parse_datetime(value)
        return parsed.date() if parsed else None
