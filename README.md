# Claude Agent

A headless, non-interactive containerized Claude Code agent for automated GitHub workflows including code implementation, PR reviews, Q&A sessions, and code analysis. This agent runs completely autonomously without user interaction.

## ⚠️ Security Warning

**IMPORTANT: This agent should only be run with trusted code.** The Claude Agent executes code and makes changes to repositories. Running it on untrusted or malicious code could result in:

- Execution of harmful code during analysis
- Unintended modifications to your codebase
- Exposure of sensitive information
- Potential security vulnerabilities

Always review the repository and ensure you trust the codebase before running the agent.

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
- **Multiple Output Formats**: Standard, JSON, and background modes

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

The Claude Agent is designed to help with various software development tasks while maintaining isolation. The command takes a repository URL and a prompt:

```bash
claude-agent <repo-url> "<prompt>" [options]
```

### Basic Syntax

```bash
# General format
claude-agent <repository-url> "<task-description>" [--mode-flag] [--options]

# GitHub issue format
claude-agent <repository-url> "/issue <number>" [--options]

# Pull request review format
claude-agent <repository-url> "/pr <number>" --review [--options]
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

### Retrieving Non-GitHub Artifacts

Since the agent runs non-interactively in a container, artifacts are persisted through Docker volume mounts. Here's how to retrieve them:

**1. Using Volume Mounts (Recommended)**
```bash
# The artifacts are saved to your local filesystem via volume mount
claude-agent https://github.com/owner/repo "Security audit --analyze" --output-dir ./my-artifacts

# Artifacts will be available at ./my-artifacts/analysis/
ls ./my-artifacts/analysis/
```

**2. Direct Docker Volume Access**
```bash
# If using default output directory
docker run -v $(pwd)/claude-artifacts:/workspace/artifacts ...

# Files are directly accessible on your host
cat ./claude-artifacts/analysis/security-audit-*.md
```

**3. CI/CD Artifact Collection**
```yaml
# GitHub Actions example
- name: Run Analysis
  run: |
    claude-agent $REPO_URL "Code quality analysis --analyze" \
      --output-dir ./analysis-results

- name: Upload Artifacts
  uses: actions/upload-artifact@v3
  with:
    name: analysis-results
    path: ./analysis-results/
```

**4. Programmatic Access (JSON Mode)**
```bash
# Use JSON output for programmatic processing
claude-agent https://github.com/owner/repo "List all API endpoints --ask" --json > api-endpoints.json

# Parse the JSON output
jq '.artifacts' api-endpoints.json
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
- Claude will follow repository conventions automatically if CLAUDE.md is present in the repo

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
  - Claude subscription: Run `claude login` on your host machine
  - API Key: Set `ANTHROPIC_API_KEY` environment variable

## Security Considerations

This tool implements several security measures:

1. **Containerized Execution**: All operations run inside Docker containers
2. **Ephemeral Environments**: Each run starts fresh (except command history)
3. **No Host File Access**: Claude cannot access your local filesystem outside the container
4. **Non-root Execution**: Runs as `node` user, not root
5. **Turn Limits**: Use `--max-turns` to limit iterations for simpler tasks or safety

### Attack Vectors to Consider

**Poisoned Dependencies**: Malicious packages in package managers (npm, pip, etc.) could:
- Execute harmful code during installation
- Exfiltrate sensitive data
- Compromise the build process

**Supply Chain Attacks**: Compromised upstream dependencies or tools

**Code Injection**: Malicious code patterns designed to exploit the agent

**Resource Exhaustion**: Infinite loops or excessive resource consumption

**Artifact-Related Attack Vectors**:
- **Path Traversal**: Malicious code could attempt to write artifacts outside the designated directory
- **Symlink Attacks**: Creation of symbolic links pointing to sensitive host files
- **Volume Mount Exploitation**: If misconfigured, volume mounts could expose host filesystem
- **File Permission Escalation**: Artifacts created with overly permissive modes
- **Content Injection**: Malicious content in artifacts (e.g., XSS in HTML reports)

**Mitigation Strategies**:
- Always use absolute paths for `--output-dir`
- Validate artifact contents before processing
- Run with minimal Docker privileges
- Regularly clean up old artifacts
- Scan artifacts for malicious content before sharing

### Security Implementation

The Claude Agent implements security through containerization:

**Container Isolation**:
- All operations run inside Docker containers
- Each task gets a fresh environment
- No access to host filesystem
- Runs as non-root user (`node`)
- Limited to repository directory for file operations

**Important Note**: The agent runs with `--dangerously-skip-permissions` flag to enable full functionality. This is required for the agent to perform its intended tasks like creating files, running commands, and making commits. Ensure you only run this on trusted repositories.


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
      
      - name: Checkout Claude Agent
        uses: actions/checkout@v3
        with:
          repository: willtech3/claude-agent
          path: claude-agent
      
      - name: Build Claude Agent Docker Image
        run: |
          cd claude-agent
          docker build -t claude-code-agent .
      
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
- name: Checkout Claude Agent
  uses: actions/checkout@v3
  with:
    repository: willtech3/claude-agent
    path: claude-agent

- name: Build Claude Agent
  run: |
    cd claude-agent
    docker build -t claude-code-agent .

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

## Adding Dependencies for Your Tech Stack

The Claude Agent comes with common development tools pre-installed. However, you may need to add specific dependencies for your technology stack:

### Creating a Custom Dockerfile

```dockerfile
# Extend the base Claude Agent image
FROM claude-code-agent:latest

# Example: Add Python data science libraries
RUN pip install pandas numpy scikit-learn jupyter

# Example: Add specific Node.js tools
RUN npm install -g typescript eslint prettier

# Example: Add database clients
RUN apt-get update && apt-get install -y \
    postgresql-client \
    mysql-client \
    redis-tools

# Example: Add language-specific tools
RUN apt-get install -y \
    golang \
    rustc \
    ruby
```

### Common Tech Stack Additions

**Frontend Development**:
```bash
# React/Vue/Angular tooling
RUN npm install -g @angular/cli @vue/cli create-react-app
```

**Backend Development**:
```bash
# API development tools
RUN pip install fastapi django flask
RUN npm install -g express-generator nest
```

**DevOps Tools**:
```bash
# Infrastructure as Code
RUN apt-get install -y terraform ansible kubectl helm
```

**Data Science**:
```bash
# ML/AI libraries
RUN pip install tensorflow pytorch transformers
```

### Best Practices for Dependencies

1. **Verify Sources**: Only install from official package repositories
2. **Pin Versions**: Use specific versions to ensure reproducibility
3. **Minimal Installation**: Only add what's necessary for your use case
4. **Security Scanning**: Run vulnerability scans on added dependencies
5. **Documentation**: Document why each dependency is needed

## Differences from Standard Claude Code

1. **Multi-Mode Operation**: Supports write, review, ask, and analyze modes
2. **Automated PR Workflow**: Specifically designed for GitHub automation
3. **Repository Isolation**: Each task runs in its own cloned repository
4. **Artifact Generation**: Produces persistent outputs for CI/CD integration
5. **Restricted Tools**: More limited tool access for security
6. **No Interactive Mode**: Runs completely autonomously without user interaction
7. **Artifact-Based Output**: All non-GitHub outputs are saved as files via volume mounts
8. **Single-Turn Execution**: Completes the entire task in one run without user intervention
