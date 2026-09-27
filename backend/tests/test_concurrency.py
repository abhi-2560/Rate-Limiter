import asyncio
import pytest
from rate_limiter.models import RateLimitRule
from rate_limiter.algorithms.token_bucket import TokenBucketAlgorithm
from rate_limiter.algorithms.sliding_window import SlidingWindowCounterAlgorithm
from rate_limiter.storage.memory import InMemoryStorage
from rate_limiter.storage.redis import RedisStorage
import fakeredis.aioredis


@pytest.mark.asyncio
@pytest.mark.parametrize("storage_type", ["memory", "redis"])
async def test_high_concurrency_token_bucket(storage_type: str):
    """
    Stress test for race conditions:
    Fires 50 concurrent requests against a bucket with capacity=10.
    Asserts that EXACTLY 10 requests succeed and EXACTLY 40 requests fail.
    """
    if storage_type == "memory":
        storage = InMemoryStorage()
    else:
        fake_redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
        storage = RedisStorage(fake_redis)

    algo = TokenBucketAlgorithm(storage)
    rule = RateLimitRule(capacity=10, window_seconds=60)
    key = f"concurrent_tb_test_{storage_type}"

    # Fire 50 concurrent requests simultaneously
    tasks = [algo.allow(key, rule, cost=1) for _ in range(50)]
    results = await asyncio.gather(*tasks)

    allowed_count = sum(1 for r in results if r.allowed)
    rejected_count = sum(1 for r in results if not r.allowed)

    await storage.close()

    assert allowed_count == 10, f"Expected exactly 10 allowed requests, got {allowed_count}"
    assert rejected_count == 40, f"Expected exactly 40 rejected requests, got {rejected_count}"


@pytest.mark.asyncio
@pytest.mark.parametrize("storage_type", ["memory", "redis"])
async def test_high_concurrency_sliding_window(storage_type: str):
    """
    Stress test for race conditions in Sliding Window:
    Fires 50 concurrent requests against a sliding window with capacity=10.
    Asserts that EXACTLY 10 requests succeed and EXACTLY 40 requests fail.
    """
    if storage_type == "memory":
        storage = InMemoryStorage()
    else:
        fake_redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
        storage = RedisStorage(fake_redis)

    algo = SlidingWindowCounterAlgorithm(storage)
    rule = RateLimitRule(capacity=10, window_seconds=60)
    key = f"concurrent_sw_test_{storage_type}"

    # Fire 50 concurrent requests simultaneously
    tasks = [algo.allow(key, rule, cost=1) for _ in range(50)]
    results = await asyncio.gather(*tasks)

    allowed_count = sum(1 for r in results if r.allowed)
    rejected_count = sum(1 for r in results if not r.allowed)

    await storage.close()

    assert allowed_count == 10, f"Expected exactly 10 allowed requests, got {allowed_count}"
    assert rejected_count == 40, f"Expected exactly 40 rejected requests, got {rejected_count}"
