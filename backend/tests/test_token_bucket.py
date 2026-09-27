import asyncio
import pytest
from rate_limiter.models import RateLimitRule
from rate_limiter.algorithms.token_bucket import TokenBucketAlgorithm


@pytest.mark.asyncio
async def test_token_bucket_initial_capacity(token_bucket_algo: TokenBucketAlgorithm):
    rule = RateLimitRule(capacity=5, window_seconds=10)
    key = "user_initial_test"

    # First request should consume 1 token, remaining 4
    res = await token_bucket_algo.allow(key, rule, cost=1)
    assert res.allowed is True
    assert res.remaining == 4
    assert res.limit == 5
    assert res.retry_after == 0.0


@pytest.mark.asyncio
async def test_token_bucket_burst_exhaustion(token_bucket_algo: TokenBucketAlgorithm):
    rule = RateLimitRule(capacity=3, window_seconds=10)
    key = "user_burst_test"

    # Consume all 3 tokens
    for i in range(3):
        res = await token_bucket_algo.allow(key, rule, cost=1)
        assert res.allowed is True
        assert res.remaining == 2 - i

    # 4th request must be rejected
    rejected = await token_bucket_algo.allow(key, rule, cost=1)
    assert rejected.allowed is False
    assert rejected.remaining == 0
    assert rejected.retry_after > 0


@pytest.mark.asyncio
async def test_token_bucket_refill(token_bucket_algo: TokenBucketAlgorithm):
    # 2 tokens per 1 second = 2 tokens/sec
    rule = RateLimitRule(capacity=2, window_seconds=1)
    key = "user_refill_test"

    # Consume both tokens
    res1 = await token_bucket_algo.allow(key, rule, cost=1)
    res2 = await token_bucket_algo.allow(key, rule, cost=1)
    assert res1.allowed is True
    assert res2.allowed is True

    # Immediate next request rejected
    res3 = await token_bucket_algo.allow(key, rule, cost=1)
    assert res3.allowed is False

    # Wait 0.6 seconds (enough to refill at least 1 token at 2 tokens/sec)
    await asyncio.sleep(0.6)

    res4 = await token_bucket_algo.allow(key, rule, cost=1)
    assert res4.allowed is True
    assert res4.remaining >= 0


@pytest.mark.asyncio
async def test_token_bucket_variable_cost(token_bucket_algo: TokenBucketAlgorithm):
    rule = RateLimitRule(capacity=10, window_seconds=10)
    key = "user_cost_test"

    # Consume 7 tokens at once
    res1 = await token_bucket_algo.allow(key, rule, cost=7)
    assert res1.allowed is True
    assert res1.remaining == 3

    # Attempt to consume 5 tokens (only 3 left) -> rejected
    res2 = await token_bucket_algo.allow(key, rule, cost=5)
    assert res2.allowed is False
    assert res2.remaining == 3

    # Attempt to consume 3 tokens -> allowed
    res3 = await token_bucket_algo.allow(key, rule, cost=3)
    assert res3.allowed is True
    assert res3.remaining == 0
