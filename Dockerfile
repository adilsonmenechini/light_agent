FROM python:3.12-slim

WORKDIR /app

# Install uv
RUN pip install --no-cache-dir uv

# Copy only dependency files first for better caching
COPY pyproject.toml requirements.txt* ./

# Install dependencies
RUN uv pip install --system -r requirements.txt

# Copy application code
COPY light_agent/ ./light_agent/
COPY workspace/ ./workspace/
COPY README.md ./

# Create data directory for memory
RUN mkdir -p data/memory

ENV PYTHONUNBUFFERED=1
ENV RESTRICT_TO_WORKSPACE=true

ENTRYPOINT ["python", "-m", "light_agent.cli.application", "chat"]
