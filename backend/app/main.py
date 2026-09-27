import os
from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, Depends, Request, Response
from pydantic import BaseModel
from redis.asyncio import from_url as redis_from_url

from rate_limiter.models import RateLimitRule, RateLimitResult, ClientTier
from rate_limiter.storage.memory import InMemoryStorage
from rate_limiter.storage.redis import RedisStorage
from rate_limiter.algorithms.token_bucket import TokenBucketAlgorithm
from rate_limiter.algorithms.sliding_window import SlidingWindowCounterAlgorithm
from rate_limiter.middleware.dependency import RateLimiterDependency
from rate_limiter.rules.resolver import get_client_ip, get_api_key, resolve_client_tier

# Storage backend configuration
STORAGE_TYPE = os.getenv("RATE_LIMIT_STORAGE", "memory").lower()
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
FAIL_OPEN = os.getenv("RATE_LIMIT_FAIL_OPEN", "true").lower() == "true"


def create_components():
    if STORAGE_TYPE == "redis":
        redis_client = redis_from_url(REDIS_URL, decode_responses=True)
        storage_instance = RedisStorage(redis_client, fail_open=FAIL_OPEN)
    else:
        storage_instance = InMemoryStorage()

    tb_algo = TokenBucketAlgorithm(storage_instance)
    sw_algo = SlidingWindowCounterAlgorithm(storage_instance)
    return storage_instance, tb_algo, sw_algo


storage, token_bucket_algo, sliding_window_algo = create_components()

# Rate Limiter Dependencies
ip_token_bucket_limiter = RateLimiterDependency(
    algorithm=token_bucket_algo,
    rule=RateLimitRule(capacity=5, window_seconds=30),
    key_func=get_client_ip,
    scope="public_api",
)

sliding_window_limiter = RateLimiterDependency(
    algorithm=sliding_window_algo,
    rule=RateLimitRule(capacity=5, window_seconds=10),
    key_func=get_client_ip,
    scope="sliding_api",
)

tiered_limiter = RateLimiterDependency(
    algorithm=token_bucket_algo,
    use_tier=True,
    scope="tiered_api",
)

login_limiter = RateLimiterDependency(
    algorithm=token_bucket_algo,
    rule=RateLimitRule(capacity=3, window_seconds=60),
    key_func=get_client_ip,
    scope="auth_login",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    if storage:
        await storage.close()


from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="FastAPI Rate Limiter Showcase",
    description="A production-grade rate limiter demonstrating Token Bucket, Sliding Window, Redis Lua scripts, and RFC 6585 compliance.",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS for frontend dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=[
        "X-RateLimit-Limit",
        "X-RateLimit-Remaining",
        "X-RateLimit-Reset",
        "Retry-After",
    ],
)


@app.get("/api/health")
async def health_check():
    """Exempt health check endpoint (bypasses rate limiting)."""
    return {
        "status": "healthy",
        "storage": STORAGE_TYPE,
        "fail_open": FAIL_OPEN,
    }


@app.post("/api/demo/reset")
async def reset_demo_state():
    """Reset all rate limiter state for demo testing purposes."""
    if storage:
        await storage.reset()
    return {"status": "ok", "message": "Rate limiter state successfully reset"}


@app.get("/api/info")
async def info():
    """Information about the current rate limiter setup."""
    return {
        "storage": STORAGE_TYPE,
        "fail_open": FAIL_OPEN,
        "supported_algorithms": ["token_bucket", "sliding_window"],
        "endpoints": {
            "/api/public": "IP-based Token Bucket (5 req / 30s)",
            "/api/sliding": "IP-based Sliding Window Counter (5 req / 10s)",
            "/api/tiered": "API-Key based Tiering (Free: 30/min, Pro: 120/min, Enterprise: 1000/min)",
            "/api/auth/login": "Strict Brute-Force Protection (3 attempts / 60s)",
            "/api/health": "Health Check (Exempt)",
        },
        "sample_api_keys": {
            "key_free_user": "Free Tier (30 req/min)",
            "key_pro_user": "Pro Tier (120 req/min)",
            "key_enterprise_user": "Enterprise Tier (1000 req/min)",
        }
    }


@app.get("/api/public")
async def public_endpoint(
    request: Request,
    limiter_result: RateLimitResult = Depends(ip_token_bucket_limiter),
):
    """
    Protected by Token Bucket algorithm.
    Limit: 5 requests per 30 seconds per IP address.
    """
    return {
        "message": "Welcome to the public API!",
        "client_ip": get_client_ip(request),
        "rate_limit": {
            "limit": limiter_result.limit,
            "remaining": limiter_result.remaining,
            "reset_epoch": limiter_result.reset_epoch,
        }
    }


@app.get("/api/sliding")
async def sliding_endpoint(
    request: Request,
    limiter_result: RateLimitResult = Depends(sliding_window_limiter),
):
    """
    Protected by Sliding Window Counter algorithm.
    Limit: 5 requests per 10 seconds per IP address.
    """
    return {
        "message": "Welcome to the sliding window API!",
        "client_ip": get_client_ip(request),
        "rate_limit": {
            "limit": limiter_result.limit,
            "remaining": limiter_result.remaining,
            "reset_epoch": limiter_result.reset_epoch,
        }
    }


@app.get("/api/tiered")
async def tiered_endpoint(
    request: Request,
    limiter_result: RateLimitResult = Depends(tiered_limiter),
):
    """
    Tier-based rate limiting using X-API-Key header.
    - No key or unknown key: Anonymous / Free tier (10-30 req/min)
    - key_pro_user: Pro tier (120 req/min)
    - key_enterprise_user: Enterprise tier (1000 req/min)
    """
    api_key = get_api_key(request)
    tier = resolve_client_tier(api_key)
    return {
        "message": f"Welcome to the tiered API, {tier.value} tier client!",
        "tier": tier.value,
        "rate_limit": {
            "limit": limiter_result.limit,
            "remaining": limiter_result.remaining,
            "reset_epoch": limiter_result.reset_epoch,
        }
    }


class LoginRequest(BaseModel):
    username: str
    password: str


@app.post("/api/auth/login")
async def login_endpoint(
    body: LoginRequest,
    limiter_result: RateLimitResult = Depends(login_limiter),
):
    """
    Strictly rate-limited login endpoint to demonstrate credential stuffing / brute-force protection.
    Limit: 3 requests per 60 seconds per IP.
    """
    if body.username == "admin" and body.password == "secret123":
        return {"authenticated": True, "token": "mock_jwt_token_xyz"}
    return {"authenticated": False, "error": "Invalid credentials"}
