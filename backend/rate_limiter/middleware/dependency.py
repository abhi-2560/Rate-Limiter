from typing import Callable, Optional, Union
from fastapi import Request, Response
from rate_limiter.algorithms.base import BaseAlgorithm
from rate_limiter.exceptions import RateLimitExceeded
from rate_limiter.models import RateLimitResult, RateLimitRule
from rate_limiter.rules.resolver import get_client_ip, get_api_key, resolve_client_tier, DEFAULT_TIER_RULES


class RateLimiterDependency:
    """
    FastAPI Route Dependency for granular per-endpoint rate limiting.
    
    Usage:
        limiter = RateLimiterDependency(algorithm, rule=RateLimitRule(capacity=10, window_seconds=60))
        
        @app.get("/items", dependencies=[Depends(limiter)])
        def get_items():
            return {"items": []}
    """

    def __init__(
        self,
        algorithm: BaseAlgorithm,
        rule: Optional[RateLimitRule] = None,
        use_tier: bool = False,
        key_func: Optional[Callable[[Request], str]] = None,
        cost: int = 1,
        scope: Optional[str] = None,
    ):
        self.algorithm = algorithm
        self.rule = rule
        self.use_tier = use_tier
        self.key_func = key_func
        self.cost = cost
        self.scope = scope

    def _resolve_key(self, request: Request) -> str:
        if self.key_func:
            raw_key = self.key_func(request)
        else:
            api_key = get_api_key(request)
            raw_key = api_key if api_key else get_client_ip(request)

        scope_prefix = f"{self.scope}:" if self.scope else f"{request.url.path}:"
        return f"{scope_prefix}{raw_key}"

    def _resolve_rule(self, request: Request) -> RateLimitRule:
        if self.use_tier:
            api_key = get_api_key(request)
            tier = resolve_client_tier(api_key)
            return DEFAULT_TIER_RULES[tier]
        if self.rule:
            return self.rule
        return RateLimitRule(capacity=60, window_seconds=60)

    async def __call__(self, request: Request, response: Response) -> RateLimitResult:
        key = self._resolve_key(request)
        rule = self._resolve_rule(request)

        result = await self.algorithm.allow(key=key, rule=rule, cost=self.cost)

        # Inject standard rate limiting headers onto the response
        response.headers["X-RateLimit-Limit"] = str(result.limit)
        response.headers["X-RateLimit-Remaining"] = str(result.remaining)
        response.headers["X-RateLimit-Reset"] = str(int(result.reset_epoch))

        if not result.allowed:
            raise RateLimitExceeded(result)

        return result
