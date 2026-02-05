# Use official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Set work directory
WORKDIR /app

# Install system dependencies (build-essential removed to fix apt network issues)
# Most python packages have binary wheels now.
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     build-essential \
#     && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Create directories for logs and data
RUN mkdir -p logs data/knowledge_base

# Create a non-root user for security (optional but recommended)
# RUN useradd -m appuser && chown -R appuser /app
# USER appuser

# Default command (overridden in docker-compose)
CMD ["python", "main.py"]
