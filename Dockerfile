FROM node:20

# Install system dependencies and development tools
RUN apt-get update && apt-get install -y \
    # Version control and GitHub CLI
    git gh \
    # Shell and terminal tools
    zsh fzf \
    # Text processing and utilities
    jq vim curl wget \
    # System tools
    procps iptables \
    # Build essentials
    build-essential \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

# Install Claude CLI
RUN npm install -g @anthropic-ai/claude-code

# Copy scripts
COPY agent-entrypoint.sh init-firewall.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/agent-entrypoint.sh /usr/local/bin/init-firewall.sh \
 && chown -R node:node /usr/local/bin /usr/local/lib

USER node
WORKDIR /workspace

# Create directories for workspace and configurations
RUN mkdir -p /workspace/repo /home/node/.claude-agent /home/node/.cache

# Copy CLAUDE.md to agent directory to avoid conflicts with repo CLAUDE.md
COPY --chown=node:node CLAUDE.md /home/node/.claude-agent/CLAUDE.md

# Configure shell history persistence
RUN touch /home/node/.zsh_history && chown node:node /home/node/.zsh_history

ENTRYPOINT ["agent-entrypoint.sh"]

