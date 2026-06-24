# Hugging Face Spaces Dockerfile — unified backend + worker
# Stage 1: Builder
FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim

RUN addgroup --system --gid 1001 appgroup && adduser --system --uid 1001 appuser

WORKDIR /app

COPY --from=builder /root/.local /home/appuser/.local
RUN chown -R appuser:appuser /home/appuser/.local

COPY backend/ ./backend/
COPY context/ ./context/
COPY database/ ./database/
COPY alembic.ini .

ENV QUEUE_MODE=local
ENV PYTHONPATH=/app
ENV PATH=/home/appuser/.local/bin:$PATH

USER appuser

EXPOSE 7860

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:7860/health')" || exit 1

CMD ["python", "backend/hf_main.py"]
