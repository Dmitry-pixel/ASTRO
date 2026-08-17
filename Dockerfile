# ============================================================
# Astro Gates — Human Design API
# Multi-stage Docker build
# ============================================================

# Stage 1: Builder — compile C extensions (numpy, pysweph)
FROM python:3.12-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ python3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# Stage 2: Runtime
FROM python:3.12-slim

WORKDIR /app

# Unbuffered output — logs appear instantly in `docker logs`
ENV PYTHONUNBUFFERED=1
# Module search path — finds humandesign package in src/ without pip install
ENV PYTHONPATH="/app/src"
# Swiss Ephemeris data files
ENV SE_EPHE_PATH=/app/ephe

# Install curl for lightweight healthcheck (~5ms vs python ~500ms)
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Copy pre-built Python packages from builder
COPY --from=builder /install /usr/local

# Copy application code (.dockerignore filters out secrets and junk)
COPY . /app

# Non-root user for security
# /app/data is the volume mount point — must be writable for SQLite + .env
RUN useradd -m -u 1000 appuser \
    && mkdir -p /app/data \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 9021

# Healthcheck defined in docker-compose.yml (single source of truth, easier to change)

CMD ["uvicorn", "humandesign.api:app", "--host", "0.0.0.0", "--port", "9021", "--workers", "1"]
