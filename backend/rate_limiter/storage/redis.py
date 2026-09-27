import logging
import time
import uuid
from typing import Optional
from redis.asyncio import Redis
from redis.exceptions import RedisError
from rate_limiter.models import RateLimitResult
from rate_limiter.storage.base import BaseStorage
from rate_limiter.storage.lua_scripts import TOKEN_BUCKET_LUA, SLIDING_WINDOW_LUA

logger = logging.getLogger("rate_limiter.storage.redis")


class RedisStorage(BaseStorage):
    """
    Distributed Redis storage engine using atomic Lua scripts.
    Guarantees zero race conditions across multiple application server instances.
    Provides fail-open resilience in case of Redis outages.
    """

    def __init__(
        self,
        redis_client: Redis,
        fail_open: bool = True,
        key_prefix: str = "rate_limit",
    ):
        self._redis = redis_client
        self._fail_open = fail_open
        self._key_prefix = key_prefix
        self._token_bucket_script = None
        self._sliding_window_script = None

    async def _init_scripts(self) -> None:
        if self._token_bucket_script is None:
            self._token_bucket_script = self._redis.register_script(TOKEN_BUCKET_LUA)
        if self._sliding_window_script is None:
            self._sliding_window_script = self._redis.register_script(SLIDING_WINDOW_LUA)

    def _make_key(self, algorithm: str, key: str) -> str:
        return f"{self._key_prefix}:{algorithm}:{key}"

    async def check_and_consume_token_bucket(
        self,
        key: str,
        capacity: int,
        refill_rate: float,
        cost: int,
        window_seconds: int,
    ) -> RateLimitResult:
        redis_key = self._make_key("tb", key)
        now = time.time()
        ttl = window_seconds * 2

        try:
            await self._init_scripts()
            # Lua returns: { allowed (0/1), remaining, retry_after (str), reset_epoch (str) }
            raw_res = await self._token_bucket_script(
                keys=[redis_key],
                args=[capacity, refill_rate, cost, now, ttl],
            )
            allowed = bool(raw_res[0] == 1)
            remaining = int(raw_res[1])
            retry_after = float(raw_res[2])
            reset_epoch = float(raw_res[3])

            return RateLimitResult(
                allowed=allowed,
                limit=capacity,
                remaining=max(0, remaining),
                reset_epoch=reset_epoch,
                retry_after=retry_after,
            )
        except (RedisError, ConnectionError, TimeoutError) as e:
            logger.error(f"Redis error in token bucket check for key '{key}': {e}")
            if self._fail_open:
                logger.warning(f"Failing open for key '{key}' due to Redis unavailability.")
                return RateLimitResult(
                    allowed=True,
                    limit=capacity,
                    remaining=capacity,
                    reset_epoch=now + window_seconds,
                    retry_after=0.0,
                )
            raise

    async def check_and_record_sliding_window(
        self,
        key: str,
        capacity: int,
        window_seconds: int,
        cost: int,
    ) -> RateLimitResult:
        redis_key = self._make_key("sw", key)
        now = time.time()
        req_id = str(uuid.uuid4())

        try:
            await self._init_scripts()
            raw_res = await self._sliding_window_script(
                keys=[redis_key],
                args=[capacity, window_seconds, cost, now, req_id],
            )
            allowed = bool(raw_res[0] == 1)
            remaining = int(raw_res[1])
            retry_after = float(raw_res[2])
            reset_epoch = float(raw_res[3])

            return RateLimitResult(
                allowed=allowed,
                limit=capacity,
                remaining=max(0, remaining),
                reset_epoch=reset_epoch,
                retry_after=retry_after,
            )
        except (RedisError, ConnectionError, TimeoutError) as e:
            logger.error(f"Redis error in sliding window check for key '{key}': {e}")
            if self._fail_open:
                logger.warning(f"Failing open for key '{key}' due to Redis unavailability.")
                return RateLimitResult(
                    allowed=True,
                    limit=capacity,
                    remaining=capacity,
                    reset_epoch=now + window_seconds,
                    retry_after=0.0,
                )
            raise

    async def reset(self) -> None:
        try:
            keys = await self._redis.keys(f"{self._key_prefix}:*")
            if keys:
                await self._redis.delete(*keys)
        except Exception as e:
            logger.error(f"Error resetting Redis storage: {e}")

    async def close(self) -> None:
        await self._redis.aclose()
