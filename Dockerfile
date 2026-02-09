# Build stage
FROM python:3.12-slim AS builder

WORKDIR /app

# Install uv
RUN pip install --no-cache-dir uv

# Copy only dependency files first for better caching
COPY pyproject.toml requirements.txt* ./

# Install dependencies
RUN uv pip install --system -r requirements.txt

# Copy application code
COPY lightagent/ ./lightagent/
COPY workspace/ ./workspace/
COPY README.md ./

# Create data directory for memory
RUN mkdir -p data/memory

# Production stage - smaller image
FROM python:3.12-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application
COPY --from=builder /app /app

ENV PYTHONUNBUFFERED=1
ENV RESTRICT_TO_WORKSPACE=true

ENTRYPOINT ["python", "-m", "lightagent.cli.application", "chat"]
