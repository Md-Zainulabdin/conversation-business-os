from pathlib import Path

from pydantic_settings import BaseSettings

BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    PROJECT_NAME: str = "CBO"
    VERSION: str = "0.1.0"

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/cbo"
    REDIS_URL: str = "redis://localhost:6379"

    SECRET_KEY: str = "change-this-to-a-random-secret-key"

    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "openai/gpt-oss-120b"

    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000"]

    model_config = {
        "env_file": BACKEND_DIR / ".env",
        "case_sensitive": True,
    }


settings = Settings()
