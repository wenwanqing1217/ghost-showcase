"""Circuit breaker for LLM calls — protects the service from cascading failures."""

from __future__ import annotations

import asyncio
import logging
from enum import Enum
from typing import Any, Callable, Coroutine, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class CircuitState(str, Enum):
    """Possible states of the circuit breaker."""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """Async circuit breaker with configurable failure threshold and recovery timeout."""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
    ) -> None:
        if failure_threshold < 1:
            raise ValueError("failure_threshold must be >= 1")
        if recovery_timeout <= 0:
            raise ValueError("recovery_timeout must be > 0")

        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout

        self._state: CircuitState = CircuitState.CLOSED
        self._failure_count: int = 0
        self._last_failure_time: float = 0.0
        self._lock: asyncio.Lock = asyncio.Lock()

    @property
    def state(self) -> CircuitState:
        if (
            self._state == CircuitState.OPEN
            and self._is_recovery_timeout_elapsed()
        ):
            self._state = CircuitState.HALF_OPEN
        return self._state

    @property
    def failure_count(self) -> int:
        return self._failure_count

    async def call(
        self,
        fn: Callable[..., Coroutine[Any, Any, T]],
        *args: Any,
        **kwargs: Any,
    ) -> T | None:
        async with self._lock:
            if self._state == CircuitState.OPEN:
                if self._is_recovery_timeout_elapsed():
                    logger.info("Circuit breaker transitioning to HALF_OPEN")
                    self._state = CircuitState.HALF_OPEN
                else:
                    logger.debug(
                        "Circuit breaker OPEN — rejecting call "
                        "(failures=%d, elapsed=%.1fs, timeout=%.1fs)",
                        self._failure_count,
                        self._elapsed_since_last_failure(),
                        self.recovery_timeout,
                    )
                    return None

            try:
                result = await fn(*args, **kwargs)
            except Exception as exc:
                self._record_failure()
                logger.warning(
                    "Circuit breaker failure #%d: %s",
                    self._failure_count,
                    exc,
                )
                return None

            if self._state == CircuitState.HALF_OPEN:
                logger.info("Circuit breaker probe succeeded — closing circuit")
            self._reset()
            return result

    def reset(self) -> None:
        self._reset()

    def __repr__(self) -> str:
        return (
            f"CircuitBreaker(state={self._state.value}, "
            f"failures={self._failure_count}, "
            f"threshold={self.failure_threshold}, "
            f"recovery_timeout={self.recovery_timeout}s)"
        )

    def _reset(self) -> None:
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time = 0.0

    def _record_failure(self) -> None:
        self._failure_count += 1
        self._last_failure_time = asyncio.get_event_loop().time()
        if self._failure_count >= self.failure_threshold:
            self._state = CircuitState.OPEN
            logger.warning(
                "Circuit breaker OPENED after %d consecutive failures "
                "(threshold=%d, recovery_timeout=%.1fs)",
                self._failure_count,
                self.failure_threshold,
                self.recovery_timeout,
            )

    def _is_recovery_timeout_elapsed(self) -> bool:
        try:
            loop_time = asyncio.get_event_loop().time()
        except RuntimeError:
            loop_time = self._last_failure_time
        return (loop_time - self._last_failure_time) >= self.recovery_timeout

    def _elapsed_since_last_failure(self) -> float:
        try:
            loop_time = asyncio.get_event_loop().time()
        except RuntimeError:
            return 0.0
        return loop_time - self._last_failure_time
