# Claude Agent

A headless, containerized Claude Code agent for automated GitHub workflows including code implementation, PR reviews, Q&A sessions, and code analysis.

## Features

- **Multi-Mode Operation**: Four distinct modes for different use cases
  - Write mode (default): Makes code changes and creates PRs
  - Review mode: Analyzes pull requests without making changes
  - Ask mode: Answers questions about codebases
  - Analyze mode: Performs security and quality analysis
- **Containerized Execution**: All operations run in isolated Docker containers
- **GitHub Integration**: Full support for issues, PRs, and GitHub CLI
- **Artifact Persistence**: Analysis outputs saved locally for review and CI/CD
- **Smart Branch Management**: Automatic branch creation for write operations
- **Multiple Output Formats**: Interactive, JSON, and background modes

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

### Modes

- **Write Mode (default)**: Makes code changes and creates pull requests
- **Review Mode (`--review`)**: Analyzes PRs without making changes
- **Ask Mode (`--ask`)**: Answers questions about the codebase
- **Analyze Mode (`--analyze`)**: Performs security/quality analysis

### Options

- `--review` - Enable PR review mode (read-only)
- `--ask` - Enable Q&A mode (read-only)
- `--analyze` - Enable analysis mode (read-only)
- `--output-dir <path>` - Directory for artifacts (default: `./claude-artifacts`)
- `--json` - Output in JSON format (great for CI/CD pipelines)
- `--bg` - Run in background mode with logging
- `--max-turns N` - Limit Claude to N iterations (default: unlimited)
- `--help` - Show help message

### Write Mode Examples (Default)

```bash
# Work on GitHub issues
claude-agent https://github.com/owner/repo "/issue 123"
claude-agent https://github.com/owner/repo "/issue 123 and add comprehensive tests"

# Custom implementation tasks
claude-agent https://github.com/owner/repo "Add dark mode support"
claude-agent https://github.com/owner/repo "Refactor authentication to use JWT"
```

### Review Mode Examples

```bash
# Review a pull request
claude-agent https://github.com/owner/repo "/pr 456 --review"

# Review with focus area
claude-agent https://github.com/owner/repo "/pr 456 focus on security --review"

# Review multiple PRs
claude-agent https://github.com/owner/repo "/pr 123,456,789 --review"
```

### Ask Mode Examples

```bash
# Ask about implementation
claude-agent https://github.com/owner/repo "How does the authentication work? --ask"

# Architecture questions
claude-agent https://github.com/owner/repo "Explain the database design --ask"

# Debugging help
claude-agent https://github.com/owner/repo "Why am I getting token expired errors? --ask"
```

### Analyze Mode Examples

```bash
# Security audit
claude-agent https://github.com/owner/repo "Security audit --analyze"

# Performance analysis
claude-agent https://github.com/owner/repo "Find performance bottlenecks --analyze"

# Code quality review
claude-agent https://github.com/owner/repo "Check for code smells and technical debt --analyze"

# Dependency analysis
claude-agent https://github.com/owner/repo "Check for vulnerable dependencies --analyze"
```

### Output Formats

```bash
# JSON output (great for scripting)
claude-agent https://github.com/owner/repo "/issue 123" --json

# Background mode with logging
claude-agent https://github.com/owner/repo "Add API documentation" --bg

# Custom artifact directory
claude-agent https://github.com/owner/repo "/pr 456 --review" --output-dir ./pr-reviews
```

### Output Artifacts

Read-only modes (review, ask, analyze) save artifacts to the output directory:

```
claude-artifacts/
├── reviews/
│   └── pr-123-review-20240623-143022.md      # PR review reports
├── analysis/
│   ├── security-audit-20240623-143022.md     # Analysis reports
│   └── security-audit-20240623-143022.sarif  # SARIF for GitHub Security
└── qa/
    └── session-20240623-143022.md            # Q&A transcripts
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

### Write Mode (Default)
1. Clones the repository into a container
2. Creates a branch based on the task:
   - For issues: `claude/issue-123`
   - For custom tasks: `claude/add-dark-mode` (from prompt)
3. Runs Claude with your prompt
4. Claude makes changes, commits, and creates a pull request
5. No local files are ever modified

### Read-Only Modes (Review, Ask, Analyze)
1. Clones the repository into a container
2. Stays on the default branch (no changes)
3. Analyzes code according to the mode
4. Saves output artifacts to the specified directory
5. Artifacts persist after container exits

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
- Claude authentication (one of):
  - Claude MAX subscription: Run `claude login` on your host machine
  - API Key: Set `ANTHROPIC_API_KEY` environment variable

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

## CI/CD Integration

### GitHub Actions - PR Review

```yaml
name: PR Review
on:
  pull_request:
    types: [opened, synchronize]

jobs:
  claude-review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Claude PR Review
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          docker run --rm \
            -e GH_TOKEN \
            -e ANTHROPIC_API_KEY \
            -e REPO_URL="${{ github.event.repository.clone_url }}" \
            -e PROMPT="/pr ${{ github.event.pull_request.number }} --review" \
            -v $PWD/artifacts:/workspace/artifacts \
            claude-code-agent
      
      - name: Upload Review Artifacts
        uses: actions/upload-artifact@v3
        with:
          name: pr-review
          path: artifacts/reviews/
```

### Security Scanning

```yaml
- name: Security Analysis
  run: |
    docker run --rm \
      -e GH_TOKEN \
      -e ANTHROPIC_API_KEY \
      -e REPO_URL="${{ github.event.repository.clone_url }}" \
      -e PROMPT="Security audit --analyze" \
      -v $PWD/security-report:/workspace/artifacts \
      claude-code-agent

- name: Upload SARIF
  uses: github/codeql-action/upload-sarif@v2
  with:
    sarif_file: ./security-report/analysis/
```

## Differences from Standard Claude Code

1. **Multi-Mode Operation**: Supports write, review, ask, and analyze modes
2. **Automated PR Workflow**: Specifically designed for GitHub automation
3. **Repository Isolation**: Each task runs in its own cloned repository
4. **Artifact Generation**: Produces persistent outputs for CI/CD integration
5. **Restricted Tools**: More limited tool access for security
6. **No Interactive Mode**: Runs as single-turn automation
