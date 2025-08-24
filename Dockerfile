# Production Dockerfile for Taara Internet Monitor
# Multi-stage build for optimal VPS deployment
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libc6-dev \
    libssl-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Create and activate virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim

# Build argument for user ID (defaults to 1000)
ARG USER_ID=1000
ARG GROUP_ID=1000

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user with proper permissions
RUN groupadd -r taara -g ${GROUP_ID} && useradd -r -g taara -u ${USER_ID} taara

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy application code with proper ownership
COPY --chown=taara:taara app/ ./app/
COPY --chown=taara:taara templates/ ./templates/
COPY --chown=taara:taara static/ ./static/
COPY --chown=taara:taara scheduler.py .
COPY --chown=taara:taara init_db.py .

# Create required directories with proper permissions
RUN mkdir -p /app/data /app/logs /app/backups && \
    chown -R taara:taara /app && \
    chmod 755 /app/data /app/logs /app/backups

# Switch to non-root user
USER taara

# Expose port
EXPOSE 8000

# Production health check with better reliability
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/data || exit 1

# Set production environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app

# Use gunicorn for production WSGI server
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "--worker-class", "uvicorn.workers.UvicornWorker", "--access-logfile", "-", "--error-logfile", "-", "--log-level", "info", "app.main:app"]
