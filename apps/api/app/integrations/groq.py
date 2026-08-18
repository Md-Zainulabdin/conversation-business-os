import asyncio
import io
import logging
import os
import re

from groq import AsyncGroq

from app.core.config import settings

_client: AsyncGroq | None = None

_AUDIO_CONTENT_TYPES = {
    "audio/mpeg": "mp3",
    "audio/mp3": "mp3",
    "audio/wav": "wav",
    "audio/x-wav": "wav",
    "audio/m4a": "m4a",
    "audio/mp4": "mp4",
    "audio/webm": "webm",
    "audio/ogg": "ogg",
    "application/ogg": "ogg",
}

_SUPPORTED_EXTENSIONS = {"mp3", "wav", "m4a", "mp4", "webm", "ogg"}

_AUDIO_MAGIC_BYTES = {
    "mp3": [b"ID3", b"\xff\xfb", b"\xff\xf3", b"\xff\xf2"],
    "wav": [b"RIFF"],
    "m4a": [b"ftypM4A", b"ftypmp4", b"ftypisom"],
    "mp4": [b"ftypM4A", b"ftypmp4", b"ftypisom"],
    "webm": [b"\x1a\x45\xdf\xa3"],
    "ogg": [b"OggS"],
}

MAX_AUDIO_BYTES = 25 * 1024 * 1024

logger = logging.getLogger(__name__)


def verify_audio_magic_bytes(file_bytes: bytes, extension: str) -> bool:
    """Verify file magic bytes match the expected audio format."""
    if len(file_bytes) < 4:
        return False
    magic_patterns = _AUDIO_MAGIC_BYTES.get(extension.lower(), [])
    if not magic_patterns:
        return True
    for pattern in magic_patterns:
        if file_bytes.startswith(pattern):
            return True
        if extension.lower() in ("m4a", "mp4") and pattern in file_bytes[:12]:
            return True
    return False


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal and use safe characters."""
    base = os.path.basename(filename)
    base = re.sub(r"[^\w.\-]", "_", base)
    if "." in base:
        name, ext = base.rsplit(".", 1)
        ext = ext.lower()
        if ext in _SUPPORTED_EXTENSIONS:
            return f"{name[:100]}.{ext}"
    return f"{base[:100]}.mp3"


def get_groq_client() -> AsyncGroq:
    global _client
    if _client is None:
        _client = AsyncGroq(api_key=settings.GROQ_API_KEY, timeout=30.0)
    return _client


def set_groq_client(client: AsyncGroq | None) -> None:
    """Set the Groq client for testing. Pass None to reset to default."""
    global _client
    _client = client


def audio_extension(content_type: str | None) -> str | None:
    if not content_type:
        return None
    base = content_type.lower().split(";")[0].strip()
    return _AUDIO_CONTENT_TYPES.get(base)


async def transcribe_audio(
    client: AsyncGroq,
    file_bytes: bytes,
    filename: str,
    *,
    content_type: str | None = None,
) -> str:
    if len(file_bytes) > MAX_AUDIO_BYTES:
        raise ValueError("Audio file is too large")
    if not file_bytes:
        raise ValueError("Audio file is empty")

    safe_filename = sanitize_filename(filename)
    extension = audio_extension(content_type)
    if not extension:
        extension = safe_filename.rsplit(".", 1)[-1].lower() if "." in safe_filename else "mp3"
    if extension not in _SUPPORTED_EXTENSIONS:
        raise ValueError("Unsupported audio format")

    if not verify_audio_magic_bytes(file_bytes, extension):
        logger.warning("Audio magic bytes mismatch: filename=%s extension=%s", filename, extension)
        raise ValueError("Audio file format does not match content")

    logger.info(
        "Starting transcription: filename=%s extension=%s size=%d",
        safe_filename,
        extension,
        len(file_bytes),
    )

    async def _create_transcription() -> str:
        transcription = await client.audio.transcriptions.create(
            model=settings.GROQ_WHISPER_MODEL,
            file=(
                safe_filename,
                io.BytesIO(file_bytes),
                content_type or f"audio/{extension}",
            ),
            response_format="json",
        )
        return transcription.text

    try:
        result = await asyncio.wait_for(
            _create_transcription(), timeout=settings.TRANSCRIPTION_TIMEOUT_SECONDS
        )
        logger.info("Transcription completed: chars=%d", len(result))
        return result
    except TimeoutError as exc:
        logger.error(
            "Transcription timed out after %ds", settings.TRANSCRIPTION_TIMEOUT_SECONDS
        )
        raise ValueError("Transcription timed out") from exc
