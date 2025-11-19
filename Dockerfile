# Multi-stage build for optimized Cloud Run deployment

# Stage 1: Builder
FROM python:3.10-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    postgresql-client \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime
FROM python:3.10-slim

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    postgresql-client \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder stage
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY . .

# Install the application
RUN pip install --no-cache-dir -e .

# Make sure scripts are in PATH
ENV PATH=/root/.local/bin:$PATH

# Cloud Run sets PORT environment variable
ENV PORT=8080

# Non-root user for security
RUN useradd -m -u 1000 mindscout && \
    chown -R mindscout:mindscout /app
USER mindscout

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:${PORT}/health', timeout=5)"

# Run database migrations and start server
CMD python -c "from mindscout.database import init_db; init_db()" && \
    exec uvicorn backend.main:app \
    --host 0.0.0.0 \
    --port ${PORT} \
    --workers 1 \
    --loop uvloop \
    --http httptools
