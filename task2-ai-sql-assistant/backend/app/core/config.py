from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "AI SQL Assistant"
    ENVIRONMENT: str = "development"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = True

    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:4201"]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v):
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        return v

    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "sqlassistant_user"
    POSTGRES_PASSWORD: str = "sqlassistant_pass"
    POSTGRES_DB: str = "sqlassistant_db"
    DATABASE_URL: str | None = None

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v, info):
        if isinstance(v, str) and v:
            return v
        data = info.data
        return (
            f"postgresql+asyncpg://{data.get('POSTGRES_USER')}:{data.get('POSTGRES_PASSWORD')}"
            f"@{data.get('POSTGRES_SERVER')}:{data.get('POSTGRES_PORT')}/{data.get('POSTGRES_DB')}"
        )

    @property
    def SYNC_DATABASE_URL(self) -> str:
        return self.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql+psycopg2://")
    READONLY_DB_USER: str = "sqlassistant_readonly"
    READONLY_DB_PASSWORD: str = "sqlassistant_readonly_pass"

    @property
    def READONLY_DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.READONLY_DB_USER}:{self.READONLY_DB_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    DATASET_SCHEMA: str = "datasets"

    MAX_RESULT_ROWS: int = 500
    QUERY_TIMEOUT_SECONDS: int = 10
    MAX_UPLOAD_ROWS: int = 200_000
    MAX_UPLOAD_SIZE_MB: int = 25

    # --- AI Integration ---
    ANTHROPIC_API_KEY: str | None = None
    OPENAI_API_KEY: str | None = None
    AI_MODEL: str = "gpt-4o"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()