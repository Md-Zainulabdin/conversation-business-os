from openai import AsyncOpenAI

from app.core.config import settings

client = AsyncOpenAI(
    api_key=settings.GROQ_API_KEY,
    base_url=settings.GROQ_BASE_URL,
)
