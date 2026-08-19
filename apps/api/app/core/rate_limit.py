"""Rate limiting utilities for API endpoints."""

import time
from collections import defaultdict
from dataclasses import dataclass, field
from threading import Lock

from app.core.config import settings


@dataclass
class RateLimitWindow:
    requests: list[float] = field(default_factory=list)


class InMemoryRateLimiter:
    """Simple in-memory rate limiter with sliding window."""

    def __init__(
        self,
        per_minute: int = 30,
        per_hour: int = 200,
    ):
        self._per_minute = per_minute
        self._per_hour = per_hour
        self._windows: dict[str, RateLimitWindow] = defaultdict(RateLimitWindow)
        self._lock = Lock()

    def _prune(self, window: RateLimitWindow, now: float) -> None:
        hour_ago = now - 3600
        window.requests = [t for t in window.requests if t > hour_ago]

    def check(self, key: str) -> tuple[bool, dict[str, int]]:
        """Check if request is allowed. Returns (allowed, headers)."""
        now = time.time()
        with self._lock:
            window = self._windows[key]
            self._prune(window, now)

            recent_minute = sum(1 for t in window.requests if t > now - 60)
            recent_hour = len(window.requests)

            if recent_minute >= self._per_minute:
                return False, {
                    "X-RateLimit-Limit-Minute": str(self._per_minute),
                    "X-RateLimit-Remaining-Minute": "0",
                    "X-RateLimit-Limit-Hour": str(self._per_hour),
                    "X-RateLimit-Remaining-Hour": str(max(0, self._per_hour - recent_hour)),
                    "Retry-After": "60",
                }

            if recent_hour >= self._per_hour:
                return False, {
                    "X-RateLimit-Limit-Minute": str(self._per_minute),
                    "X-RateLimit-Remaining-Minute": str(max(0, self._per_minute - recent_minute)),
                    "X-RateLimit-Limit-Hour": str(self._per_hour),
                    "X-RateLimit-Remaining-Hour": "0",
                    "Retry-After": "3600",
                }

            window.requests.append(now)

            return True, {
                "X-RateLimit-Limit-Minute": str(self._per_minute),
                "X-RateLimit-Remaining-Minute": str(self._per_minute - recent_minute - 1),
                "X-RateLimit-Limit-Hour": str(self._per_hour),
                "X-RateLimit-Remaining-Hour": str(self._per_hour - recent_hour - 1),
            }


_rate_limiter: InMemoryRateLimiter | None = None


def get_rate_limiter() -> InMemoryRateLimiter:
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = InMemoryRateLimiter(
            per_minute=settings.AI_RATE_LIMIT_PER_MINUTE,
            per_hour=settings.AI_RATE_LIMIT_PER_HOUR,
        )
    return _rate_limiter