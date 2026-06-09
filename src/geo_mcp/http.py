"""Shared async HTTP client with rate limiting and retry logic."""

import asyncio
import time

import httpx

from .config import settings


class RateLimiter:
    """Client-side token-bucket rate limiter."""

    def __init__(self, rate: float):
        self.rate = rate
        self._last_request: float = 0.0
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        async with self._lock:
            now = time.monotonic()
            wait = max(0.0, (1.0 / self.rate) - (now - self._last_request))
            if wait > 0:
                await asyncio.sleep(wait)
            self._last_request = time.monotonic()


def get_client() -> httpx.AsyncClient:
    """Create a configured async HTTP client with retry transport."""
    transport = httpx.AsyncHTTPTransport(retries=settings.http_retries)
    return httpx.AsyncClient(
        headers={"User-Agent": settings.user_agent},
        timeout=httpx.Timeout(30.0),
        transport=transport,
    )


_nominatim_limiter: RateLimiter | None = None


def nominatim_limiter() -> RateLimiter:
    global _nominatim_limiter
    if _nominatim_limiter is None:
        _nominatim_limiter = RateLimiter(settings.nominatim_rate_limit)
    return _nominatim_limiter
