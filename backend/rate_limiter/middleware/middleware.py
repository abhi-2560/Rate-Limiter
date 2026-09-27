import json
from typing import Callable, List, Optional, Set
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response
from rate_limiter.algorithms.base import BaseAlgorithm
from rate_limiter.models import RateLimitRule
from rate_limiter.rules.resolver import get_client_ip, get_api_key, resolve_client_tier, DEFAULT_TIER_RULES


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Global ASGI Middleware for app-wide rate limiting.
    Protects entire application while allowing specific paths to be exempt.
    """

    def __init__(
        self,
        app,
        algorithm: BaseAlgorithm,
        default_rule: Optional[RateLimitRule] = None,
        use_tier: bool = False,
        exempt_paths: Optional[List[str]] = None,
    ):
        super().__init__(app)
        self.algorithm = algorithm
        self.default_rule = default_rule or RateLimitRule(capacity=60, window_seconds=60)
        self.use_tier = use_tier
        self.exempt_paths: Set[str] = set(exempt_paths or [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
            "/favicon.ico",
        ])

    def _is_exempt(self, path: str) -> bool:
        if path in self.exempt_paths:
            return True
        for exempt in self.exempt_paths:
            if exempt.endswith("/*") and path.startswith(exempt[:-2]):
                return True
        return False

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Check if path is exempt
        if self._is_exempt(request.url.path):
            return await call_next(request)

        # Resolve identity & rule
        api_key = get_api_key(request)
        key = f"global:{api_key}" if api_key else f"global:{get_client_ip(request)}"

        if self.use_tier:
            tier = resolve_client_tier(api_key)
            rule = DEFAULT_TIER_RULES[tier]
        else:
            rule = self.default_rule

        # Check rate limit
        result = await self.algorithm.allow(key=key, rule=rule, cost=1)

        # Build rate limit headers
        rl_headers = {
            "X-RateLimit-Limit": str(result.limit),
            "X-RateLimit-Remaining": str(result.remaining),
            "X-RateLimit-Reset": str(int(result.reset_epoch)),
        }

        if not result.allowed:
            rl_headers["Retry-After"] = str(result.retry_after_int)
            error_body = json.dumps({
                "error": "Too Many Requests",
                "detail": f"Rate limit of {result.limit} requests exceeded. Try again in {result.retry_after_int} seconds.",
                "retry_after_seconds": result.retry_after_int,
                "reset_epoch": int(result.reset_epoch),
            })
            return Response(
                content=error_body,
                status_code=429,
                headers=rl_headers,
                media_type="application/json",
            )

        # Proceed with request
        response = await call_next(request)

        # Attach rate limit headers to downstream response
        for header_name, header_value in rl_headers.items():
            response.headers[header_name] = header_value

        return response
