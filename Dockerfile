FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
COPY src/ ./src/

# Install POWER core framework and POWER-GUI
RUN pip install --no-cache-dir /app

ENV POWER_GUI_HOST=0.0.0.0
ENV POWER_GUI_PORT=8080
ENV POWER_GUI_VAULT_PATH=/brain

EXPOSE 8080

CMD ["python", "-m", "power_gui.app", "--host", "0.0.0.0", "--port", "8080", "--vault", "/brain"]
