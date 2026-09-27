/**
 * RateShield Main Application Controller
 * Coordinates API requests, visualizers, state management, and telemetry streaming.
 */

import { ApiClient } from "./api.js";
import { TokenBucketVisualizer } from "./visualizers/token_bucket.js";
import { SlidingWindowVisualizer } from "./visualizers/sliding_window.js";

class App {
  constructor() {
    this.apiClient = new ApiClient(() => this.getBackendUrl());
    this.tokenBucket = new TokenBucketVisualizer();
    this.slidingWindow = new SlidingWindowVisualizer();

    // Tier state
    this.selectedTier = "free";
    this.selectedApiKey = "key_free_user";
    this.tierLimit = 30;
    this.tierRemaining = 30;

    // Auth state
    this.authMaxAttempts = 3;
    this.authRemainingAttempts = 3;
    this.authLockTimer = null;

    // Telemetry state
    this.telemetryLogs = [];
    this.activeFilter = "all";

    this.initDOMElements();
    this.bindEvents();
    this.startHealthPolling();
  }

  getBackendUrl() {
    return this.backendUrlInput.value.trim() || "http://localhost:8000";
  }

  initDOMElements() {
    this.backendUrlInput = document.getElementById("backend-url");
    this.healthIndicator = document.getElementById("health-indicator");
    this.healthText = document.getElementById("health-text");
    this.storageBadge = document.getElementById("storage-badge");
    this.failOpenBadge = document.getElementById("failopen-badge");
    this.btnResetDemo = document.getElementById("btn-reset-demo");

    // Token Bucket buttons
    this.btnTbSingle = document.getElementById("btn-tb-single");
    this.btnTbBurst = document.getElementById("btn-tb-burst");

    // Sliding Window buttons
    this.btnSwSingle = document.getElementById("btn-sw-single");
    this.btnSwBurst = document.getElementById("btn-sw-burst");

    // Tier components
    this.tierPillContainer = document.getElementById("tier-pill-selector");
    this.activeHeaderPreview = document.getElementById("active-header-preview");
    this.tierProgressFill = document.getElementById("tier-progress-fill");
    this.tierRemainingText = document.getElementById("tier-remaining-text");
    this.tierLimitText = document.getElementById("tier-limit-text");
    this.btnTieredSingle = document.getElementById("btn-tiered-single");

    // Auth components
    this.authCard = document.getElementById("card-auth-login");
    this.authPips = document.getElementById("auth-pips");
    this.btnLoginBad = document.getElementById("btn-login-bad");
    this.btnLoginGood = document.getElementById("btn-login-good");
    this.loginPasswordInput = document.getElementById("login-password");
    this.authLockBanner = document.getElementById("auth-lock-banner");
    this.authLockTimerEl = document.getElementById("auth-lock-timer");

    // Telemetry
    this.telemetryTbody = document.getElementById("telemetry-tbody");
    this.telemetryCount = document.getElementById("telemetry-count");
    this.btnClearLogs = document.getElementById("btn-clear-logs");
    this.filterButtons = document.querySelectorAll(".filter-btn");
  }

  bindEvents() {
    // Demo Reset
    this.btnResetDemo.addEventListener("click", () => this.handleResetDemo());

    // Token Bucket actions
    this.btnTbSingle.addEventListener("click", () => this.handleTokenBucketRequest(1));
    this.btnTbBurst.addEventListener("click", () => this.handleTokenBucketBurst(6));

    // Sliding Window actions
    this.btnSwSingle.addEventListener("click", () => this.handleSlidingWindowRequest());
    this.btnSwBurst.addEventListener("click", () => this.handleSlidingWindowBurst(6));

    // Tier selection
    this.tierPillContainer.querySelectorAll(".tier-pill").forEach((pill) => {
      pill.addEventListener("click", (e) => this.handleTierSelect(e.currentTarget));
    });
    this.btnTieredSingle.addEventListener("click", () => this.handleTieredRequest());

    // Auth actions
    this.btnLoginBad.addEventListener("click", () => this.handleLogin("wrong_password_987"));
    this.btnLoginGood.addEventListener("click", () => this.handleLogin("secret123"));

    // Telemetry actions
    this.btnClearLogs.addEventListener("click", () => this.clearTelemetryLogs());
    this.filterButtons.forEach((btn) => {
      btn.addEventListener("click", (e) => {
        this.filterButtons.forEach((b) => b.classList.remove("active"));
        e.currentTarget.classList.add("active");
        this.activeFilter = e.currentTarget.dataset.filter;
        this.renderTelemetryLogs();
      });
    });
  }

  /* ------------------------------------------------------------------------
     System Health & Info
     ------------------------------------------------------------------------ */

