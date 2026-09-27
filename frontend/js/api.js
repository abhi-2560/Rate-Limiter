/**
 * RateShield API Client
 * Sends HTTP requests, records client round-trip latency,
 * and extracts RFC 6585 / standard rate limiting response headers.
 */

export class ApiClient {
  constructor(getBaseUrl) {
    this.getBaseUrl = getBaseUrl;
  }

  async sendRequest(endpoint, options = {}) {
    const baseUrl = this.getBaseUrl().replace(/\/$/, "");
    const url = `${baseUrl}${endpoint}`;
    const startTime = performance.now();

    const headers = {
      "Accept": "application/json",
      ...(options.headers || {}),
    };

    if (options.body && typeof options.body === "object") {
      headers["Content-Type"] = "application/json";
      options.body = JSON.stringify(options.body);
    }

    try {
      const response = await fetch(url, {
        method: options.method || "GET",
        headers,
        body: options.body,
      });

      const elapsedMs = Math.round(performance.now() - startTime);
      let data = null;
      try {
        data = await response.json();
      } catch (err) {
        data = { error: "Non-JSON response" };
      }

      // Extract RateLimit headers
      const rateLimitHeaders = {
        limit: response.headers.get("X-RateLimit-Limit") || "-",
        remaining: response.headers.get("X-RateLimit-Remaining") || "-",
        reset: response.headers.get("X-RateLimit-Reset") || "-",
        retryAfter: response.headers.get("Retry-After") || "-",
      };

      return {
        ok: response.ok,
        status: response.status,
        statusText: response.statusText,
        latencyMs: elapsedMs,
        headers: rateLimitHeaders,
        data,
        timestamp: new Date().toLocaleTimeString(),
        endpoint,
        method: options.method || "GET",
      };
    } catch (networkError) {
      const elapsedMs = Math.round(performance.now() - startTime);
      return {
        ok: false,
        status: 0,
        statusText: "Network Error / Offline",
        latencyMs: elapsedMs,
        headers: { limit: "-", remaining: "-", reset: "-", retryAfter: "-" },
        data: { error: networkError.message },
        timestamp: new Date().toLocaleTimeString(),
        endpoint,
        method: options.method || "GET",
      };
    }
  }

  async checkHealth() {
    return this.sendRequest("/api/health");
  }

  async resetDemoState() {
    return this.sendRequest("/api/demo/reset", { method: "POST" });
  }
}
