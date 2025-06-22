# Claude Agent

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
# Navigate to where you cloned this repository
cd /path/to/claude-agent

# Build the Docker image
docker build -t claude-code-agent .
```

### 2. Set up the Command

Add the script to your PATH by creating a symbolic link:

```bash
# Create a symlink in a directory that's in your PATH
# Common options include ~/.local/bin, ~/bin, or /usr/local/bin
ln -s /path/to/claude-agent/claude-agent ~/.local/bin/claude-agent

# Make sure the target directory exists first:
mkdir -p ~/.local/bin
```

Alternatively, add the claude-agent directory to your PATH:

```bash
# Add to ~/.bashrc or ~/.zshrc
export PATH="/path/to/claude-agent:$PATH"
```

### 3. Ensure GitHub Token is Set

```bash
export GH_TOKEN=your_github_token_here
```

## Usage

The command takes a repository URL and a prompt:

```bash
claude-agent <repo-url> "<prompt>" [options]
```

### Options

- `--json` - Output in JSON format (great for CI/CD pipelines)
- `--bg` - Run in background mode with logging
- `--max-turns N` - Limit Claude to N iterations (default: unlimited)
- `--help` - Show help message

### Work on GitHub Issues

```bash
# Simple issue reference
claude-agent https://github.com/owner/repo "/issue 123"

# Issue with additional instructions
claude-agent https://github.com/owner/repo "/issue 123 and add comprehensive tests"

# Issue with specific requirements
claude-agent https://github.com/owner/repo "/issue 456 but use TypeScript"
```

### Custom Tasks

```bash
# Add a new feature
claude-agent https://github.com/owner/repo "Add dark mode support"

# Refactor code
claude-agent https://github.com/owner/repo "Refactor authentication to use JWT"

# Fix a bug
claude-agent https://github.com/owner/repo "Fix memory leak in image processing"
```

### Output Formats

```bash
# JSON output (great for scripting)
claude-agent https://github.com/owner/repo "/issue 123" --json

# Background mode with logging
claude-agent https://github.com/owner/repo "Add API documentation" --bg
```

### Controlling Agent Iterations

```bash
# Unlimited turns (default) - Claude decides when the task is complete
claude-agent https://github.com/owner/repo "Refactor authentication system"

# Limit to 5 turns for simple tasks
claude-agent https://github.com/owner/repo "Fix typo in README" --max-turns 5

# More turns for complex tasks
claude-agent https://github.com/owner/repo "/issue 789" --max-turns 20
```

### View Help

```bash
claude-agent --help
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

### When to Use --max-turns

**Leave unlimited (default)** for:
- Complex features or refactoring
- Tasks where scope is unclear
- When you want Claude to fully complete the task

**Set a limit** for:
- Simple, well-defined tasks (5-10 turns)
- When you want to review progress incrementally
- Testing or experimentation
- Resource-constrained environments

## Requirements

- Docker
- GitHub personal access token (with repo permissions)
- Claude API access (via `~/.claude` directory)

## Security Considerations

This tool implements several security measures:

1. **Containerized Execution**: All operations run inside Docker containers
2. **Tool Restrictions**: Claude is limited to specific git and GitHub operations
   - By default, Claude runs with unlimited turns (stops when task is complete)
   - Use `--max-turns` to limit iterations for simpler tasks or safety
3. **Network Security**: Optional firewall configuration (requires privileged mode)
4. **No Local File Access**: Claude cannot access your local filesystem
5. **Ephemeral Environments**: Each run starts fresh (except command history)

### Network Security (Optional)

To enable network restrictions, run the container with `--cap-add=NET_ADMIN`:

```bash
# Modify the claude-agent script to add this flag to docker run commands
```

This implements a default-deny firewall policy, only allowing connections to:
- GitHub domains
- Anthropic API endpoints
- NPM registry
- Essential services

## Differences from Standard Claude Code

1. **Automated PR Workflow**: Specifically designed for GitHub PR automation
2. **Repository Isolation**: Each task runs in its own cloned repository
3. **Restricted Tools**: More limited tool access compared to interactive Claude Code
4. **No Interactive Mode**: Runs as a single-turn automation
