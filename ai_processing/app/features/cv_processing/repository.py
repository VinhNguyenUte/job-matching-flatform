import json
from datetime import datetime
from uuid import UUID

import asyncpg


class CVRepository:
    @staticmethod
    async def mark_processing(conn: asyncpg.Connection, cv_id: UUID, cv_urls: list[str]):
        await conn.execute(
            """
            UPDATE cvs
            SET parsed_data = COALESCE(parsed_data, '{}'::jsonb) || $2::jsonb,
                updated_at = $3
            WHERE id = $1
            """,
            cv_id,
            json.dumps({"status": "processing", "cv_urls": cv_urls}, ensure_ascii=False),
            datetime.now(),
        )

    @staticmethod
    async def update_processed(
        conn: asyncpg.Connection,
        cv_id: UUID,
        raw_text: str,
        parsed_data: dict,
        embedding: list[float] | None,
    ):
        await conn.execute(
            """
            UPDATE cvs
            SET raw_text = $2,
                parsed_data = $3::jsonb,
                embedding = $4::vector,
                updated_at = $5
            WHERE id = $1
            """,
            cv_id,
            raw_text,
            json.dumps(parsed_data, ensure_ascii=False),
            CVRepository._vector(embedding) if embedding else None,
            datetime.now(),
        )

    @staticmethod
    async def mark_failed(conn: asyncpg.Connection, cv_id: UUID, cv_urls: list[str], error: str):
        await conn.execute(
            """
            UPDATE cvs
            SET parsed_data = COALESCE(parsed_data, '{}'::jsonb) || $2::jsonb,
                updated_at = $3
            WHERE id = $1
            """,
            cv_id,
            json.dumps({"status": "failed", "cv_urls": cv_urls, "error": error}, ensure_ascii=False),
            datetime.now(),
        )

    @staticmethod
    async def find_matching_jobs(conn: asyncpg.Connection, embedding: list[float] | None, limit: int = 5) -> list[dict]:
        if not embedding:
            return []

        rows = await conn.fetch(
            """
            SELECT id, title, 1 - (embedding <=> $1::vector) AS score
            FROM jobs
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> $1::vector
            LIMIT $2
            """,
            CVRepository._vector(embedding),
            limit,
        )
        return [
            {
                "id": str(row["id"]),
                "title": row["title"],
                "score": float(row["score"]) if row["score"] is not None else None,
            }
            for row in rows
        ]

    @staticmethod
    async def insert_cv(
        conn: asyncpg.Connection,
        user_id: UUID,
        title: str,
        raw_text: str,
        parsed_data: dict,
        embedding: list[float] | None,
        is_primary: bool,
    ) -> asyncpg.Record:
        return await conn.fetchrow(
            """
            INSERT INTO cvs (
                user_id, title, raw_text, parsed_data, embedding,
                is_primary, created_at, updated_at
            )
            VALUES ($1, $2, $3, $4::jsonb, $5::vector, $6, $7, $7)
            RETURNING id, user_id, title, raw_text, parsed_data, is_primary, created_at, updated_at
            """,
            user_id,
            title,
            raw_text,
            json.dumps(parsed_data, ensure_ascii=False),
            CVRepository._vector(embedding) if embedding else None,
            is_primary,
            datetime.now(),
        )

    @staticmethod
    def _vector(value: list[float]) -> str:
        return "[" + ",".join(str(float(item)) for item in value) + "]"

