# Customer Success FTE — Multi-Stage Dockerfile
# Phase 2: Specialization

# ─── Stage 1: Build Dependencies ──────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY production/requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ─── Stage 2: Production Image ────────────────────────────────────────────
FROM python:3.12-slim AS production

# Labels
LABEL org.opencontainers.image.title="Customer Success FTE"
LABEL org.opencontainers.image.description="24/7 AI-powered customer support across Email, WhatsApp, and Web"
LABEL org.opencontainers.image.version="2.0.0"

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r fte && useradd -r -g fte -d /home/fte -s /sbin/nologin fte
RUN mkdir -p /home/fte && chown -R fte:fte /home/fte

# Copy Python packages from builder
COPY --from=builder /install /usr/local

# Set working directory
WORKDIR /app

# Copy application code
COPY production/ ./production/
COPY incubation/ ./incubation/
COPY context/ ./context/

# Set permissions
RUN chown -R fte:fte /app

# Switch to non-root user
USER fte

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Default command (API server)
CMD ["uvicorn", "production.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
