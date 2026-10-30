# -----------------------------------------------------------------------------
# Dockerfile — packages the Streamlit dashboard for free hosting (Render/Koyeb)
# Sprint 0: skeleton only. We flesh this out in Sprint 6 (Portfolio Pivot).
#
# Build (later):  docker build -t azure-financial-lakehouse .
# Run   (later):  docker run -p 8501:8501 azure-financial-lakehouse
# -----------------------------------------------------------------------------

FROM python:3.11-slim

WORKDIR /app

# System deps (kept minimal for a lean image)
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App + local exported Gold data (Portfolio Pivot path)
COPY app/ ./app/
COPY data/export/ ./data/export/
COPY config/ ./config/

EXPOSE 8501

# Streamlit must bind 0.0.0.0 inside containers
CMD ["streamlit", "run", "app/streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
