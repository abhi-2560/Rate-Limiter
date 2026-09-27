from typing import Dict
from fastapi import HTTPException, status
from rate_limiter.models import RateLimitResult


class RateLimitExceeded(HTTPException):
    """HTTP 429 Too Many Requests exception adhering to RFC 6585."""

    def __init__(self, result: RateLimitResult, detail: str = "Too Many Requests"):
        headers: Dict[str, str] = {
            "X-RateLimit-Limit": str(result.limit),
            "X-RateLimit-Remaining": str(result.remaining),
            "X-RateLimit-Reset": str(int(result.reset_epoch)),
            "Retry-After": str(result.retry_after_int),
        }
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": detail,
                "retry_after_seconds": result.retry_after_int,
                "reset_epoch": int(result.reset_epoch),
                "limit": result.limit,
            },
            headers=headers,
        )
        self.result = result
