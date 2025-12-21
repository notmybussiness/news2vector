FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download model at build time
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('jhgan/ko-sroberta-multitask')"

# Copy source
COPY src/ ./src/

# Expose port
EXPOSE 8001

# Run server
CMD ["python", "-m", "src.main"]
