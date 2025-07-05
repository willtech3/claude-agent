FROM python:3.12-slim

WORKDIR /app

# Install system dependencies, uv, and Node.js (for Claude Code CLI)
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && curl -LsSf https://astral.sh/uv/install.sh | sh \
    && npm install -g @anthropic/claude-code

# Add uv to PATH
ENV PATH="/root/.cargo/bin:${PATH}"

# Copy requirements first for better caching
COPY requirements.txt .
RUN uv pip install --system -r requirements.txt

# Copy application code
COPY . .

# Create workspaces and sessions directories
RUN mkdir -p /workspaces /sessions

# Create non-root user
RUN useradd -m -u 1000 agent && chown -R agent:agent /app /workspaces /sessions

USER agent

# Set default environment variables
ENV PYTHONUNBUFFERED=1

# Health check - check if the process is running
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD pgrep -f "python -m wrapper.main" || exit 1

CMD ["python", "-m", "wrapper.main"]