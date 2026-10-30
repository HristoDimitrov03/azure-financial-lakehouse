# Extract + Gold export pipeline (feeds web/public/data/gold_metrics.json).
# Build:  docker build -t lakehouse-pipeline .
# Or use: docker compose run --rm pipeline

FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY config/ ./config/
COPY src/ ./src/
COPY scripts/ ./scripts/

# data/ and web/public/data/ are bind-mounted at runtime (see docker-compose.yml)
RUN mkdir -p data/raw data/export web/public/data

CMD ["sh", "-c", "python scripts/run_extract.py && python scripts/build_gold_export.py"]
