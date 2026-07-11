from functools import lru_cache
from typing import List

from pydantic import AnyHttpUrl, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- App ---
    APP_NAME: str = "University Course Allocation System"
    ENVIRONMENT: str = "development"  
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = True

    # --- Security ---
    SECRET_KEY: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    ALGORITHM: str = "HS256"

    # --- CORS ---
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:4200"]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v):
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        return v

    # --- Database ---
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "allocation_user"
    POSTGRES_PASSWORD: str = "allocation_pass"
    POSTGRES_DB: str = "allocation_db"
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

    # --- AI Integration ---
    AI_PROVIDER: str = "openai"  # openai
    ANTHROPIC_API_KEY: str | None = None
    OPENAI_API_KEY: str | None = None
    AI_MODEL: str = "gpt-4o"

    AI_ASSISTANT_RATE_LIMIT_PER_MIN: int = 10


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()