FROM python:3.11.9-slim-bookworm

WORKDIR /app

# Install minimal OS build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Pin power-framework core to audited immutable commit
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir "git+https://github.com/weby-homelab/power-framework.git@e0a1804858fa58781180d1dfe1eb601629199973"

COPY pyproject.toml .
COPY src/ ./src/

RUN pip install --no-cache-dir .


# Create dedicated non-root application user and group
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /bin/bash -m appuser && \
    mkdir -p /brain && \
    chown -R appuser:appgroup /app /brain

USER 10001:10001

ENV POWER_GUI_HOST=0.0.0.0
ENV POWER_GUI_PORT=8080
ENV POWER_GUI_VAULT_PATH=/brain
ENV POWER_GUI_AUTH_ENABLED=true

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/healthz', timeout=3)" || exit 1

CMD ["python", "-m", "power_gui.app", "--host", "0.0.0.0", "--port", "8080", "--vault", "/brain"]

