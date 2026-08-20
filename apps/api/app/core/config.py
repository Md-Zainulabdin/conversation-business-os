from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings

BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    PROJECT_NAME: str = "CBO"
    VERSION: str = "0.1.0"

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/cbo"
    REDIS_URL: str = "redis://localhost:6379"

    SECRET_KEY: str = ""
    ENVIRONMENT: str = "development"

    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "openai/gpt-oss-120b"
    GROQ_WHISPER_MODEL: str = "whisper-large-v3-turbo"

    TRANSCRIPTION_TIMEOUT_SECONDS: float = 60.0
    CHAT_COMPLETION_TIMEOUT_SECONDS: float = 30.0

    FUZZY_MATCH_THRESHOLD: float = 0.78
    FUZZY_TIE_THRESHOLD: float = 0.05

    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000"]

    AI_RATE_LIMIT_PER_MINUTE: int = 30
    AI_RATE_LIMIT_PER_HOUR: int = 200

    model_config = {
        "env_file": BACKEND_DIR / ".env",
        "case_sensitive": True,
    }

    @field_validator("DATABASE_URL")
    @classmethod
    def ensure_asyncpg_driver(cls, value: str) -> str:
        if value.startswith("postgresql://"):
            return value.replace("postgresql://", "postgresql+asyncpg://", 1)
        return value

    def validate_security(self) -> None:
        if self.ENVIRONMENT == "production" and not self.SECRET_KEY:
            raise RuntimeError(
                "SECRET_KEY must be set to a strong random value in production"
            )


settings = Settings()
settings.validate_security()
