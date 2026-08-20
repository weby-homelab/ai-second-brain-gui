# 🤖 P.O.W.E.R-GUI — Operations & Deployment Guide for AI Agents

> **Scope:** Operations / deployment playbook (not an A2A 1.0 or AAIF conformance claim)  
> **Target Application:** `power-gui` (P.O.W.E.R-GUI v0.7.3)
> **Audience:** Autonomous AI Agents (Claude, Gemini, Antigravity, OpenCode, Codex, Cursor, AutoGPT, LangChain, FastMCP)

This document provides a deterministic, machine-actionable playbook for any AI agent tasked with deploying, configuring, verifying, or programmatically interacting with the **P.O.W.E.R-GUI Web Cockpit**. Runtime discovery metadata uses **`experimental/custom-discovery`** only.

---

## 📇 1. Experimental custom discovery metadata (runtime)

```json
{
  "protocol": "experimental/custom-discovery",
  "name": "power-gui",
  "version": "0.7.3",
  "description": "Production-grade, AI-native web cockpit and decision center for Obsidian Second Brain",
  "runtime": "FastAPI BFF / Python 3.11-3.14",
  "security_model": {
    "user_id": "10001:10001 (non-root)",
    "capabilities": "cap_drop: [ALL]",
    "rootfs": "read_only: true",
    "auth": "Session cookie (HMAC-SHA256) + Double-Submit CSRF",
    "isolation": "Tmpfs for /tmp and /home/appuser"
  },
  "interfaces": {
    "http_port": 8080,
    "host_binding": "127.0.0.1:8008 (or LAN IP for reverse proxy)",
    "sse_stream": "/tasks/api/events/stream",
    "health_endpoint": "/login",
    "vault_path": "/brain",
    "cache_path": "/data"
  }
}
```

---

## 🚀 2. Deterministic Installation Playbooks

### Playbook A: Production Docker Compose (Recommended)

When deploying via Docker Compose, follow this exact sequence:

1. **Pre-flight Vault Preparation:**
   Ensure the host Obsidian vault directory exists and is readable/writable by UID `10001` or world-accessible:
   ```bash
   mkdir -p /path/to/your/obsidian/brain
   chmod -R 775 /path/to/your/obsidian/brain
   ```

2. **Generate Persistent Secrets:**
   Generate a cryptographic secret key and choose a strong admin password:
   ```bash
   export POWER_GUI_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
   export POWER_GUI_ADMIN_PASSWORD="<generate-strong-password>"
   export POWER_GUI_BIND_ADDRESS="127.0.0.1"
   ```

3. **Deploy Docker Compose Stack:**
   Create and run the canonical hardened `docker-compose.yml`:
   ```yaml
   services:
     power-gui:
       image: webyhomelab/power-gui:0.7.3
       container_name: power-gui
       restart: unless-stopped
       init: true
       user: "10001:10001"
       security_opt:
         - no-new-privileges:true
       cap_drop:
         - ALL
       read_only: true
       tmpfs:
         - /tmp:rw,noexec,nosuid,size=512m
         - /home/appuser:rw,noexec,nosuid,size=128m
       ports:
         - "${POWER_GUI_BIND_ADDRESS:-127.0.0.1}:8008:8080"
       mem_limit: 1g
       cpus: 1.5
       pids_limit: 256
       ulimits:
         nofile:
           soft: 4096
           hard: 4096
       environment:
         - POWER_GUI_HOST=0.0.0.0
         - POWER_GUI_PORT=8080
         - POWER_GUI_VAULT_PATH=/brain
         - POWER_GUI_AUTH_ENABLED=true
         - POWER_GUI_ADMIN_PASSWORD=${POWER_GUI_ADMIN_PASSWORD}
         - POWER_GUI_SECRET_KEY=${POWER_GUI_SECRET_KEY}
         - POWER_GUI_COOKIE_SECURE=true
         - POWER_GUI_SESSION_MAX_AGE_SECONDS=86400
         - XDG_CACHE_HOME=/data/cache
         - POWER_CACHE_DIR=/data/power_cache
         - POWER_ALLOW_DENSE_FALLBACK=1
       volumes:
         - /path/to/your/obsidian/brain:/brain:rw
         - power_cache:/data

   volumes:
     power_cache:
       driver: local
   ```

   Execute launch:
   ```bash
   docker compose up -d
   ```

