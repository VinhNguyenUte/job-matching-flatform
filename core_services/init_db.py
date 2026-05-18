import argparse
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()


def build_database_url() -> str:
    postgres_user = os.getenv("POSTGRES_USER")
    postgres_password = os.getenv("POSTGRES_PASSWORD")
    postgres_host = os.getenv("POSTGRES_HOST")
    postgres_port = os.getenv("POSTGRES_PORT", "5432")
    postgres_db = os.getenv("POSTGRES_DB")

    missing_keys = [
        key
        for key, value in {
            "POSTGRES_USER": postgres_user,
            "POSTGRES_PASSWORD": postgres_password,
            "POSTGRES_HOST": postgres_host,
            "POSTGRES_DB": postgres_db,
        }.items()
        if not value
    ]
    if missing_keys:
        raise RuntimeError(f"Missing database configuration in .env: {', '.join(missing_keys)}")

    if os.path.exists("/.dockerenv") and postgres_host in {"localhost", "127.0.0.1"}:
        postgres_host = "localhost"

    return f"postgresql://{postgres_user}:{postgres_password}@{postgres_host}:{postgres_port}/{postgres_db}"


DATABASE_URL_FROM_POSTGRES_ENV = build_database_url()
# app.core.database requires DATABASE_URL at import time. Force it to match POSTGRES_* for init_db.
os.environ["DATABASE_URL"] = DATABASE_URL_FROM_POSTGRES_ENV

from app.core.database import Base  # noqa: E402
from app.models import (  # noqa: E402,F401 - imported so SQLAlchemy registers all tables
    Application,
    Benefit,
    CV,
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
    User,
)

DROP_ORDER = [
    "applications",
    "job_locations",
    "job_skills",
    "job_tools",
    "job_languages",
    "job_benefits",
    "job_mindsets",
    "cvs",
    "jobs",
    "job_raw_logs",
    "skills",
    "tools",
    "languages",
    "benefits",
    "mindsets",
    "companies",
    "users",
]


def init_db(reset: bool = False) -> None:
    engine = create_engine(DATABASE_URL_FROM_POSTGRES_ENV, pool_pre_ping=True)
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))

        if reset:
            for table_name in DROP_ORDER:
                conn.execute(text(f"DROP TABLE IF EXISTS {table_name} CASCADE"))

        Base.metadata.create_all(bind=conn)

    action = "reset and initialized" if reset else "initialized"
    print("Database schema " + action + " successfully using POSTGRES_* from .env.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Initialize JobMatch database schema.")
    parser.add_argument("--reset", action="store_true", help="Drop existing tables before creating schema.")
    args = parser.parse_args()
    init_db(reset=args.reset)
