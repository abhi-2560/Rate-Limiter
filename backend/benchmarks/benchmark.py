import asyncio
import os
import sys
import time
import statistics
from typing import List

# Ensure root directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import httpx
from app.main import app


async def send_request(client: httpx.AsyncClient, url: str):
    start = time.perf_counter()
    response = await client.get(url)
    elapsed_ms = (time.perf_counter() - start) * 1000.0
    return elapsed_ms, response.status_code


async def run_benchmark(concurrency: int = 50, total_requests: int = 1000):
    print(f"================================================================")
    print(f"  FastAPI Rate Limiter Concurrency & Latency Benchmark")
    print(f"  Total Requests: {total_requests} | Concurrency: {concurrency}")
    print(f"================================================================")

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        latencies: List[float] = []
        status_counts = {200: 0, 429: 0, "other": 0}

        semaphore = asyncio.Semaphore(concurrency)

        async def worker():
            async with semaphore:
                lat, status = await send_request(client, "/api/public")
                latencies.append(lat)
                if status == 200:
                    status_counts[200] += 1
                elif status == 429:
                    status_counts[429] += 1
                else:
                    status_counts["other"] += 1

        start_time = time.perf_counter()
        tasks = [asyncio.create_task(worker()) for _ in range(total_requests)]
        await asyncio.gather(*tasks)
        total_time_seconds = time.perf_counter() - start_time

    latencies.sort()
    rps = total_requests / total_time_seconds
    p50 = statistics.median(latencies)
    p95 = latencies[int(len(latencies) * 0.95)]
    p99 = latencies[int(len(latencies) * 0.99)]
    avg = statistics.mean(latencies)

    print("\n--- RESULTS ---")
    print(f"  Total Time Taken : {total_time_seconds:.3f} s")
    print(f"  Throughput (RPS) : {rps:.2f} req/s")
    print(f"  200 OK           : {status_counts[200]} requests")
    print(f"  429 Throttled    : {status_counts[429]} requests")
    print(f"  Other / Errors   : {status_counts['other']} requests")
    print("\n--- LATENCY OVERHEAD ---")
    print(f"  Average Latency  : {avg:.2f} ms")
    print(f"  P50 (Median)     : {p50:.2f} ms")
    print(f"  P95              : {p95:.2f} ms")
    print(f"  P99              : {p99:.2f} ms")
    print(f"  Min / Max        : {min(latencies):.2f} ms / {max(latencies):.2f} ms")
    print("================================================================\n")


if __name__ == "__main__":
    asyncio.run(run_benchmark(concurrency=50, total_requests=1000))
