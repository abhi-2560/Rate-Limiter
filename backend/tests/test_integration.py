import pytest
import httpx
from unittest.mock import AsyncMock
from app.main import app
from rate_limiter.models import RateLimitRule
from rate_limiter.storage.redis import RedisStorage
from redis.exceptions import ConnectionError


@pytest.mark.asyncio
async def test_health_check_exempt():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        for _ in range(10):
            response = await client.get("/api/health")
            assert response.status_code == 200
            assert response.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_public_endpoint_rate_limiting_and_headers():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        # First 5 requests should pass (limit=5)
        for i in range(5):
            res = await client.get("/api/public")
            assert res.status_code == 200
            assert "X-RateLimit-Limit" in res.headers
            assert res.headers["X-RateLimit-Limit"] == "5"
            assert "X-RateLimit-Remaining" in res.headers
            assert "X-RateLimit-Reset" in res.headers

        # 6th request must receive 429 Too Many Requests
        throttled_res = await client.get("/api/public")
        assert throttled_res.status_code == 429
        assert "Retry-After" in throttled_res.headers
        assert int(throttled_res.headers["Retry-After"]) >= 1
        data = throttled_res.json()
        assert "detail" in data
        assert "error" in data["detail"]


@pytest.mark.asyncio
async def test_tiered_endpoint():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        # Pro user should have capacity=120
        res_pro = await client.get("/api/tiered", headers={"X-API-Key": "key_pro_user"})
        assert res_pro.status_code == 200
        assert res_pro.headers["X-RateLimit-Limit"] == "120"
        assert res_pro.json()["tier"] == "pro"

        # Free user should have capacity=30
        res_free = await client.get("/api/tiered", headers={"X-API-Key": "key_free_user"})
        assert res_free.status_code == 200
        assert res_free.headers["X-RateLimit-Limit"] == "30"
        assert res_free.json()["tier"] == "free"


@pytest.mark.asyncio
async def test_redis_fail_open():
    """Verify that if Redis connection fails, the system fails open and permits requests."""
    mock_redis = AsyncMock()
    mock_script = AsyncMock()
    mock_script.side_effect = ConnectionError("Connection to Redis refused")
    mock_redis.register_script = lambda script_code: mock_script

    storage = RedisStorage(mock_redis, fail_open=True)
    res = await storage.check_and_consume_token_bucket("key_fail_open", 10, 1.0, 1, 60)

    assert res.allowed is True
    assert res.remaining == 10
    await storage.close()
