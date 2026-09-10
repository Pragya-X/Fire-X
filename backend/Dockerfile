FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN useradd --create-home firex && mkdir -p /app/data /app/uploads /app/models && chown -R firex:firex /app
ENV DATA_DIR=/app/data UPLOAD_DIR=/app/uploads MODEL_DIR=/app/models
USER firex

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --retries=5 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health')" || exit 1

# Demo seeding requires DEMO_MODE=true and a nonproduction environment.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]