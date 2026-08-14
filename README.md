# 🧠 P.O.W.E.R-GUI

[🇺🇸 English](README.md) | [🇺🇦 Українська](README.ua.md)

[![Docker Image](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://hub.docker.com/r/webyhomelab/power-gui)
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org)
[![P.O.W.E.R](https://img.shields.io/badge/P.O.W.E.R-3.7+-FF6B6B?style=for-the-badge)](https://github.com/weby-homelab/power-framework)
[![Tailscale](https://img.shields.io/badge/Tailscale-5F259F?style=for-the-badge&logo=tailscale&logoColor=white)](https://tailscale.com)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

![P.O.W.E.R-GUI Dashboard](second-brain-portal-EN.png)

![P.O.W.E.R-GUI Knowledge Graph](SB-Graph.gif)

**P.O.W.E.R-GUI** is the production-grade, AI-native web cockpit and decision center for your personal [Obsidian](https://obsidian.md) knowledge base (Second Brain). Designed strictly as a **Docker-First** application, it bridges human operators and autonomous AI agents through the **P.O.W.E.R Framework (P.A.R.A. + OKF v0.1 + Graph RAG + LLM-Wiki)**.

---

## 🏛️ Architecture & Core Principles

P.O.W.E.R-GUI adopts the **Backend-For-Frontend (BFF)** pattern built on FastAPI and Pydantic v2 Settings. It communicates exclusively through the canonical `PowerClient` boundary to the P.O.W.E.R `ApplicationService`, guaranteeing zero unvalidated direct writes to your knowledge vault.

```
┌────────────────────────────────────────────────────────────────────────┐
│                               OPERATOR                                 │
│        (Knowledge Graph / Hybrid Search / Task & Decision Queue)       │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ HTTP / SSE (Tailscale Protected)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        P.O.W.E.R-GUI (Docker)                          │
│   [Dashboard]  [Notes Editor]  [Task Manager v2]  [Decision Queue]     │
│   [Bleach Sanitizer]  [CSRF Defense]  [Strict CSP]  [WCAG 2.2 AA]      │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ PowerClient Port
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                     P.O.W.E.R Application API v2                       │
│        • Proposal Gate      • OKF Metadata Linter   • Event Ledger     │
│        • Task Store (flock) • Source Service        • Receipts Engine  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Direct / Inode I/O
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                         /brain (Obsidian Vault)                        │
└────────────────────────────────────────────────────────────────────────┘
```

---

## ✨ Key Capabilities

### 1. 📋 Canonical Task Manager v2 Cockpit
- **Interactive Kanban Swimlanes:** Seamlessly track tasks across lifecycle states: `backlog` ➔ `ready` ➔ `in-progress` ➔ `blocked` / `input-required` / `auth-required` ➔ `completed` / `failed`.
- **Monotonic Revision Control:** Concurrency is protected via `expected_revision` checks to eliminate lost updates.
- **Append-Only Event Ledger:** Every task transition produces an immutable audit event with a SHA-256 payload digest.
- **Real-Time SSE Streaming:** Live status updates streamed directly to the browser via Server-Sent Events (`/tasks/api/events/stream`).

### 2. 🛡️ Transactional Note Editor & Proposal Gate
- **Human-in-the-Loop Workflow:** AI agents and operators submit mutations via proposals (`Edit` ➔ `Propose` ➔ `Lint Validation` ➔ `Human Approval` ➔ `Apply`).
- **Zero Full Overwrites:** Protects against unintentional data wipeouts by enforcing atomic diff reviews and immutable receipts.
- **ETag Concurrency Guard:** Prevents mid-air collision when editing notes simultaneously.

### 3. 🌐 Dynamic 2D Force-Directed Knowledge Graph
- Visualizes vault topologies and note relations in real time using D3 force layout.
- Provides global vault views as well as localized 2-depth subtrees for individual notes.
- **WCAG 2.2 AA Accessibility:** Includes high-contrast matrix fallbacks for screen readers and keyboard navigation.

### 4. 🔍 Multi-Modal Hybrid Search
- Seamlessly query notes across four search backends:
  - `Auto`: Hybrid dense semantic retrieval with full-text fallback.
  - `FTS`: Lean BM25 full-text search with token proximity matching.
  - `Semantic`: Dense vector embeddings (e.g., `BGE-M3` 1024d).
  - `Reranked`: Cross-encoder scoring for deep contextual relevance.

### 5. 🔒 Enterprise-Grade Security & Sanitization
- **Bleach HTML Sanitization:** Comprehensive protection against XSS injections, malformed links, and adversarial payloads.
- **HMAC-SHA256 CSRF Tokens:** Enforced on all mutating HTTP POST endpoints.
- **Strict Content-Security-Policy (CSP):** Zero external CDN dependencies; all scripts, fonts, and stylesheets are self-hosted.
- **Path Traversal Defense:** Strict `PermissionError` enforcement preventing directory escapes outside the vault boundary.

---

## 🐳 Docker Deployment (Standard & Recommended)

P.O.W.E.R-GUI is designed to run exclusively in Docker.

### 1. One-Line Quickstart

```bash
docker run -d \
  --name power-gui \
  --restart unless-stopped \
  -p 8008:8080 \
  -v /path/to/your/obsidian/brain:/brain:rw \
  webyhomelab/power-gui:latest
```

Open your browser at `http://<your-host-ip>:8008`.

---

### 2. Docker Compose Setup

Create a `docker-compose.yml` file:

```yaml
version: '3.8'

services:
  power-gui:
    image: webyhomelab/power-gui:latest
    container_name: power-gui
    restart: unless-stopped
    ports:
      - "8008:8080"
    environment:
      - POWER_GUI_HOST=0.0.0.0
      - POWER_GUI_PORT=8080
      - POWER_GUI_VAULT_PATH=/brain
      - POWER_GUI_AUTH_ENABLED=false
    volumes:
      - /path/to/your/obsidian/brain:/brain:rw
```

Start the service:

```bash
docker compose up -d
```

---

### 3. Proxmox VE (LXC Container) Deployment

When running inside an unprivileged Proxmox LXC container (e.g. `LXC 200`):

1. **Mount host vault to the container from Proxmox host:**
   ```bash
   pct set 200 -mp0 /root/geminicli/brain,mp=/mnt/brain
   ```

2. **Run container inside LXC with mapped volume:**
   ```bash
   docker run -d \
     --name power-gui \
     --restart unless-stopped \
     -p 8008:8080 \
     -v /mnt/brain:/brain:rw \
     webyhomelab/power-gui:latest
   ```

---

## ⚙️ Configuration Reference

Configuration is managed entirely via environment variables (with the `POWER_GUI_` prefix):

| Variable | Type | Default | Description |
| :--- | :---: | :---: | :--- |
| `POWER_GUI_HOST` | `str` | `0.0.0.0` | IP address for Uvicorn to bind. |
| `POWER_GUI_PORT` | `int` | `8080` | Internal listening port. |
| `POWER_GUI_VAULT_PATH` | `Path` | `/brain` | Absolute path to mounted Obsidian vault. |
| `POWER_GUI_AUTH_ENABLED` | `bool` | `false` | Enable session cookie authentication. |
| `POWER_GUI_ADMIN_PASSWORD_HASH` | `str` | `""` | SHA256 / PBKDF2 hash of admin password. |
| `POWER_GUI_SECRET_KEY` | `str` | `"power-secret-key-12345"` | Secret key used for signing session and CSRF tokens. |
| `POWER_GUI_SESSION_MAX_AGE_SECONDS`| `int` | `86400` | Session lifetime (default: 24 hours). |
| `POWER_GUI_COOKIE_SECURE` | `bool` | `false` | Set to `true` when serving over HTTPS. |
| `POWER_GUI_COOKIE_SAMESITE` | `str` | `lax` | Cookie SameSite policy (`lax`, `strict`, `none`). |

---

## 🧪 Testing & Verification

Run the test suite and linters locally:

```bash
# Run contract and unit test suite
pytest tests/ -v

# Run code style & security linter
ruff check src tests
```

---

## 📄 License

Distributed under the **MIT License**. See [LICENSE](LICENSE) for details.
