"""Conversation history and execute idempotency keys.

Backed by Redis (safe across multiple workers) when a Redis server is
reachable; otherwise falls back to process-local in-memory storage so
development and tests keep working without Redis.
"""

import asyncio
import logging
import threading
import time
from collections import deque

from redis.asyncio import Redis

from app.core.config import settings
from app.schemas.ai import AIExecuteResponse

logger = logging.getLogger(__name__)

_HISTORY_MAX_MESSAGES = 6
_HISTORY_TTL_SECONDS = 600
_MAX_SESSIONS = 500
_IDEMPOTENCY_TTL_SECONDS = 1800

_SESSION_KEY = "cbo:session:{key}"
_IDEMPOTENCY_KEY = "cbo:idem:{key}"

_SEPARATOR = "\x00"


class AiSessionStore:
    def __init__(
        self,
        max_messages: int = _HISTORY_MAX_MESSAGES,
        ttl_seconds: float = _HISTORY_TTL_SECONDS,
        max_sessions: int = _MAX_SESSIONS,
    ):
        self._max_messages = max_messages
        self._ttl_seconds = ttl_seconds
        self._max_sessions = max_sessions
        self._sessions: dict[str, tuple[float, deque]] = {}
        self._lock = threading.Lock()
        self._redis: Redis | None = None
        self._redis_checked = False

    async def _get_redis(self) -> Redis | None:
        if self._redis_checked:
            return self._redis
        self._redis_checked = True
        if not settings.REDIS_URL:
            return None
        try:
            client = Redis.from_url(settings.REDIS_URL, decode_responses=True)
            await asyncio.wait_for(client.ping(), timeout=2)
            self._redis = client
        except Exception:
            logger.warning("Redis unavailable; using in-memory session store")
            self._redis = None
        return self._redis

    def _prune_locked(self, now: float) -> None:
        stale = [
            key
            for key, (updated, _) in self._sessions.items()
            if now - updated > self._ttl_seconds
        ]
        for key in stale:
            del self._sessions[key]
        if len(self._sessions) > self._max_sessions:
            oldest = sorted(
                self._sessions, key=lambda k: self._sessions[k][0]
            )[: len(self._sessions) - self._max_sessions]
            for key in oldest:
                del self._sessions[key]

    async def push(self, conversation_id: str, role: str, text: str) -> None:
        redis = await self._get_redis()
        if redis is not None:
            try:
                key = _SESSION_KEY.format(key=conversation_id)
                pipe = redis.pipeline()
                pipe.rpush(key, f"{role}{_SEPARATOR}{text}")
                pipe.ltrim(key, -self._max_messages, -1)
                pipe.expire(key, int(self._ttl_seconds))
                await pipe.execute()
                return
            except Exception:
                logger.warning(
                    "Redis session push failed; using in-memory fallback", exc_info=True
                )
                self._redis = None

        now = time.monotonic()
        with self._lock:
            self._prune_locked(now)
            entry = self._sessions.get(conversation_id)
            if entry is None:
                history = deque(maxlen=self._max_messages)
            else:
                _, history = entry
            history.append((role, text))
            self._sessions[conversation_id] = (now, history)

    async def get_history(self, conversation_id: str) -> list[tuple[str, str]]:
        redis = await self._get_redis()
        if redis is not None:
            try:
                key = _SESSION_KEY.format(key=conversation_id)
                raw = await redis.lrange(key, 0, -1)
                if not raw:
                    return []
                entries = []
                for item in raw:
                    if _SEPARATOR in item:
                        role, text = item.split(_SEPARATOR, 1)
                        entries.append((role, text))
                return entries
            except Exception:
                logger.warning(
                    "Redis session read failed; using in-memory fallback", exc_info=True
                )
                self._redis = None

        now = time.monotonic()
        with self._lock:
            entry = self._sessions.get(conversation_id)
            if entry is None:
                return []
            updated, history = entry
            if now - updated > self._ttl_seconds:
                del self._sessions[conversation_id]
                return []
            self._sessions[conversation_id] = (now, history)
            return list(history)


class IdempotencyStore:
    def __init__(self, ttl_seconds: float = _IDEMPOTENCY_TTL_SECONDS):
        self._ttl_seconds = ttl_seconds
        self._results: dict[str, tuple[float, AIExecuteResponse]] = {}
        self._lock = threading.Lock()
        self._redis: Redis | None = None
        self._redis_checked = False

    async def _get_redis(self) -> Redis | None:
        if self._redis_checked:
            return self._redis
        self._redis_checked = True
        if not settings.REDIS_URL:
            return None
        try:
            client = Redis.from_url(settings.REDIS_URL, decode_responses=True)
            await asyncio.wait_for(client.ping(), timeout=2)
            self._redis = client
        except Exception:
            logger.warning("Redis unavailable; using in-memory idempotency store")
            self._redis = None
        return self._redis

    async def get(self, key: str) -> AIExecuteResponse | None:
        redis = await self._get_redis()
        if redis is not None:
            try:
                raw = await redis.get(_IDEMPOTENCY_KEY.format(key=key))
                if raw is None:
                    return None
                return AIExecuteResponse.model_validate_json(raw)
            except Exception:
                logger.warning(
                    "Redis idempotency read failed; using in-memory fallback",
                    exc_info=True,
                )
                self._redis = None

        now = time.monotonic()
        with self._lock:
            entry = self._results.get(key)
            if not entry:
                return None
            created, result = entry
            if now - created > self._ttl_seconds:
                del self._results[key]
                return None
            return result

    async def set(self, key: str, result: AIExecuteResponse) -> None:
        redis = await self._get_redis()
        if redis is not None:
            try:
                await redis.set(
                    _IDEMPOTENCY_KEY.format(key=key),
                    result.model_dump_json(),
                    ex=int(self._ttl_seconds),
                )
                return
            except Exception:
                logger.warning(
                    "Redis idempotency write failed; using in-memory fallback",
                    exc_info=True,
                )
                self._redis = None

        with self._lock:
            self._results[key] = (time.monotonic(), result)


ai_session_store = AiSessionStore()
idempotency_store = IdempotencyStore()