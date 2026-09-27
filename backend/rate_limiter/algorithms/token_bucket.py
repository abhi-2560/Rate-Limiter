from rate_limiter.algorithms.base import BaseAlgorithm
from rate_limiter.models import RateLimitRule, RateLimitResult


class TokenBucketAlgorithm(BaseAlgorithm):
    """
    Token Bucket Algorithm.
    Allows bursts of traffic up to `capacity`, with tokens continuously refilled
    at a steady rate `capacity / window_seconds`.
    """

    @property
    def name(self) -> str:
        return "token_bucket"

    async def allow(
        self,
        key: str,
        rule: RateLimitRule,
        cost: int = 1,
    ) -> RateLimitResult:
        return await self._storage.check_and_consume_token_bucket(
            key=key,
            capacity=rule.capacity,
            refill_rate=rule.refill_rate_per_second,
            cost=cost,
            window_seconds=rule.window_seconds,
        )
