from dataclasses import dataclass
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class ClientTier(str, Enum):
    ANONYMOUS = "anonymous"
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class RateLimitRule(BaseModel):
    """Configuration rule for a rate limit policy."""
    capacity: int = Field(gt=0, description="Maximum number of requests/tokens allowed in the window")
    window_seconds: int = Field(gt=0, description="Duration of the rate limit window in seconds")
    cost: int = Field(default=1, ge=1, description="Default cost in tokens per request")

    @property
    def refill_rate_per_second(self) -> float:
        """Token replenishment rate per second for Token Bucket algorithm."""
        return float(self.capacity) / float(self.window_seconds)


@dataclass(frozen=True)
class RateLimitResult:
    """Outcome of evaluating a rate limit request."""
    allowed: bool
    limit: int
    remaining: int
    reset_epoch: float
    retry_after: float

    @property
    def retry_after_int(self) -> int:
        """Seconds to wait before retrying, rounded up to next integer for HTTP header compliance."""
        return max(1, int(self.retry_after + 0.999))
