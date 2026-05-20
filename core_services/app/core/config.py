from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Enterprise Job Matching Core API"
    ENVIRONMENT: str = "development"  # development, staging, production
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5433/job_matching_db"
    AI_PROCESSING_URL: str = "http://localhost:8001"

    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""
    CLOUDINARY_FOLDER: str = "job-matching/cvs"

    RABBITMQ_URL: str = "amqp://guest:guest@localhost:5672/"
    RABBITMQ_HOST: str = "localhost"
    CV_QUEUE_NAME: str = "cv_processing_queue"
    CV_PROCESSING_QUEUE: str = "cv_processing_queue"

    SECRET_KEY: str = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    class Config:
        env_file = "../.env"
        extra = "ignore"


settings = Settings()
