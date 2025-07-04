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
COPY requirements.txt .
RUN uv pip install --system -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 agent && chown -R agent:agent /app

USER agent

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/health').raise_for_status()"

EXPOSE 8080

CMD ["python", "-m", "agent.main"]