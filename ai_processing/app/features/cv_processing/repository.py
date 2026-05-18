import json
from datetime import datetime
from uuid import UUID

import asyncpg


class CVRepository:
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