---

### Playbook B: Proxmox VE (LXC Container `LXC 200`)

When executing inside an unprivileged Proxmox LXC container:

1. **Mount Vault from Proxmox Host to LXC:**
   ```bash
   pct set 200 -mp0 /host/storage/brain,mp=/mnt/brain
   ```

2. **Execute Hardened Docker Run inside Container:**
   ```bash
   docker run -d \
     --name power-gui \
     --restart unless-stopped \
     -p "${POWER_GUI_BIND_ADDRESS:-127.0.0.1}:8008:8080" \
     --user 10001:10001 \
     --cap-drop ALL \
     --security-opt no-new-privileges:true \
     --read-only \
     --tmpfs /tmp:rw,noexec,nosuid,size=512m \
     --tmpfs /home/appuser:rw,noexec,nosuid,size=128m \
     -e POWER_GUI_AUTH_ENABLED=true \
     -e POWER_GUI_ADMIN_PASSWORD="<admin-password>" \
     -e POWER_GUI_SECRET_KEY="<secret-key>" \
     -e POWER_GUI_COOKIE_SECURE=true \
     -v /mnt/brain:/brain:rw \
     -v power_cache:/data \
     webyhomelab/power-gui:0.7.3
   ```

---

### Playbook C: Native Python Systemd Service

When deploying directly on bare-metal or a VM:

1. **Environment & Dependencies:**
   ```bash
   python3 -m venv venv
   ./venv/bin/pip install -U pip setuptools wheel
   ./venv/bin/pip install -e ".[dev]"
   ```

2. **Systemd Service Setup (`/etc/systemd/system/power-gui.service`):**
   ```ini
   [Unit]
   Description=P.O.W.E.R. GUI Web Cockpit
   After=network.target

   [Service]
   Type=simple
   User=root
   WorkingDirectory=/path/to/ai-second-brain-gui
   ExecStart=/path/to/ai-second-brain-gui/venv/bin/power-gui --host 127.0.0.1 --port 8008
   Restart=always
   RestartSec=3
   Environment=POWER_GUI_VAULT_PATH=/path/to/brain
   Environment=POWER_GUI_HOST=127.0.0.1
   Environment=POWER_GUI_PORT=8008
   Environment=POWER_GUI_AUTH_ENABLED=true
   Environment=POWER_GUI_ADMIN_PASSWORD="<admin-password>"
   Environment=POWER_GUI_SECRET_KEY="<secret-key>"

   [Install]
   WantedBy=multi-user.target
   ```

3. **Start Service:**
   ```bash
   systemctl daemon-reload
   systemctl enable power-gui --now
   ```

---

## 🔍 3. Automated Verification & Validation Gate

AI agents must perform this multi-step verification before declaring deployment complete:

### Step 1: Health Probe
```bash
# Verify HTTP listener is live and returns HTTP 200 on /login
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8008/login
# Expected Output: 200
```

### Step 2: Session Authentication & Cookie Extraction
```bash
# Submit credentials to obtain session and CSRF cookies
curl -s -i -X POST http://127.0.0.1:8008/login \
  -d "password=<admin-password>" \
  -c /tmp/cookies.txt
# Expected Header: Set-Cookie: power_gui_session=...; HttpOnly; SameSite=lax
# Expected Response: HTTP/1.1 303 See Other (Redirect to /)
```

