import pytest
import pytest_asyncio
import fakeredis.aioredis
from rate_limiter.storage.memory import InMemoryStorage
from rate_limiter.storage.redis import RedisStorage
from rate_limiter.algorithms.token_bucket import TokenBucketAlgorithm
from rate_limiter.algorithms.sliding_window import SlidingWindowCounterAlgorithm


@pytest_asyncio.fixture
async def memory_storage():
    storage = InMemoryStorage(cleanup_interval_seconds=1.0)
    yield storage
    await storage.close()


@pytest_asyncio.fixture
async def fake_redis_storage():
    # Use fakeredis for async Redis emulation without needing an external Redis server
    fake_redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    storage = RedisStorage(fake_redis, fail_open=True)
    yield storage
    await storage.close()


@pytest_asyncio.fixture(params=["memory", "redis"])
async def any_storage(request, memory_storage, fake_redis_storage):
    """Parameterized fixture to run tests against both In-Memory and Redis backends."""
    if request.param == "memory":
        return memory_storage
    return fake_redis_storage


@pytest_asyncio.fixture
async def token_bucket_algo(any_storage):
    return TokenBucketAlgorithm(any_storage)


@pytest_asyncio.fixture
async def sliding_window_algo(any_storage):
    return SlidingWindowCounterAlgorithm(any_storage)
