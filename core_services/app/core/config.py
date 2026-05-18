from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Enterprise Job Matching Core API"
    DATABASE_URL: str
    AI_PROCESSING_URL: str = "http://ai_processing:8001"

    # MinIO Object Storage
    MINIO_ENDPOINT: str
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str
    MINIO_BUCKET_CV: str = "user-cvs"

    # RabbitMQ Broker
    RABBITMQ_URL: str
    CV_QUEUE_NAME: str = "cv_processing_queue"

    # JWT Security
    SECRET_KEY: str = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    class Config:
        env_file = "../.env"
        extra = "ignore"


settings = Settings()
