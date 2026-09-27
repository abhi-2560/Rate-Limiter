from abc import ABC, abstractmethod
from rate_limiter.models import RateLimitRule, RateLimitResult
from rate_limiter.storage.base import BaseStorage


class BaseAlgorithm(ABC):
    """Abstract Strategy for rate limiting algorithms."""

    def __init__(self, storage: BaseStorage):
        self._storage = storage

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the algorithm."""
        pass

    @abstractmethod
    async def allow(
        self,
        key: str,
        rule: RateLimitRule,
        cost: int = 1,
    ) -> RateLimitResult:
        """Evaluate if request for `key` under `rule` with `cost` is allowed."""
        pass
