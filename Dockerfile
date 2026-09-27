# CareConnect - Production Container Image
FROM python:3.13-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

WORKDIR /app

# Install system dependencies if required
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Copy and install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create database directory if not existing and ensure permissions
RUN mkdir -p /app/database

# Expose port (default 8080 for Google Cloud Run)
EXPOSE 8080

# Run with Gunicorn on 0.0.0.0 listening to 
CMD exec gunicorn --bind 0.0.0.0: --workers 2 --threads 4 --timeout 60 app:app
