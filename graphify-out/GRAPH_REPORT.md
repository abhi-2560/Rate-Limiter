# Graph Report - Rate_Limiter  (2026-09-28)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 247 nodes · 568 edges · 14 communities (9 shown, 5 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 47 edges (avg confidence: 0.95)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `a21534c9`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- main.py
- RateLimitRule
- SlidingWindowVisualizer
- redis.py
- InMemoryStorage
- App
- RedisStorage
- RateLimitResult
- RateLimitMiddleware
- login_endpoint
- app/__init__.py
- benchmarks/__init__.py
- tests/__init__.py
- fastapi-rate-limiter

## God Nodes (most connected - your core abstractions)
1. `RateLimitResult` - 36 edges
2. `RateLimitRule` - 35 edges
3. `InMemoryStorage` - 22 edges
4. `RedisStorage` - 22 edges
5. `App` - 21 edges
6. `BaseAlgorithm` - 20 edges
7. `TokenBucketAlgorithm` - 20 edges
8. `SlidingWindowCounterAlgorithm` - 18 edges
9. `BaseStorage` - 16 edges
10. `RateLimiterDependency` - 13 edges

## Surprising Connections (you probably didn't know these)
- `BaseAlgorithm` --uses--> `RateLimitResult`  [INFERRED]
  backend/rate_limiter/algorithms/base.py → backend/rate_limiter/models.py
- `BaseAlgorithm` --uses--> `BaseStorage`  [INFERRED]
  backend/rate_limiter/algorithms/base.py → backend/rate_limiter/storage/base.py
- `RateLimiterDependency` --uses--> `BaseAlgorithm`  [INFERRED]
  backend/rate_limiter/middleware/dependency.py → backend/rate_limiter/algorithms/base.py
- `RateLimitMiddleware` --uses--> `BaseAlgorithm`  [INFERRED]
  backend/rate_limiter/middleware/middleware.py → backend/rate_limiter/algorithms/base.py
- `SlidingWindowCounterAlgorithm` --uses--> `RateLimitResult`  [INFERRED]
  backend/rate_limiter/algorithms/sliding_window.py → backend/rate_limiter/models.py

## Import Cycles
- None detected.

## Communities (14 total, 5 thin omitted)

### Community 0 - "main.py"
Cohesion: 0.08
Nodes (39): AsyncClient, health_check(), info(), lifespan(), public_endpoint(), Request, Information about the current rate limiter setup., Protected by Token Bucket algorithm. Limit: 5 requests per 30 seconds per IP… (+31 more)

### Community 1 - "RateLimitRule"
Cohesion: 0.11
Nodes (29): create_components(), BaseAlgorithm, ABC, Name of the algorithm., Evaluate if request for `key` under `rule` with `cost` is allowed., Abstract Strategy for rate limiting algorithms., Sliding Window Counter Algorithm. Maintains a fine-grained moving window of…, SlidingWindowCounterAlgorithm (+21 more)

### Community 2 - "SlidingWindowVisualizer"
Cohesion: 0.13
Nodes (4): RFC-6585, ApiClient, SlidingWindowVisualizer, TokenBucketVisualizer

### Community 3 - "redis.py"
Cohesion: 0.11
Nodes (15): asyncio, BaseStorage, ABC, Atomically check and record a request in a sliding window counter., Clear all rate limit data for testing or demo reset., Clean up resources, connections, or background workers., Abstract interface for rate limit storage engines., Atomic Redis Lua scripts for concurrency-safe rate limiting. (+7 more)

### Community 4 - "InMemoryStorage"
Cohesion: 0.12
Nodes (14): InMemoryStorage, Async-safe in-memory storage engine. Uses per-key asyncio locks to prevent race…, SlidingWindowState, TokenBucketState, any_storage(), fake_redis_storage(), memory_storage(), Parameterized fixture to run tests against both In-Memory and Redis backends. (+6 more)

### Community 6 - "RedisStorage"
Cohesion: 0.15
Nodes (11): Distributed Redis storage engine using atomic Lua scripts. Guarantees zero race…, RedisStorage, asyncio, Verify that if Redis connection fails, the system fails open and permits…, test_health_check_exempt(), test_public_endpoint_rate_limiting_and_headers(), test_redis_fail_open(), test_tiered_endpoint() (+3 more)

### Community 7 - "RateLimitResult"
Cohesion: 0.17
Nodes (11): RateLimitExceeded, HTTP 429 Too Many Requests exception adhering to RFC 6585., Request, Response, RateLimiterDependency, FastAPI Route Dependency for granular per-endpoint rate limiting. Usage:…, RateLimitResult, Outcome of evaluating a rate limit request. (+3 more)

### Community 8 - "RateLimitMiddleware"
Cohesion: 0.25
Nodes (6): Request, Response, RateLimitMiddleware, Global ASGI Middleware for app-wide rate limiting. Protects entire application…, BaseHTTPMiddleware, RequestResponseEndpoint

### Community 9 - "login_endpoint"
Cohesion: 0.29
Nodes (7): login_endpoint(), LoginRequest, BaseModel, Reset all rate limiter state for demo testing purposes., Strictly rate-limited login endpoint to demonstrate credential stuffing /…, reset_demo_state(), post

## Knowledge Gaps
- **2 isolated node(s):** `fastapi-rate-limiter`, `RFC-6585`
  These have ≤1 connection - possible missing edges. (Counts symbols only; 77 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **5 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `RateLimitResult` connect `RateLimitResult` to `main.py`, `RateLimitRule`, `redis.py`, `InMemoryStorage`, `RedisStorage`, `login_endpoint`?**
  _High betweenness centrality (0.130) - this node is a cross-community bridge._
- **Why does `RateLimitRule` connect `RateLimitRule` to `main.py`, `RateLimitMiddleware`, `RedisStorage`, `RateLimitResult`?**
  _High betweenness centrality (0.092) - this node is a cross-community bridge._
- **Why does `RedisStorage` connect `RedisStorage` to `main.py`, `RateLimitRule`, `redis.py`, `InMemoryStorage`, `RateLimitResult`?**
  _High betweenness centrality (0.071) - this node is a cross-community bridge._
- **Are the 12 inferred relationships involving `RateLimitResult` (e.g. with `login_endpoint()` and `public_endpoint()`) actually correct?**
  _`RateLimitResult` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Are the 13 inferred relationships involving `RateLimitRule` (e.g. with `BaseAlgorithm` and `SlidingWindowCounterAlgorithm`) actually correct?**
  _`RateLimitRule` has 13 INFERRED edges - model-reasoned connections that need verification._
- **Are the 4 inferred relationships involving `InMemoryStorage` (e.g. with `RateLimitResult` and `memory_storage()`) actually correct?**
  _`InMemoryStorage` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `RedisStorage` (e.g. with `RateLimitResult` and `fake_redis_storage()`) actually correct?**
  _`RedisStorage` has 5 INFERRED edges - model-reasoned connections that need verification._