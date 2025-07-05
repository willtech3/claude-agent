FROM node:20-slim AS claude-installer

# Install Claude Code CLI
RUN npm install -g @anthropic-ai/claude-code

FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    # Required for git operations
    git \
    # Required for Claude Code
    nodejs npm \
    # GitHub CLI for PR operations
    gh \
    # Required for file operations
    ripgrep \
    # General utilities
    curl jq \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy Claude Code from the installer stage
COPY --from=claude-installer /usr/local/lib/node_modules/@anthropic-ai/claude-code /usr/local/lib/node_modules/@anthropic-ai/claude-code
COPY --from=claude-installer /usr/local/bin/claude /usr/local/bin/claude

# Install uv for Python package management
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:${PATH}"

# Copy requirements first for better caching
COPY requirements.txt .
RUN uv pip install --system -r requirements.txt

# Copy application code
COPY . .

# Create directories for wrapper workspaces and sessions
RUN mkdir -p /workspaces /sessions /tmp/claude-sessions /tmp/claude-artifacts

# Create non-root user
RUN useradd -m -u 1000 agent && \
    chown -R agent:agent /app /workspaces /sessions /tmp/claude-sessions /tmp/claude-artifacts && \
    # Allow agent user to run git commands
    git config --global --add safe.directory '*'

USER agent

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV NODE_ENV=production

# Health check - check if the wrapper process is running
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD pgrep -f "python -m wrapper.main" || exit 1

CMD ["python", "-m", "wrapper.main"]