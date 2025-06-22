#!/usr/bin/env bash
set -euo pipefail

# Initialize network security (optional, requires root)
if [ -f /usr/local/bin/init-firewall.sh ] && [ "$EUID" -eq 0 ]; then
    /usr/local/bin/init-firewall.sh || echo "Warning: Firewall initialization failed, continuing without network restrictions"
fi

# Clone the repository
REPO_URL="${REPO_URL:?Repository URL is required}"
PROMPT="${PROMPT:?Prompt is required}"
CLONE_DIR="/workspace/repo"

echo "Cloning repository: $REPO_URL"
git clone "$REPO_URL" "$CLONE_DIR"
cd "$CLONE_DIR"

# Configure git for commits
git config user.name "Claude Agent"
git config user.email "claude@example.com"

# Create branch name from prompt
# Extract issue number if present, otherwise create from prompt
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

# Point Claude to our agent instructions
export CLAUDE_INSTRUCTIONS_FILE="/home/node/.claude-agent/CLAUDE.md"

# Run Claude with the prompt
echo "$PROMPT" | claude -p \
  --output-format stream-json \
  --verbose \
  --dangerously-skip-permissions \
  ${MAX_TURNS:+--max-turns $MAX_TURNS} \
  --allowedTools \
    "Bash(git clone:*, git checkout:*, git add:*, git commit:*, git push:*, git config:*, git status:*, git diff:*, git log:*, git branch:*, git remote:*)" \
    "Bash(gh pr create:*, gh issue view:*, gh api:*)" \
    "Bash(npm:*, yarn:*, pnpm:*)" \
    "Bash(python:*, pip:*, pytest:*)" \
    "Bash(make:*, cmake:*)" \
    "Bash(cd:*, pwd:*, echo:*, cat:*, grep:*, find:*, ls:*)" \
    "Write" \
    "Read" \
    "Edit" \
    "MultiEdit" \
    "Grep" \
    "Glob" \
    "LS"