from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str

    MINIO_ENDPOINT: str
    MINIO_ROOT_USER: str
    MINIO_ROOT_PASSWORD: str
    MINIO_BUCKET_NAME: str = "cv-bucket"

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    GEMINI_API_KEY: str

    RABBITMQ_URL: str = "amqp://guest:guest@rabbitmq:5672/"

    class Config:
        env_file = ".env"

settings = Settings()