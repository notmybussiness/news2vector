# News RAG API Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY data-pipeline/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY data-pipeline/src ./src

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV MILVUS_HOST=milvus
ENV MILVUS_PORT=19530
ENV RAG_API_HOST=0.0.0.0
ENV RAG_API_PORT=8000

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run server
CMD ["python", "-m", "src.api.server"]
