"""In-memory conversation history and execute idempotency keys.

Both are short-lived, process-local stores. They are intentionally not
persisted (no database tables) so the MVP stays simple; a restart simply
loses the in-memory state.
"""

import threading
import time
from collections import deque

from app.schemas.ai import AIExecuteResponse

_HISTORY_MAX_MESSAGES = 6
_HISTORY_TTL_SECONDS = 600
_MAX_SESSIONS = 500
_IDEMPOTENCY_TTL_SECONDS = 1800


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

    def push(self, conversation_id: str, role: str, text: str) -> None:
        now = time.monotonic()
        with self._lock:
            self._prune_locked(now)
            entry = self._sessions.get(conversation_id)
            if entry is None:
                history = deque(maxlen=self._max_messages)
                self._sessions[conversation_id] = (now, history)
            else:
                _, history = entry
                self._sessions[conversation_id] = (now, history)
            history.append((role, text))

    def get_history(self, conversation_id: str) -> list[tuple[str, str]]:
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

    def get(self, key: str) -> AIExecuteResponse | None:
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

    def set(self, key: str, result: AIExecuteResponse) -> None:
        with self._lock:
            self._results[key] = (time.monotonic(), result)


ai_session_store = AiSessionStore()
idempotency_store = IdempotencyStore()