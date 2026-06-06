# Hugging Face Spaces Dockerfile — unified backend + worker
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/
COPY context/ ./context/
COPY database/ ./database/
COPY alembic.ini .

ENV QUEUE_MODE=local
ENV PYTHONPATH=/app

EXPOSE 7860

CMD ["python", "backend/hf_main.py"]
