/**
 * Token Bucket Visualizer
 * Manages token reservoir graphics, refill ticker, and countdown timer.
 */

export class TokenBucketVisualizer {
  constructor() {
    this.capacity = 5;
    this.windowSeconds = 30;
    this.refillRate = this.capacity / this.windowSeconds; // ~0.1666 tokens/s
    this.tokens = 5.0;
    this.lastUpdated = Date.now();
    this.countdownTimer = null;

    // DOM Elements
    this.liquidEl = document.getElementById("tb-liquid");
    this.tokensGridEl = document.getElementById("tb-tokens-grid");
    this.remainingValEl = document.getElementById("tb-remaining-val");
    this.resetValEl = document.getElementById("tb-reset-val");
    this.lockOverlayEl = document.getElementById("tb-lock-overlay");
    this.lockCountdownEl = document.getElementById("tb-lock-countdown");
    this.cardEl = document.getElementById("card-token-bucket");

    this.startRefillTicker();
  }

  startRefillTicker() {
    setInterval(() => {
      const now = Date.now();
      const elapsedSeconds = (now - this.lastUpdated) / 1000.0;
      this.lastUpdated = now;

      if (this.tokens < this.capacity) {
        this.tokens = Math.min(this.capacity, this.tokens + (elapsedSeconds * this.refillRate));
        this.render();
      }
    }, 250);
  }

  updateFromResponse(response) {
    if (response.ok) {
      const remaining = response.headers.remaining !== "-" ? parseInt(response.headers.remaining, 10) : Math.floor(this.tokens - 1);
      this.tokens = Math.max(0, remaining);
      this.lastUpdated = Date.now();

      // Trigger success flash
      this.cardEl.classList.remove("pulse-success", "shake");
      void this.cardEl.offsetWidth; // trigger reflow
      this.cardEl.classList.add("pulse-success");

      this.clearLock();
    } else if (response.status === 429) {
      this.tokens = 0;
      this.lastUpdated = Date.now();

      // Trigger shake animation
      this.cardEl.classList.remove("shake", "pulse-success");
      void this.cardEl.offsetWidth;
      this.cardEl.classList.add("shake");

      const retryAfter = parseInt(response.headers.retryAfter, 10) || 6;
      this.triggerLock(retryAfter);
    }
    this.render();
  }

  triggerLock(seconds) {
    if (this.countdownTimer) clearInterval(this.countdownTimer);
    let remainingSec = seconds;

    this.lockOverlayEl.classList.add("active");
    this.lockCountdownEl.textContent = `Throttled (${remainingSec}s)`;

    this.countdownTimer = setInterval(() => {
      remainingSec -= 1;
      if (remainingSec <= 0) {
        this.clearLock();
      } else {
        this.lockCountdownEl.textContent = `Throttled (${remainingSec}s)`;
      }
    }, 1000);
  }

  clearLock() {
    if (this.countdownTimer) {
      clearInterval(this.countdownTimer);
      this.countdownTimer = null;
    }
    this.lockOverlayEl.classList.remove("active");
  }

  reset() {
    this.tokens = this.capacity;
    this.lastUpdated = Date.now();
    this.clearLock();
    this.render();
  }

  render() {
    const fillPercent = Math.min(100, Math.max(0, (this.tokens / this.capacity) * 100));
    this.liquidEl.style.height = `${fillPercent}%`;

    const intTokens = Math.floor(this.tokens);
    this.remainingValEl.textContent = `${intTokens} / ${this.capacity}`;

    // Update tokens chip display
    const tokenElements = this.tokensGridEl.querySelectorAll(".token");
    tokenElements.forEach((el, index) => {
      if (index < intTokens) {
        el.classList.add("active");
      } else {
        el.classList.remove("active");
      }
    });

    // Reset In estimate
    const deficit = this.capacity - this.tokens;
    const timeToFull = deficit > 0 ? Math.ceil(deficit / this.refillRate) : 0;
    this.resetValEl.textContent = `${timeToFull}s`;
  }
}
