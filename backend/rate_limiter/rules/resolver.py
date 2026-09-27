from typing import Callable, Dict, Optional
from fastapi import Request
from rate_limiter.models import ClientTier, RateLimitRule


# Default tier rules: requests per window (seconds)
DEFAULT_TIER_RULES: Dict[ClientTier, RateLimitRule] = {
    ClientTier.ANONYMOUS: RateLimitRule(capacity=10, window_seconds=60),     # 10 req/min
    ClientTier.FREE: RateLimitRule(capacity=30, window_seconds=60),          # 30 req/min
    ClientTier.PRO: RateLimitRule(capacity=120, window_seconds=60),         # 120 req/min
    ClientTier.ENTERPRISE: RateLimitRule(capacity=1000, window_seconds=60),  # 1000 req/min
}

# Mock API Key to Tier registry for demonstration / testing
MOCK_API_KEYS: Dict[str, ClientTier] = {
    "key_free_user": ClientTier.FREE,
    "key_pro_user": ClientTier.PRO,
    "key_enterprise_user": ClientTier.ENTERPRISE,
}


def get_client_ip(request: Request) -> str:
    """
    Extracts the real client IP address, safely taking into account
    reverse proxies (e.g. Nginx, Cloudflare) via X-Forwarded-For header.
    """
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Client IP is the first comma-separated address
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()

    if request.client and request.client.host:
        return request.client.host

    return "127.0.0.1"


def get_api_key(request: Request) -> Optional[str]:
    """Extracts API key from X-API-Key header or Authorization Bearer token."""
    api_key = request.headers.get("X-API-Key")
    if api_key:
        return api_key.strip()
    
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header[7:].strip()

    return None


def resolve_client_tier(api_key: Optional[str]) -> ClientTier:
    """Resolves client tier from API key, defaulting to ANONYMOUS."""
    if not api_key:
        return ClientTier.ANONYMOUS
    return MOCK_API_KEYS.get(api_key, ClientTier.FREE)
