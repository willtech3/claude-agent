#!/usr/bin/env bash
set -euo pipefail

# Initialize network security (optional, requires root)
if [ -f /usr/local/bin/init-firewall.sh ] && [ "$EUID" -eq 0 ]; then
    /usr/local/bin/init-firewall.sh || echo "Warning: Firewall initialization failed, continuing without network restrictions"
fi

# Handle Claude authentication
if [ -f ~/.claude/.credentials.json ]; then
    # Credentials file exists (mounted from host)
    echo "Using Claude credentials from ~/.claude/.credentials.json"
elif [ -n "${ANTHROPIC_API_KEY:-}" ]; then
    # Using API key - Claude CLI will pick this up automatically
    echo "Using ANTHROPIC_API_KEY for authentication..."
else
    echo "Warning: No Claude authentication provided. Claude commands may fail."
fi

# Configure git authentication if GH_TOKEN is provided
if [ -n "${GH_TOKEN:-}" ]; then
    git config --global credential.helper store
    echo "https://x-access-token:${GH_TOKEN}@github.com" > ~/.git-credentials
    git config --global url."https://x-access-token:${GH_TOKEN}@github.com/".insteadOf "https://github.com/"
    
    # GitHub CLI will automatically use GH_TOKEN from environment
    # We don't need to run gh auth login when GH_TOKEN is set
    gh auth status >/dev/null 2>&1 || true
else
    echo "Warning: GH_TOKEN not set. GitHub CLI commands (gh) will not work."
    echo "This includes fetching GitHub issues with '/issue' commands."
    
    # If the prompt contains /issue or /pr, fail early
    if [[ "$PROMPT" =~ /(issue|pr|pull) ]]; then
        echo "Error: Cannot fetch GitHub issues/PRs without GH_TOKEN authentication."
        echo "Please set GH_TOKEN environment variable before running."
        exit 1
    fi
fi

# Clone the repository
REPO_URL="${REPO_URL:?Repository URL is required}"
PROMPT="${PROMPT:?Prompt is required}"
CLONE_DIR="/workspace/repo"

echo "Cloning repository: $REPO_URL"
git clone "$REPO_URL" "$CLONE_DIR" || {
    echo "Error: Failed to clone repository. If this is a private repository, ensure GH_TOKEN is set."
    exit 1
}
cd "$CLONE_DIR"

# Configure git for commits
git config user.name "Claude Agent"
git config user.email "claude@example.com"

# Detect operation mode from prompt
MODE="write"  # default
OUTPUT_DIR="${OUTPUT_DIR:-/workspace/artifacts}"

if [[ "$PROMPT" =~ --review ]] || [[ "$PROMPT" =~ /pr[[:space:]]+[0-9]+ ]] || [[ "$PROMPT" =~ /pull/[0-9]+ ]]; then
    MODE="review"
elif [[ "$PROMPT" =~ --ask ]]; then
    MODE="ask"
elif [[ "$PROMPT" =~ --analyze ]]; then
    MODE="analyze"
fi

echo "Running in ${MODE^^} mode"

# Create artifacts directory structure
mkdir -p "$OUTPUT_DIR"/{reviews,analysis,qa}

# Create branch name based on mode and prompt
if [[ "$MODE" == "write" ]]; then
    # For write mode, create a feature branch
    if [[ "$PROMPT" =~ /issue[[:space:]]+([0-9]+) ]]; then
        BRANCH_NAME="claude/issue-${BASH_REMATCH[1]}"
    else
        # Create branch name from first few words of prompt
        # Remove special characters and convert to lowercase
        BRANCH_WORDS=$(echo "$PROMPT" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9 ]//g' | awk '{print $1"-"$2"-"$3}' | sed 's/-*$//')
        BRANCH_NAME="claude/${BRANCH_WORDS:-task}"
    fi
    git checkout -b "$BRANCH_NAME"
    echo "Working on branch: $BRANCH_NAME"
else
    # For read-only modes, stay on default branch
    echo "Staying on default branch for read-only operation"
fi

# Point Claude to mode-specific agent instructions
export CLAUDE_INSTRUCTIONS_FILE="/home/node/.claude-agent/CLAUDE-${MODE^^}.md"

# Prepare mode-specific prompt enforcement
if [[ "$MODE" == "write" ]]; then
    ENFORCED_PROMPT="[SYSTEM: You MUST commit all changes and create a PR before finishing. Include these as todos: git add, git commit, git push, gh pr create. This is MANDATORY.]

$PROMPT"
else
    ENFORCED_PROMPT="[SYSTEM: This is ${MODE^^} mode - a READ-ONLY operation. Do NOT make any code changes. Save all outputs to $OUTPUT_DIR/${MODE}s/. The artifacts directory is mounted and will persist after the container exits.]

$PROMPT"
fi

# Run Claude with the enforced prompt
echo "$ENFORCED_PROMPT" | claude -p \
  --output-format stream-json \
  --verbose \
  --dangerously-skip-permissions \
  ${MAX_TURNS:+--max-turns $MAX_TURNS} \
  --allowedTools \
    "Bash(git clone:*, git checkout:*, git add:*, git commit:*, git push:*, git config:*, git status:*, git diff:*, git log:*, git branch:*, git remote:*)" \
    "Bash(gh pr create:*, gh pr view:*, gh pr diff:*, gh pr comment:*, gh pr review:*, gh issue view:*, gh api:*)" \
    "Bash(npm:*, yarn:*, pnpm:*)" \
    "Bash(python:*, pip:*, pytest:*)" \
    "Bash(make:*, cmake:*)" \
    "Bash(cd:*, pwd:*, echo:*, cat:*, grep:*, find:*, ls:*, tree:*, wc:*, sort:*, uniq:*, head:*, tail:*, awk:*, sed:*, date:*, mkdir:*)" \
    "Write" \
    "Read" \
    "Edit" \
    "MultiEdit" \
    "Grep" \
    "Glob" \
    "LS" \
  --disallowedTools \
    "Bash(curl:*, wget:*, nc:*, netcat:*)" \
    "Bash(ssh:*, scp:*, rsync:*)" \
    "Bash(sudo:*, su:*, chmod:*, chown:*)" \
    "Bash(rm -rf:*, dd:*, format:*)" \
    "Bash(cron:*, crontab:*, at:*)" \
    "Bash(systemctl:*, service:*)" \
    "Bash(gpg --gen-key:*, openssl genrsa:*, openssl req -new:*)" \
    "Bash(iptables:*, firewall-cmd:*)" \
    "Bash(eval:*, exec:*)" \
    "Bash(node -e:*, python -c:*, bash -c:*)" \
    "Bash(export PATH=:*, export LD_LIBRARY_PATH=:*)"