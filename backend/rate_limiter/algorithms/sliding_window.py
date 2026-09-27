from rate_limiter.algorithms.base import BaseAlgorithm
from rate_limiter.models import RateLimitRule, RateLimitResult


class SlidingWindowCounterAlgorithm(BaseAlgorithm):
    """
    Sliding Window Counter Algorithm.
    Maintains a fine-grained moving window of requests. Avoids the boundary
    double-quota burst issue inherent in fixed window counters.
    """

    @property
    def name(self) -> str:
        return "sliding_window"

    async def allow(
        self,
        key: str,
        rule: RateLimitRule,
        cost: int = 1,
    ) -> RateLimitResult:
        return await self._storage.check_and_record_sliding_window(
            key=key,
            capacity=rule.capacity,
            window_seconds=rule.window_seconds,
            cost=cost,
        )
