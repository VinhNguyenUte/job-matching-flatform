import asyncpg

from app.common.config import settings


async def connect_sql_db() -> asyncpg.Connection:
    return await asyncpg.connect(settings.database_url)