  async startHealthPolling() {
    const check = async () => {
      const res = await this.apiClient.checkHealth();
      if (res.ok) {
        this.healthIndicator.className = "status-indicator status-online";
        this.healthText.textContent = "Backend Online";
        this.storageBadge.textContent = (res.data?.storage || "memory").toUpperCase();
        this.failOpenBadge.style.display = res.data?.fail_open ? "inline-flex" : "none";
      } else {
        this.healthIndicator.className = "status-indicator status-offline";
        this.healthText.textContent = "Backend Offline";
      }
    };
    await check();
    setInterval(check, 8000);
  }

  async handleResetDemo() {
    this.btnResetDemo.disabled = true;
    const res = await this.apiClient.resetDemoState();
    this.logTelemetry(res);

    this.tokenBucket.reset();
    this.slidingWindow.reset();
    this.resetAuthState();
    this.tierRemaining = this.tierLimit;
    this.updateTierDisplay();

    setTimeout(() => {
      this.btnResetDemo.disabled = false;
    }, 400);
  }

  /* ------------------------------------------------------------------------
     1. Token Bucket Handler
     ------------------------------------------------------------------------ */

  async handleTokenBucketRequest(cost = 1) {
    this.btnTbSingle.disabled = true;
    const res = await this.apiClient.sendRequest("/api/public");
    this.tokenBucket.updateFromResponse(res);
    this.logTelemetry(res);
    this.btnTbSingle.disabled = false;
  }

  async handleTokenBucketBurst(count = 6) {
    this.btnTbBurst.disabled = true;
    const promises = Array.from({ length: count }, () =>
      this.apiClient.sendRequest("/api/public")
    );
    const results = await Promise.all(promises);

    results.forEach((res) => {
      this.tokenBucket.updateFromResponse(res);
      this.logTelemetry(res);
    });

    setTimeout(() => {
      this.btnTbBurst.disabled = false;
    }, 600);
  }

  /* ------------------------------------------------------------------------
     2. Sliding Window Handler
     ------------------------------------------------------------------------ */

  async handleSlidingWindowRequest() {
    this.btnSwSingle.disabled = true;
    const res = await this.apiClient.sendRequest("/api/sliding");
    if (res.ok) {
      this.slidingWindow.recordRequest();
    } else {
      this.slidingWindow.recordRejection(res.headers.retryAfter);
    }
    this.logTelemetry(res);
    this.btnSwSingle.disabled = false;
  }

  async handleSlidingWindowBurst(count = 6) {
    this.btnSwBurst.disabled = true;
    const promises = Array.from({ length: count }, () =>
      this.apiClient.sendRequest("/api/sliding")
    );
    const results = await Promise.all(promises);

    results.forEach((res) => {
      if (res.ok) {
        this.slidingWindow.recordRequest();
      } else {
        this.slidingWindow.recordRejection(res.headers.retryAfter);
      }
      this.logTelemetry(res);
    });

    setTimeout(() => {
      this.btnSwBurst.disabled = false;
    }, 600);
  }

  /* ------------------------------------------------------------------------
     3. Tiered Handler
     ------------------------------------------------------------------------ */

  handleTierSelect(pillEl) {
    this.tierPillContainer.querySelectorAll(".tier-pill").forEach((p) => p.classList.remove("active"));
    pillEl.classList.add("active");

    this.selectedTier = pillEl.dataset.tier;
    this.selectedApiKey = pillEl.dataset.key;
    this.tierLimit = parseInt(pillEl.dataset.limit, 10);
    this.tierRemaining = this.tierLimit;

    if (this.selectedApiKey) {
      this.activeHeaderPreview.textContent = `X-API-Key: ${this.selectedApiKey}`;
    } else {
      this.activeHeaderPreview.textContent = `(No API Key • Identified by Client IP)`;
    }

    this.updateTierDisplay();
  }

  async handleTieredRequest() {
    this.btnTieredSingle.disabled = true;
    const headers = {};
    if (this.selectedApiKey) {
      headers["X-API-Key"] = this.selectedApiKey;
    }

    const res = await this.apiClient.sendRequest("/api/tiered", { headers });
    if (res.headers.remaining !== "-") {
      this.tierRemaining = parseInt(res.headers.remaining, 10);
    } else if (res.ok) {
      this.tierRemaining = Math.max(0, this.tierRemaining - 1);
    }
    this.updateTierDisplay();
    this.logTelemetry(res);
    this.btnTieredSingle.disabled = false;
  }

  updateTierDisplay() {
    const percent = Math.min(100, Math.max(0, (this.tierRemaining / this.tierLimit) * 100));
    this.tierProgressFill.style.width = `${percent}%`;
    this.tierRemainingText.textContent = `${this.tierRemaining} requests remaining`;
    this.tierLimitText.textContent = `Quota: ${this.tierLimit} / 60s`;
  }

