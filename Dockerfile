FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install power-framework core from GitHub main
RUN pip install --no-cache-dir "git+https://github.com/weby-homelab/power-framework.git@main"

COPY pyproject.toml .
COPY src/ ./src/

RUN pip install --no-cache-dir -e .

ENV POWER_GUI_HOST=0.0.0.0
ENV POWER_GUI_PORT=8080
ENV POWER_GUI_VAULT_PATH=/brain
ENV POWER_GUI_AUTH_ENABLED=false

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/dashboard', timeout=3)" || exit 1

CMD ["python", "-m", "power_gui.app", "--host", "0.0.0.0", "--port", "8080", "--vault", "/brain"]
