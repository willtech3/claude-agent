# 7. Agent Wrapper Approach

Date: 2025-01-04

## Status

Accepted (Temporary - see SDK Migration Plan)

## Context

We need to implement an AI agent that can:
- Analyze code repositories
- Create pull requests
- Review code changes
- Answer questions about codebases

Options considered:
1. Build custom agent from scratch
2. Use Claude API directly with custom tooling
3. Wrap existing Claude Code CLI tool
4. Wait for official SDK

Time constraint: Need working POC quickly for validation

## Decision

Use a Python wrapper around the Claude Code CLI for initial implementation:

### Architecture
```python
# Wrapper provides:
- Session management
- Output parsing
- Error handling
- SQS integration
- Artifact management
```

### Implementation
1. Run Claude Code CLI in subprocess
2. Parse streamed output for events
3. Manage file system isolation
4. Handle authentication forwarding
5. Convert CLI output to API responses

This is explicitly a temporary solution with planned migration to official SDK.

## Consequences

**Positive:**
- Rapid implementation (days vs months)
- Leverages battle-tested Claude Code
- Full feature set immediately available
- Learning opportunity for requirements
- Can validate product-market fit quickly

**Negative:**
- Performance overhead from subprocess
- Complex output parsing required
- Limited control over agent behavior
- Potential brittleness from CLI changes
- Technical debt to migrate later
- Resource intensive (full process per task)