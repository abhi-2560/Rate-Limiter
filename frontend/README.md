# RateShield Frontend Visualizer

An interactive developer dashboard for testing and visualizing the FastAPI Rate Limiter algorithms in real time.

## Features

- **Token Bucket Visualizer**: Animated fluid/token reservoir with continuous refill tick, burst simulator, and live countdown timer.
- **Sliding Window Timeline**: Continuous rolling 10-second timeline track plotting incoming request timestamps and evicting expired ones.
- **Tiered API Key Playground**: Interactive tier switcher (Anonymous, Free, Pro, Enterprise) testing dynamic quota allocation.
- **Brute-Force Auth Protection**: Mock login screen simulating strict IP-level credential stuffing protection.
- **RFC 6585 Telemetry Inspector**: Real-time console recording HTTP latency, status codes, and standard rate limit headers (`X-RateLimit-*`, `Retry-After`).

## Running the Frontend

The frontend is built using **Vanilla HTML5, Vanilla CSS3, and ES6 JavaScript** with no npm build steps required.

### Option 1: Python Built-in HTTP Server
From the project root:
```bash
python3 -m http.server 3000 --directory frontend
```
Then visit `http://localhost:3000` in your browser.

### Option 2: Live Server / VS Code / Cursor
Right-click `frontend/index.html` and select **Open with Live Server**.

### Option 3: npx serve
```bash
npx serve frontend -p 3000
```
