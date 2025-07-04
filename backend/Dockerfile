FROM python:3.12-slim

WORKDIR /app

# Install system dependencies and uv
RUN apt-get update && apt-get install -y \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && curl -LsSf https://astral.sh/uv/install.sh | sh

# Add uv to PATH
ENV PATH="/root/.cargo/bin:${PATH}"

# Copy requirements first for better caching
COPY pyproject.toml .
COPY README.md .

# Install Python dependencies using uv (including dev dependencies for local development)
RUN uv pip install --system -e ".[dev]"

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 api && chown -R api:api /app

USER api

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]