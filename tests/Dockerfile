# Test Runner Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        gcc \
        python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements from backend (tests use same dependencies)
COPY requirements.txt ./backend_requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r backend_requirements.txt

# Copy test files
COPY . .

# Create reports directory
RUN mkdir -p reports

# Create non-root user
RUN adduser --disabled-password --gecos '' testuser \
    && chown -R testuser:testuser /app
USER testuser

# Default command to run all tests
CMD ["python", "run_all_tests.py", "--backend-url", "http://backend:5001", "--frontend-url", "http://frontend:3002"]
