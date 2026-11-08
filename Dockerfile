# syntax=docker/dockerfile:1
FROM python:3.12-slim

# System dependencies for audio and image processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency files
COPY requirements.txt setup.py ./

# Install python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application codebase
COPY . .

# Expose ports: 8000 for Studio & API
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/report/health')" || exit 1

# Start server
CMD ["python", "run_server.py"]

