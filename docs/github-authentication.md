# GitHub Authentication for Claude Agent

## Overview

The Claude Agent requires GitHub CLI (`gh`) authentication to interact with GitHub repositories. This document explains how to set up authentication properly.

## For Public Repositories

Even though public repositories can be read without authentication, the GitHub CLI still requires authentication to function properly. Here's how to set up minimal access:

### Option 1: Create a Fine-Grained Personal Access Token (Recommended)

1. Go to GitHub Settings > Developer settings > Personal access tokens > Fine-grained tokens
2. Click "Generate new token"
3. Give it a name like "claude-agent-public"
4. Set expiration as needed
5. Under "Repository access", select "Public Repositories (read-only)"
6. No additional permissions are needed for reading public repos
7. Click "Generate token" and copy the token

### Option 2: Use a Classic Token with Minimal Permissions

1. Go to GitHub Settings > Developer settings > Personal access tokens > Tokens (classic)
2. Click "Generate new token"
3. Give it a note like "claude-agent-public"
4. Select NO scopes (for public repo read access only)
5. Click "Generate token"

### Set the Token

```bash
export GH_TOKEN=your_token_here
```

## For Private Repositories

For private repositories or to create PRs, you'll need additional permissions:

### Required Scopes for Full Functionality:
- `repo` - Full control of private repositories
- `workflow` - Update GitHub Action workflows (if needed)
- `write:org` - Read org and team membership (if working with org repos)

## Troubleshooting

### "Invalid API key" Error
This usually means:
1. GH_TOKEN is not set
2. The token has expired
3. The token lacks necessary permissions

### Checking Authentication Status
The agent should run this at startup:
```bash
gh auth status
```

### Token Best Practices
1. Use fine-grained tokens when possible
2. Set minimal permissions needed
3. Rotate tokens regularly
4. Never commit tokens to repositories

## Container Environment

When running the Claude Agent in Docker, ensure the token is passed:

```bash
docker run -e GH_TOKEN=$GH_TOKEN ... claude-code-agent ...
```

The `claude-agent` script handles this automatically when GH_TOKEN is set in your environment.