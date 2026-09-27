import asyncio
import pytest
from rate_limiter.models import RateLimitRule
from rate_limiter.algorithms.sliding_window import SlidingWindowCounterAlgorithm


@pytest.mark.asyncio
async def test_sliding_window_basic_capacity(sliding_window_algo: SlidingWindowCounterAlgorithm):
    rule = RateLimitRule(capacity=4, window_seconds=10)
    key = "sw_basic_test"

    for i in range(4):
        res = await sliding_window_algo.allow(key, rule, cost=1)
        assert res.allowed is True
        assert res.remaining == 3 - i

    # 5th request should be rejected
    rejected = await sliding_window_algo.allow(key, rule, cost=1)
    assert rejected.allowed is False
    assert rejected.remaining == 0
    assert rejected.retry_after > 0


@pytest.mark.asyncio
async def test_sliding_window_expiration(sliding_window_algo: SlidingWindowCounterAlgorithm):
    rule = RateLimitRule(capacity=2, window_seconds=1)
    key = "sw_expire_test"

    # Fill capacity
    assert (await sliding_window_algo.allow(key, rule, cost=1)).allowed is True
    assert (await sliding_window_algo.allow(key, rule, cost=1)).allowed is True
    assert (await sliding_window_algo.allow(key, rule, cost=1)).allowed is False

    # Wait for window to expire
    await asyncio.sleep(1.1)

    # Should be allowed again
    res = await sliding_window_algo.allow(key, rule, cost=1)
    assert res.allowed is True
    assert res.remaining == 1
