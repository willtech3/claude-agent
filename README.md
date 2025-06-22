# Claude PR Agent

A Docker-based setup for running Claude Code on GitHub repositories with a simple, unified interface.

## Features

- Single prompt interface for all workflows
- Automatic repository cloning inside container
- Smart branch naming based on task
- Git configuration and PR creation built-in
- No local file modifications
- Multiple output formats (interactive, JSON, background)

## Quick Start

### 1. Build the Docker Image

```bash
docker build -t claude-code-agent /Users/williamlane/claude-agent/
```

### 2. Set up the Command

Add the script to your PATH:

```bash
ln -s /Users/williamlane/claude-agent/claude-pr ~/bin/claude-pr
```

Or add to your `.zshrc`:

```bash
export PATH="/Users/williamlane/claude-agent:$PATH"
```

### 3. Ensure GitHub Token is Set

```bash
export GH_TOKEN=your_github_token_here
```

## Usage

The command takes a repository URL and a prompt:

```bash
claude-pr <repo-url> "<prompt>" [options]
```

### Work on GitHub Issues

```bash
# Simple issue reference
claude-pr https://github.com/owner/repo "/issue 123"

# Issue with additional instructions
claude-pr https://github.com/owner/repo "/issue 123 and add comprehensive tests"

# Issue with specific requirements
claude-pr https://github.com/owner/repo "/issue 456 but use TypeScript"
```

### Custom Tasks

```bash
# Add a new feature
claude-pr https://github.com/owner/repo "Add dark mode support"

# Refactor code
claude-pr https://github.com/owner/repo "Refactor authentication to use JWT"

# Fix a bug
claude-pr https://github.com/owner/repo "Fix memory leak in image processing"
```

### Output Formats

```bash
# JSON output (great for scripting)
claude-pr https://github.com/owner/repo "/issue 123" --json

# Background mode with logging
claude-pr https://github.com/owner/repo "Add API documentation" --bg
```

### View Help

```bash
claude-pr --help
```

## How It Works

1. Clones the repository into a container
2. Creates a branch based on the task:
   - For issues: `claude/issue-123`
   - For custom tasks: `claude/add-dark-mode` (from prompt)
3. Runs Claude with your prompt
4. Claude makes changes, commits, and creates a pull request
5. No local files are ever modified

## Prompt Tips

- For issues, use `/issue NUMBER` format
- Be specific about requirements
- Can combine issue references with additional instructions
- Claude will follow repository conventions automatically

## Requirements

- Docker
- GitHub personal access token (with repo permissions)
- Claude API access (via `~/.claude` directory)