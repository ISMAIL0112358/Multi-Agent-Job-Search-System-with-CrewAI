FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ /app/backend/

# Create data directory for SQLite & ChromaDB
RUN mkdir -p /app/data

# Set environment variables
ENV PORT=8000
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8000

# Start server
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
