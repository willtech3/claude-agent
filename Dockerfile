FROM node:20

# tools + Claude CLI
RUN apt-get update && apt-get install -y gh git zsh fzf jq procps \
 && npm install -g @anthropic-ai/claude-code

COPY agent-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/agent-entrypoint.sh \
 && chown -R node:node /usr/local/bin /usr/local/lib

USER node
WORKDIR /workspace

# Create directories
RUN mkdir -p /workspace/repo /home/node/.claude-agent

# Copy CLAUDE.md to agent directory to avoid conflicts with repo CLAUDE.md
COPY --chown=node:node CLAUDE.md /home/node/.claude-agent/CLAUDE.md

ENTRYPOINT ["agent-entrypoint.sh"]

