# Hugging Face Spaces Dockerfile — unified backend + worker
# All Python deps provide manylinux wheels, so gcc/C compiler not needed.
FROM python:3.11-slim AS builder

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir --prefer-binary --retries 5 --timeout 30 --user -r requirements.txt

FROM python:3.11-slim AS runtime

RUN addgroup --system --gid 1001 appgroup && adduser --system --uid 1001 appuser

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
