import argparse
import asyncio
from pathlib import Path

import asyncpg

from app.core.config import settings

RESET_SQL = """
DROP TABLE IF EXISTS applications CASCADE;
DROP TABLE IF EXISTS cvs CASCADE;
DROP TABLE IF EXISTS job_raw_logs CASCADE;
DROP TABLE IF EXISTS job_locations CASCADE;
DROP TABLE IF EXISTS job_mindsets CASCADE;
DROP TABLE IF EXISTS mindsets CASCADE;
DROP TABLE IF EXISTS job_tools CASCADE;
DROP TABLE IF EXISTS tools CASCADE;
DROP TABLE IF EXISTS job_benefits CASCADE;
DROP TABLE IF EXISTS benefits CASCADE;
DROP TABLE IF EXISTS job_languages CASCADE;
DROP TABLE IF EXISTS languages CASCADE;
DROP TABLE IF EXISTS job_skills CASCADE;
DROP TABLE IF EXISTS skills CASCADE;
DROP TABLE IF EXISTS jobs CASCADE;
DROP TABLE IF EXISTS companies CASCADE;
DROP TABLE IF EXISTS users CASCADE;
"""


async def init_db(reset: bool = False):
    conn = await asyncpg.connect(settings.asyncpg_database_url)
    schema_path = Path(__file__).parent / "sql" / "schema.sql"
    schema_sql = schema_path.read_text(encoding="utf-8")
    try:
        if reset:
            await conn.execute(RESET_SQL)
        await conn.execute(schema_sql)
        print("Backend database schema initialized successfully.")
    finally:
        await conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Initialize backend-owned database schema.")
    parser.add_argument("--reset", action="store_true", help="Drop existing backend-owned tables before creating schema.")
    args = parser.parse_args()
    asyncio.run(init_db(reset=args.reset))
