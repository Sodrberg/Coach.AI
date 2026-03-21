"""In-memory per-user rate limiter for LLM-triggering endpoints."""

import logging
import time
from collections import deque
from typing import Dict

from fastapi import Depends, HTTPException

from app.api.auth import get_authenticated_user
from app.models.user import Session

logger = logging.getLogger(__name__)


class InMemoryRateLimiter:
    """
    Sliding-window rate limiter using in-memory deques.

    Suitable for single-process deployments. State resets on server restart
    (acceptable — briefly more lenient, not a security problem).
    """

    def __init__(self) -> None:
        self._buckets: Dict[str, deque] = {}
        self._check_count = 0

    def check(self, key: str, max_requests: int, window_seconds: int) -> bool:
        """Return True if the request is allowed, False if rate-limited."""
        now = time.monotonic()
        bucket = self._buckets.setdefault(key, deque())

        # Purge entries outside the window
        while bucket and bucket[0] < now - window_seconds:
            bucket.popleft()

        if len(bucket) >= max_requests:
            return False

        bucket.append(now)

        # Periodic cleanup of stale buckets (every 500 checks)
        self._check_count += 1
        if self._check_count >= 500:
            self._cleanup(now, window_seconds)
            self._check_count = 0

        return True

    def _cleanup(self, now: float, default_window: int) -> None:
        """Remove buckets with no recent activity."""
        stale_keys = [
            key
            for key, bucket in self._buckets.items()
            if not bucket or bucket[-1] < now - default_window
        ]
        for key in stale_keys:
            del self._buckets[key]
        if stale_keys:
            logger.debug(f"Rate limiter cleanup: removed {len(stale_keys)} stale buckets")


# Global singleton
rate_limiter = InMemoryRateLimiter()


def require_rate_limit(max_requests: int, window_seconds: int):
    """
    FastAPI dependency factory that enforces per-user rate limits.

    Usage in routes:
        session: Session = Depends(require_rate_limit(3, 3600))  # 3 per hour
    """

    async def dependency(
        session: Session = Depends(get_authenticated_user),
    ) -> Session:
        key = f"{session.user_id}:{max_requests}:{window_seconds}"
        if not rate_limiter.check(key, max_requests, window_seconds):
            logger.warning(
                f"Rate limit exceeded for user {session.user_id} "
                f"(limit: {max_requests}/{window_seconds}s)"
            )
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please try again later.",
            )
        return session

    return dependency
