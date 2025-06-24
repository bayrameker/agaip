# =============================================================================
# AGAIP FRAMEWORK - MULTI-STAGE DOCKERFILE
# =============================================================================

# =============================================================================
# BASE STAGE - Common dependencies and setup
# =============================================================================
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    POETRY_VERSION=1.7.1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry==$POETRY_VERSION

# Create app user
RUN groupadd -r agaip && useradd -r -g agaip agaip

# Set work directory
WORKDIR /app

# Copy poetry files
COPY pyproject.toml poetry.lock ./

# Configure poetry
RUN poetry config virtualenvs.create false

# =============================================================================
# DEVELOPMENT STAGE - For local development
# =============================================================================
FROM base as development

# Install all dependencies (including dev dependencies)
RUN poetry install --no-root

# Copy application code
COPY . .

# Change ownership to app user
RUN chown -R agaip:agaip /app

# Switch to app user
USER agaip

# Create necessary directories
RUN mkdir -p /app/logs /app/data /app/plugins

# Expose ports
EXPOSE 8000 9090

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command
CMD ["uvicorn", "agaip.api.app:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# =============================================================================
# PRODUCTION STAGE - Optimized for production
# =============================================================================
FROM base as production

# Install only production dependencies
RUN poetry install --only=main --no-root

# Copy application code
COPY . .

# Remove unnecessary files
RUN rm -rf tests/ docs/ examples/ .git/ .github/ \
    && find . -type f -name "*.pyc" -delete \
    && find . -type d -name "__pycache__" -delete

# Change ownership to app user
RUN chown -R agaip:agaip /app

# Switch to app user
USER agaip

# Create necessary directories
RUN mkdir -p /app/logs /app/data

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Production command
CMD ["uvicorn", "agaip.api.app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

# =============================================================================
# TESTING STAGE - For running tests
# =============================================================================
FROM development as testing

# Install test dependencies
RUN poetry install --with=test

# Run tests
CMD ["pytest", "-v", "--cov=agaip", "--cov-report=html", "--cov-report=term"]
