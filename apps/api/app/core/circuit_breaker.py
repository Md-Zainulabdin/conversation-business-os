"""Circuit breaker for external API calls."""

import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from threading import Lock
from typing import TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreakerConfig:
    failure_threshold: int = 5
    success_threshold: int = 2
    timeout_seconds: float = 30.0
    excluded_exceptions: tuple[type[Exception], ...] = ()


class CircuitBreaker:
    """Circuit breaker implementation with thread-safe state management."""

    def __init__(
        self,
        name: str,
        config: CircuitBreakerConfig | None = None,
    ):
        self._name = name
        self._config = config or CircuitBreakerConfig()
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: float | None = None
        self._lock = Lock()

    @property
    def state(self) -> CircuitState:
        with self._lock:
            if (
                self._state == CircuitState.OPEN
                and self._last_failure_time is not None
                and time.time() - self._last_failure_time >= self._config.timeout_seconds
            ):
                self._state = CircuitState.HALF_OPEN
                self._success_count = 0
                logger.info("Circuit breaker %s: OPEN -> HALF_OPEN", self._name)
            return self._state

    def _record_success(self) -> None:
        with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self._config.success_threshold:
                    self._state = CircuitState.CLOSED
                    self._failure_count = 0
                    self._success_count = 0
                    logger.info("Circuit breaker %s: HALF_OPEN -> CLOSED", self._name)
            elif self._state == CircuitState.CLOSED:
                self._failure_count = 0

    def _record_failure(self, exc: Exception) -> None:
        if isinstance(exc, self._config.excluded_exceptions):
            return

        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()
            if self._state == CircuitState.HALF_OPEN:
                self._state = CircuitState.OPEN
                self._success_count = 0
                logger.warning("Circuit breaker %s: HALF_OPEN -> OPEN (failure in half-open)", self._name)
            elif self._state == CircuitState.CLOSED and self._failure_count >= self._config.failure_threshold:
                self._state = CircuitState.OPEN
                logger.warning(
                    "Circuit breaker %s: CLOSED -> OPEN (threshold=%d reached)",
                    self._name,
                    self._config.failure_threshold,
                )

    async def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Execute function with circuit breaker protection."""
        state = self.state
        if state == CircuitState.OPEN:
            raise CircuitBreakerOpenError(f"Circuit breaker {self._name} is OPEN")

        try:
            result = await func(*args, **kwargs)
            self._record_success()
            return result
        except Exception as exc:
            self._record_failure(exc)
            raise

    def reset(self) -> None:
        """Manually reset the circuit breaker to CLOSED state."""
        with self._lock:
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._success_count = 0
            self._last_failure_time = None
            logger.info("Circuit breaker %s: manually reset to CLOSED", self._name)


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open and rejecting calls."""
    pass


# Global circuit breaker instances
_chat_breaker: CircuitBreaker | None = None
_transcription_breaker: CircuitBreaker | None = None


def get_chat_breaker() -> CircuitBreaker:
    global _chat_breaker
    if _chat_breaker is None:
        _chat_breaker = CircuitBreaker(
            "groq_chat",
            CircuitBreakerConfig(
                failure_threshold=5,
                success_threshold=2,
                timeout_seconds=30.0,
            ),
        )
    return _chat_breaker


def get_transcription_breaker() -> CircuitBreaker:
    global _transcription_breaker
    if _transcription_breaker is None:
        _transcription_breaker = CircuitBreaker(
            "groq_transcription",
            CircuitBreakerConfig(
                failure_threshold=3,
                success_threshold=2,
                timeout_seconds=60.0,
            ),
        )
    return _transcription_breaker


async def call_with_chat_breaker[T](func: Callable[..., T], *args, **kwargs) -> T:
    """Execute a function with the chat circuit breaker."""
    breaker = get_chat_breaker()
    return await breaker.call(func, *args, **kwargs)


async def call_with_transcription_breaker[T](func: Callable[..., T], *args, **kwargs) -> T:
    """Execute a function with the transcription circuit breaker."""
    breaker = get_transcription_breaker()
    return await breaker.call(func, *args, **kwargs)


def reset_circuit_breakers() -> None:
    """Reset all circuit breakers to closed state. For testing purposes."""
    global _chat_breaker, _transcription_breaker
    if _chat_breaker is not None:
        _chat_breaker.reset()
    if _transcription_breaker is not None:
        _transcription_breaker.reset()