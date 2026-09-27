# RateShield | Production-Grade Rate Limiter & Visualizer

A modular, extensible, and high-performance Rate Limiter built with **Python 3.11+**, **FastAPI**, and **Redis**, accompanied by an interactive **Developer Visualizer Dashboard**.

Designed to demonstrate core backend engineering competencies: clean software design patterns, concurrency safety, distributed systems fundamentals, robust testing, and production-readiness.

---

## Project Structure

```text
Rate_Limiter/
├── backend/                       # Core FastAPI & Redis Rate Limiter Engine
│   ├── app/                      # Application routes, health, and demo showcase
│   ├── rate_limiter/             # Core rate limiting package
│   │   ├── algorithms/           # Token Bucket & Sliding Window Strategy Pattern
│   │   ├── storage/              # In-Memory & Redis Lua Script Storage Engines
│   │   ├── middleware/           # Route Dependency & ASGI Middleware
│   │   └── rules/                # Identity & API-key tier resolvers
│   ├── tests/                    # 20 automated pytest unit, integration & concurrency tests
│   ├── benchmarks/               # Latency & throughput benchmark scripts
│   ├── Dockerfile & compose      # Containerized setup with Redis 7
│   └── requirements.txt
│
└── frontend/                      # Interactive Visual Testing Dashboard
    ├── index.html                # Semantic UI dashboard
    ├── css/                      # Dark-mode design system & component styles
    └── js/                       # Real-time visualizers & RFC 6585 telemetry inspector
```

---

## Quickstart

### 1. Start the Backend & Redis

#### Option A: Docker Compose (Recommended)
```bash
cd backend
docker compose up -d --build
```
The API is now running at `http://localhost:8000`.

#### Option B: Local Python Virtualenv (In-Memory Mode)
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

---

### 2. Start the Frontend Dashboard

From the project root:
```bash
python3 -m http.server 3000 --directory frontend
```
Visit **`http://localhost:3000`** in your browser.

---

## Frontend Interactive Showcase

1. **Token Bucket Visualizer**: Watch liquid/token levels rise continuously according to the refill rate ($0.167\text{ tokens/s}$). Test single requests or burst traffic.
2. **Sliding Window Log**: View incoming request timestamps drift across a moving 10-second timeline. Watch expired requests automatically evict.
3. **Tiered API Key Playground**: Switch between Anonymous, Free, Pro, and Enterprise tiers to inspect dynamic quota allocation via `X-API-Key`.
4. **Brute-Force Auth Shield**: Simulate password guessing attempts against `/api/auth/login` to see strict lockouts triggered on the 4th attempt.
5. **RFC 6585 Telemetry Inspector**: Live monospace table logging response status (`200 OK` vs `429 Too Many Requests`), latency in milliseconds, and headers (`X-RateLimit-*`, `Retry-After`).

---

## Running Backend Tests

```bash
cd backend
./.venv/bin/pytest -v
```
Runs 20 automated tests verifying:
- Concurrency safety under simultaneous bursts (50 requests against capacity 10)
- Burst exhaustion and continuous refill
- Sliding window expiration
- Tiered quota mapping
- Redis fail-open resilience