### Step 3: Authenticated BFF Probe
```bash
# Verify authenticated access to dashboard
curl -s -b /tmp/cookies.txt http://127.0.0.1:8008/ | grep -q "P.O.W.E.R" && echo "PASS" || echo "FAIL"
# Expected Output: PASS
```

### Step 4: Real-time SSE Stream Connection Test
```bash
# Verify SSE event stream responds with 200 and text/event-stream
curl -s -N -b /tmp/cookies.txt --max-time 3 http://127.0.0.1:8008/tasks/api/events/stream \
  | head -n 5
# Expected Content: event: ... or : keep-alive comments
```

---

## 📡 4. HTTP API interaction reference (GUI BFF)

AI agents interacting with P.O.W.E.R-GUI must use the following structured endpoints:

| Endpoint | Method | Purpose | Agent Payload / Parameters |
| :--- | :---: | :--- | :--- |
| `/search` | `GET` | Multimodal Knowledge Search | `?q=<query>&mode=auto\|fts\|semantic\|rerank` |
| `/notes` | `GET` | List vault notes & metadata | `?folder=01_Projects` |
| `/notes/read?path=<path>` | `GET` | Read note content & parsed OKF | Returns sanitized HTML & raw content |
| `/notes/propose` | `POST` | Propose note creation or modification | Form: `path`, `content`, `expected_revision`, `csrf_token` |
| `/decisions` | `GET` | List pending human approval requests | Returns list of pending proposals |
| `/decisions/{id}/resolve`| `POST` | Approve/reject pending proposal | Form: `action=approve\|reject`, `csrf_token` |
| `/tasks` | `GET` | Kanban board & task list | Filter by state (`backlog`, `ready`, `working`) |
| `/tasks/new` | `POST` | Create new v2 task | Form: `title`, `description`, `category`, `csrf_token` |
| `/tasks/{id}/transition` | `POST` | Move task across state machine | Form: `new_state`, `expected_revision`, `csrf_token` |
| `/tasks/api/events/stream`| `GET` | Real-time SSE event stream | Header: `Accept: text/event-stream`; optional `task_id` and `since_sequence` cursor |
| `/federation` | `GET` | Fleet probe latencies & health | Returns node latency telemetry |

### Safe Note Mutation Protocol for AI Agents:
Agents **must never** write directly to `.md` files on disk. Always submit through the proposal workflow:
1. `GET /notes/read?path=<path>` to obtain the current note and `csrf_token`.
2. `POST /notes/propose` with proposed changes.
3. If human-in-the-loop is enabled, wait for decision resolution via `/decisions`.
4. Check `/receipts` for the immutable SHA-256 execution audit receipt.

---

## 🛡️ 5. Zero-Error Safety Invariants

1. **Non-Root Execution:** Container must always run as UID `10001` (`cap_drop: [ALL]`).
2. **Read-Only Root Filesystem:** Container rootfs must be mounted `--read-only`, utilizing dedicated tmpfs for `/tmp` and `/home/appuser`.
3. **Flock Concurrency Control:** Inode locks (`mutation.lock` with mode `0o600`) prevent race conditions during concurrent agent queries.
4. **Optimistic Locking:** All mutations must pass `expected_revision` to prevent silent overwrites of parallel agent edits.
5. **No Secret Leakage:** Never print `POWER_GUI_ADMIN_PASSWORD` or `POWER_GUI_SECRET_KEY` in shell outputs or agent logs.

---

## ✅ 6. Definition of Done (DoD) Checklist for AI Agents

- [ ] Vault directory is mounted read-write to `/brain`.
- [ ] Persistent cache volume is mounted to `/data`.
- [ ] Container starts with status `Up` (`docker ps -f name=power-gui`).
- [ ] Health probe `GET /login` returns HTTP 200.
- [ ] Authentication probe `POST /login` issues valid session cookie.
- [ ] Real-time SSE event stream responds with active stream.
- [ ] Unit & contract tests pass locally (`pytest tests/` — 35+ passed).
- [ ] No potential secrets or credentials committed into version control.
