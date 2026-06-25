# Hugging Face Spaces Dockerfile — unified backend + worker
# gcc is in builder (not runtime) so C extensions can compile from source
# if no pre-built wheel is available for the target platform (ARM64).
FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends gcc \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir --prefer-binary --retries 5 --timeout 30 --user -r requirements.txt

FROM python:3.11-slim AS runtime

RUN useradd -m -u 1001 appuser

WORKDIR /app

COPY --from=builder /root/.local /home/appuser/.local
COPY backend/ ./backend/
COPY context/ ./context/
COPY database/ ./database/
COPY alembic.ini .

RUN chown -R appuser:appuser /home/appuser/.local

ENV QUEUE_MODE=local
ENV PYTHONPATH=/app
ENV PATH=/home/appuser/.local/bin:$PATH

USER appuser

EXPOSE 7860

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:7860/health')" || exit 1

CMD ["python", "backend/hf_main.py"]
