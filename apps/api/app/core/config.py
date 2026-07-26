from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "CBO"
    VERSION: str = "0.1.0"

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/cbo"
    REDIS_URL: str = "redis://localhost:6379"

    SECRET_KEY: str = "change-this-to-a-random-secret-key"

    GROQ_API_KEY: str = ""
    GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"

    WHATSAPP_API_TOKEN: str = ""
    WHATSAPP_PHONE_NUMBER_ID: str = ""
    WHATSAPP_VERIFY_TOKEN: str = ""

    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000"]

    model_config = {"env_file": ".env", "case_sensitive": True}


settings = Settings()
