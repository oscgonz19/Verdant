# =============================================================================
# Verdant - Vegetation Change Intelligence Platform
# Multi-stage Dockerfile for reproducible builds
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Base image with system dependencies
# -----------------------------------------------------------------------------
FROM python:3.11-slim as base

# Prevent Python from writing pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies for geospatial libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libgdal-dev \
    libgeos-dev \
    libproj-dev \
    libspatialindex-dev \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# -----------------------------------------------------------------------------
# Stage 2: Builder - Install Python dependencies
# -----------------------------------------------------------------------------
FROM base as builder

WORKDIR /build

# Copy only dependency files first (better caching)
COPY pyproject.toml setup.py ./

# Create a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install dependencies
RUN pip install --upgrade pip setuptools wheel && \
    pip install -e ".[all]"

# -----------------------------------------------------------------------------
# Stage 3: Production image
# -----------------------------------------------------------------------------
FROM base as production

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash verdant
WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY --chown=verdant:verdant . .

# Install the package
RUN pip install -e .

# Create directories for data and credentials
RUN mkdir -p /app/data /app/output /app/credentials && \
    chown -R verdant:verdant /app

# Switch to non-root user
USER verdant

# Expose ports
EXPOSE 8000 8501

# Default command
CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

# -----------------------------------------------------------------------------
# Stage 4: Development image with testing tools
# -----------------------------------------------------------------------------
FROM production as development

USER root

# Install development tools
RUN pip install pytest pytest-cov pytest-asyncio httpx ipython jupyter

# Create test directories
RUN mkdir -p /app/htmlcov /app/test-results && \
    chown -R verdant:verdant /app

USER verdant

# Override command for development
CMD ["bash"]

# -----------------------------------------------------------------------------
# Stage 5: Testing image
# -----------------------------------------------------------------------------
FROM development as testing

# Run tests by default
CMD ["pytest", "tests/", "-v", "--cov=engine", "--cov=services", "--cov-report=html"]
