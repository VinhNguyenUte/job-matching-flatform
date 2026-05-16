from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    AI_PROVIDER: str = "gemini"
    AI_GENERATION_MODEL: str = "gemini-2.5-flash"
    AI_EMBEDDING_MODEL: str | None = None
    GEMINI_API_KEY: str | None = None
    VERTEX_API_KEY: str | None = None
    VERTEX_GEMINI_APIKEY: str | None = None
    GOOGLE_CLOUD_PROJECT: str | None = None
    VERTEX_PROJECT_ID: str | None = None
    GOOGLE_CLOUD_LOCATION: str = "us-central1"
    VERTEX_LOCATION: str | None = None
    GOOGLE_APPLICATION_CREDENTIALS: str | None = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def normalized_ai_provider(self) -> str:
        return self.AI_PROVIDER.strip().lower()

    @property
    def vertex_api_key(self) -> str | None:
        return self.VERTEX_API_KEY or self.VERTEX_GEMINI_APIKEY

    @property
    def vertex_project_id(self) -> str | None:
        return self.GOOGLE_CLOUD_PROJECT or self.VERTEX_PROJECT_ID

    @property
    def vertex_location(self) -> str:
        return self.VERTEX_LOCATION or self.GOOGLE_CLOUD_LOCATION

    @property
    def embedding_model(self) -> str:
        if self.AI_EMBEDDING_MODEL:
            return self.AI_EMBEDDING_MODEL
        return "gemini-embedding-001"


settings = Settings()
