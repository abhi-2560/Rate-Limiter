/**
 * Sliding Window Visualizer
 * Continuous moving timeline animating individual request timestamps across a 10s window.
 */

export class SlidingWindowVisualizer {
  constructor() {
    this.windowSeconds = 10;
    this.capacity = 5;
    this.requests = []; // Array of timestamps (epoch ms)

    // DOM Elements
    this.trackEl = document.getElementById("sw-timeline-track");
    this.activeCountEl = document.getElementById("sw-active-count");
    this.nextSlotEl = document.getElementById("sw-next-slot");
    this.cardEl = document.getElementById("card-sliding-window");

    this.startAnimationLoop();
  }

  recordRequest() {
    const now = Date.now();
    this.requests.push(now);

    // Pulse card on request
    this.cardEl.classList.remove("pulse-success", "shake");
    void this.cardEl.offsetWidth;
    this.cardEl.classList.add("pulse-success");
  }

  recordRejection(retryAfter) {
    this.cardEl.classList.remove("shake", "pulse-success");
    void this.cardEl.offsetWidth;
    this.cardEl.classList.add("shake");
  }

  reset() {
    this.requests = [];
    this.trackEl.querySelectorAll(".req-pip").forEach((el) => el.remove());
    this.updateStats(Date.now());
  }

  startAnimationLoop() {
    const animate = () => {
      this.tick();
      requestAnimationFrame(animate);
    };
    requestAnimationFrame(animate);
  }

  tick() {
    const now = Date.now();
    const windowDurationMs = this.windowSeconds * 1000;
    const windowStartMs = now - windowDurationMs;

    // Filter out requests older than the 10-second window
    this.requests = this.requests.filter((ts) => ts > windowStartMs);

    // Update or create DOM pips
    const existingPips = this.trackEl.querySelectorAll(".req-pip");
    existingPips.forEach((p) => p.remove());

    this.requests.forEach((ts, idx) => {
      const elapsed = now - ts;
      const progress = elapsed / windowDurationMs; // 0 (now, right) to 1.0 (expired, left)
      const leftPercent = (1 - progress) * 100;

      const pip = document.createElement("div");
      pip.className = "req-pip";
      pip.style.left = `${leftPercent}%`;
      pip.title = `Request #${idx + 1} - ${(elapsed / 1000).toFixed(1)}s ago`;

      if (progress > 0.85) {
        pip.classList.add("evicting");
      }

      this.trackEl.appendChild(pip);
    });

    this.updateStats(now);
  }

  updateStats(now) {
    const active = this.requests.length;
    this.activeCountEl.textContent = `${active} / ${this.capacity}`;

    if (active >= this.capacity && this.requests.length > 0) {
      const oldestTs = this.requests[0];
      const remainingSec = Math.max(0, ((oldestTs + this.windowSeconds * 1000) - now) / 1000).toFixed(1);
      this.nextSlotEl.textContent = `In ${remainingSec}s`;
    } else {
      this.nextSlotEl.textContent = "Immediately";
    }
  }
}
