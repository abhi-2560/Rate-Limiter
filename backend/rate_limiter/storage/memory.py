import asyncio
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Dict, Tuple, Optional
from rate_limiter.models import RateLimitResult
from rate_limiter.storage.base import BaseStorage


@dataclass
class TokenBucketState:
    tokens: float
    last_updated: float
    capacity: int
    refill_rate: float
    expires_at: float


@dataclass
class SlidingWindowState:
    requests: Deque[Tuple[float, int]] = field(default_factory=deque)  # (timestamp, cost)
    expires_at: float = 0.0


class InMemoryStorage(BaseStorage):
    """
    Async-safe in-memory storage engine.
    Uses per-key asyncio locks to prevent race conditions within the process
    and a background task to evict stale keys and avoid memory leaks.
    """

    def __init__(self, cleanup_interval_seconds: float = 60.0):
        self._token_buckets: Dict[str, TokenBucketState] = {}
        self._sliding_windows: Dict[str, SlidingWindowState] = {}
        self._locks: Dict[str, asyncio.Lock] = {}
        self._global_lock = asyncio.Lock()
        self._cleanup_interval = cleanup_interval_seconds
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = True

    async def _get_lock(self, key: str) -> asyncio.Lock:
        async with self._global_lock:
            if key not in self._locks:
                self._locks[key] = asyncio.Lock()
            return self._locks[key]

    def _ensure_cleanup_task(self) -> None:
        if self._cleanup_task is None or self._cleanup_task.done():
            try:
                loop = asyncio.get_running_loop()
                self._cleanup_task = loop.create_task(self._eviction_worker())
            except RuntimeError:
                pass

    async def _eviction_worker(self) -> None:
        while self._running:
            try:
                await asyncio.sleep(self._cleanup_interval)
                await self._evict_expired()
            except asyncio.CancelledError:
                break
            except Exception:
                pass

    async def _evict_expired(self) -> None:
        now = time.time()
        async with self._global_lock:
            expired_tb = [k for k, v in self._token_buckets.items() if v.expires_at <= now]
            for k in expired_tb:
                self._token_buckets.pop(k, None)
                self._locks.pop(k, None)

            expired_sw = [k for k, v in self._sliding_windows.items() if v.expires_at <= now]
            for k in expired_sw:
                self._sliding_windows.pop(k, None)
                self._locks.pop(k, None)

    async def check_and_consume_token_bucket(
        self,
        key: str,
        capacity: int,
        refill_rate: float,
        cost: int,
        window_seconds: int,
    ) -> RateLimitResult:
        self._ensure_cleanup_task()
        lock = await self._get_lock(key)
        now = time.time()

        async with lock:
            state = self._token_buckets.get(key)
            if state is None:
                tokens = float(capacity)
                last_updated = now
            else:
                elapsed = max(0.0, now - state.last_updated)
                tokens = min(float(capacity), state.tokens + (elapsed * refill_rate))
                last_updated = now

            if tokens >= cost:
                tokens -= cost
                allowed = True
                remaining = int(tokens)
                retry_after = 0.0
            else:
                allowed = False
                remaining = int(tokens)
                deficit = cost - tokens
                retry_after = deficit / refill_rate if refill_rate > 0 else float(window_seconds)

            reset_after = (capacity - tokens) / refill_rate if refill_rate > 0 else float(window_seconds)
            reset_epoch = now + reset_after
            expires_at = now + (window_seconds * 2)

            self._token_buckets[key] = TokenBucketState(
                tokens=tokens,
                last_updated=last_updated,
                capacity=capacity,
                refill_rate=refill_rate,
                expires_at=expires_at,
            )

            return RateLimitResult(
                allowed=allowed,
                limit=capacity,
                remaining=max(0, remaining),
                reset_epoch=reset_epoch,
                retry_after=retry_after,
            )

    async def check_and_record_sliding_window(
        self,
        key: str,
        capacity: int,
        window_seconds: int,
        cost: int,
    ) -> RateLimitResult:
        self._ensure_cleanup_task()
        lock = await self._get_lock(key)
        now = time.time()
        window_start = now - window_seconds

        async with lock:
            state = self._sliding_windows.get(key)
            if state is None:
                state = SlidingWindowState()
                self._sliding_windows[key] = state

            # Remove timestamps outside the sliding window
            while state.requests and state.requests[0][0] <= window_start:
                state.requests.popleft()

            current_count = sum(c for _, c in state.requests)

            if (current_count + cost) <= capacity:
                state.requests.append((now, cost))
                state.expires_at = now + (window_seconds * 2)
                remaining = capacity - (current_count + cost)
                return RateLimitResult(
                    allowed=True,
                    limit=capacity,
                    remaining=remaining,
                    reset_epoch=now + window_seconds,
                    retry_after=0.0,
                )
            else:
                # Window limit exceeded
                oldest_ts = state.requests[0][0] if state.requests else now
                retry_after = max(0.0, (oldest_ts + window_seconds) - now)
                reset_epoch = oldest_ts + window_seconds
                state.expires_at = now + (window_seconds * 2)
                return RateLimitResult(
                    allowed=False,
                    limit=capacity,
                    remaining=0,
                    reset_epoch=reset_epoch,
                    retry_after=retry_after,
                )

    async def reset(self) -> None:
        async with self._global_lock:
            self._token_buckets.clear()
            self._sliding_windows.clear()
            self._locks.clear()

    async def close(self) -> None:
        self._running = False
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        self._token_buckets.clear()
        self._sliding_windows.clear()
        self._locks.clear()
