from abc import ABC, abstractmethod
from rate_limiter.models import RateLimitResult


class BaseStorage(ABC):
    """Abstract interface for rate limit storage engines."""

    @abstractmethod
    async def check_and_consume_token_bucket(
        self,
        key: str,
        capacity: int,
        refill_rate: float,
        cost: int,
        window_seconds: int,
    ) -> RateLimitResult:
        """Atomically refill and consume tokens from a token bucket."""
        pass

    @abstractmethod
    async def check_and_record_sliding_window(
        self,
        key: str,
        capacity: int,
        window_seconds: int,
        cost: int,
    ) -> RateLimitResult:
        """Atomically check and record a request in a sliding window counter."""
        pass

    @abstractmethod
    async def reset(self) -> None:
        """Clear all rate limit data for testing or demo reset."""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Clean up resources, connections, or background workers."""
        pass
