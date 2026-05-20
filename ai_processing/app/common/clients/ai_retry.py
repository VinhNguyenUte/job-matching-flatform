import asyncio
import random
import re
from collections.abc import Callable
from typing import TypeVar

from app.common.config import settings

T = TypeVar("T")

_last_call_at: dict[str, float] = {}
_rate_limit_locks: dict[str, asyncio.Lock] = {}


def _is_transient_ai_error(exc: Exception) -> bool:
    message = str(exc)
    return any(
        marker in message
        for marker in (
            "429",
            "503",
            "RESOURCE_EXHAUSTED",
            "UNAVAILABLE",
            "rate limit",
            "high demand",
            "quota",
        )
    )


def _retry_delay_seconds(exc: Exception, attempt: int) -> float:
    message = str(exc)
    retry_match = re.search(r"retryDelay['\"]?\s*:\s*['\"]?(\d+(?:\.\d+)?)s", message)
    if not retry_match:
        retry_match = re.search(r"Please retry in (\d+(?:\.\d+)?)s", message)
    if retry_match:
        delay = float(retry_match.group(1))
    else:
        delay = settings.AI_RETRY_BASE_DELAY_SECONDS * (2 ** attempt)
    jitter = random.uniform(0.0, 1.0)
    return min(delay + jitter, settings.AI_RETRY_MAX_DELAY_SECONDS)


async def _wait_for_rate_slot(key: str, min_interval_seconds: float) -> None:
    if min_interval_seconds <= 0:
        return

    lock = _rate_limit_locks.setdefault(key, asyncio.Lock())
    async with lock:
        now = asyncio.get_running_loop().time()
        elapsed = now - _last_call_at.get(key, 0.0)
        wait_seconds = min_interval_seconds - elapsed
        if wait_seconds > 0:
            await asyncio.sleep(wait_seconds)
        _last_call_at[key] = asyncio.get_running_loop().time()


async def call_ai_with_retry(
    operation_name: str,
    call: Callable[[], T],
    *,
    rate_limit_key: str | None = None,
    min_interval_seconds: float = 0.0,
) -> T:
    last_exc: Exception | None = None
    for attempt in range(settings.AI_RETRY_ATTEMPTS):
        try:
            if rate_limit_key:
                await _wait_for_rate_slot(rate_limit_key, min_interval_seconds)
            return call()
        except Exception as exc:
            last_exc = exc
            if attempt >= settings.AI_RETRY_ATTEMPTS - 1 or not _is_transient_ai_error(exc):
                raise
            await asyncio.sleep(_retry_delay_seconds(exc, attempt))

    raise RuntimeError(f"{operation_name} failed") from last_exc