  /* ------------------------------------------------------------------------
     4. Auth Brute-Force Handler
     ------------------------------------------------------------------------ */

  async handleLogin(password) {
    this.loginPasswordInput.value = password;
    this.btnLoginBad.disabled = true;
    this.btnLoginGood.disabled = true;

    const res = await this.apiClient.sendRequest("/api/auth/login", {
      method: "POST",
      body: { username: "admin", password },
    });

    if (res.status === 429) {
      this.authRemainingAttempts = 0;
      this.renderAuthPips();
      this.triggerAuthLockout(parseInt(res.headers.retryAfter, 10) || 60);
      this.authCard.classList.remove("shake");
      void this.authCard.offsetWidth;
      this.authCard.classList.add("shake");
    } else {
      if (res.headers.remaining !== "-") {
        this.authRemainingAttempts = parseInt(res.headers.remaining, 10);
      } else {
        this.authRemainingAttempts = Math.max(0, this.authRemainingAttempts - 1);
      }
      this.renderAuthPips();
      if (this.authRemainingAttempts === 0) {
        this.triggerAuthLockout(60);
      }
    }

    this.logTelemetry(res);

    if (this.authRemainingAttempts > 0) {
      this.btnLoginBad.disabled = false;
      this.btnLoginGood.disabled = false;
    }
  }

  renderAuthPips() {
    const pips = [
      document.getElementById("auth-pip-1"),
      document.getElementById("auth-pip-2"),
      document.getElementById("auth-pip-3"),
    ];
    pips.forEach((pip, index) => {
      if (index < this.authRemainingAttempts) {
        pip.className = "pip active";
      } else {
        pip.className = "pip exhausted";
      }
    });
  }

  triggerAuthLockout(seconds) {
    if (this.authLockTimer) clearInterval(this.authLockTimer);
    let remainingSec = seconds;

    this.authLockBanner.style.display = "flex";
    this.authLockTimerEl.textContent = `${remainingSec}s`;
    this.btnLoginBad.disabled = true;
    this.btnLoginGood.disabled = true;

    this.authLockTimer = setInterval(() => {
      remainingSec -= 1;
      if (remainingSec <= 0) {
        this.resetAuthState();
      } else {
        this.authLockTimerEl.textContent = `${remainingSec}s`;
      }
    }, 1000);
  }

  resetAuthState() {
    if (this.authLockTimer) {
      clearInterval(this.authLockTimer);
      this.authLockTimer = null;
    }
    this.authRemainingAttempts = this.authMaxAttempts;
    this.authLockBanner.style.display = "none";
    this.renderAuthPips();
    this.btnLoginBad.disabled = false;
    this.btnLoginGood.disabled = false;
  }

  /* ------------------------------------------------------------------------
     5. Telemetry & Log Inspector
     ------------------------------------------------------------------------ */

  logTelemetry(entry) {
    this.telemetryLogs.unshift(entry);
    if (this.telemetryLogs.length > 50) {
      this.telemetryLogs.pop();
    }
    this.renderTelemetryLogs();
  }

  clearTelemetryLogs() {
    this.telemetryLogs = [];
    this.renderTelemetryLogs();
  }

  renderTelemetryLogs() {
    const filtered = this.telemetryLogs.filter((log) => {
      if (this.activeFilter === "200") return log.status === 200;
      if (this.activeFilter === "429") return log.status === 429;
      return true;
    });

    this.telemetryCount.textContent = `${this.telemetryLogs.length} requests`;

    if (filtered.length === 0) {
      this.telemetryTbody.innerHTML = `
        <tr class="empty-row">
          <td colspan="9">No matching logs found. Click any action above to generate traffic.</td>
        </tr>
      `;
      return;
    }

    this.telemetryTbody.innerHTML = filtered
      .map((log) => {
        const is200 = log.status === 200;
        const statusBadgeClass = is200 ? "status-200" : log.status === 429 ? "status-429" : "status-429";
        const retryAfterFormatted = log.headers.retryAfter !== "-" ? `${log.headers.retryAfter}s` : "-";

        return `
          <tr>
            <td>${log.timestamp}</td>
            <td><strong>${log.method}</strong></td>
            <td><code>${log.endpoint}</code></td>
            <td><span class="status-badge ${statusBadgeClass}">${log.status || "ERR"}</span></td>
            <td>${log.latencyMs} ms</td>
            <td>${log.headers.limit}</td>
            <td>${log.headers.remaining}</td>
            <td>${log.headers.reset}</td>
            <td>${retryAfterFormatted}</td>
          </tr>
        `;
      })
      .join("");
  }
}

// Initialize on DOM load
window.addEventListener("DOMContentLoaded", () => {
  new App();
});
