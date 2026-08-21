FROM python:3.13.15-slim-bookworm@sha256:00faa2debb87529f9f0764e9491d8ba400a3678976616c3bd7cb193745ac20d1

ARG POWER_FRAMEWORK_COMMIT=527cc8a77187e9fa6d724b604d1a6634545da575

WORKDIR /app

# Install minimal OS build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install the exact suite-reviewed POWER revision with semantic dense embeddings.
RUN pip install --no-cache-dir "power-framework[semantic] @ git+https://github.com/weby-homelab/power-framework.git@${POWER_FRAMEWORK_COMMIT}"

COPY pyproject.toml .
COPY src/ ./src/
COPY entrypoint.sh /app/entrypoint.sh

RUN pip install --no-cache-dir .


# Create dedicated non-root application user, group, and cache directories
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /bin/bash -m appuser && \
    mkdir -p /brain /data/cache /data/power_cache /tmp/cache /home/appuser/.cache && \
    chown -R appuser:appgroup /app /brain /data /tmp/cache /home/appuser && \
    chmod +x /app/entrypoint.sh

USER 10001:10001

ENV POWER_GUI_HOST=0.0.0.0
ENV POWER_GUI_PORT=8080
ENV POWER_GUI_VAULT_PATH=/brain
ENV POWER_GUI_AUTH_ENABLED=true
# /data is the named volume mount point; XDG_CACHE_HOME must point here
# so the FTS SQLite DB survives container restarts.
ENV XDG_CACHE_HOME=/data/cache
ENV POWER_CACHE_DIR=/data/power_cache
ENV POWER_ALLOW_DENSE_FALLBACK=1

EXPOSE 8080

# Extended start-period to allow FTS pre-warm on first boot with large vaults
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/healthz', timeout=5)"]

ENTRYPOINT ["/app/entrypoint.sh"]
