# 5. Provider Abstraction Pattern

Date: 2025-01-04

## Status

Accepted

## Context

The Claude Agent needs to integrate with multiple:
- Git providers (GitHub, GitLab, Bitbucket)
- AI providers (Anthropic, AWS Bedrock, Google Vertex AI)
- Cloud services (AWS, potentially others)

Each provider has different:
- Authentication mechanisms
- API interfaces
- Rate limits
- Feature sets
- Error handling

We need a design that allows easy addition of new providers without modifying core business logic.

## Decision

Implement a provider abstraction pattern using:

### Interface Definition
```python
# Base interfaces
class GitProvider(Protocol):
    async def get_repository(self, repo_id: str) -> Repository
    async def create_pull_request(self, ...) -> PullRequest
    async def get_issue(self, issue_id: str) -> Issue

class AIProvider(Protocol):
    async def complete(self, prompt: str) -> Response
    async def stream_complete(self, prompt: str) -> AsyncIterator[str]
```

### Factory Pattern
```python
def get_git_provider(config: ProviderConfig) -> GitProvider:
    match config.type:
        case "github": return GitHubProvider(config)
        case "gitlab": return GitLabProvider(config)
        case "bitbucket": return BitbucketProvider(config)
```

### Configuration
```yaml
providers:
  git:
    type: github
    api_token: ${GITHUB_TOKEN}
  ai:
    type: bedrock
    region: us-east-1
    model: claude-3-sonnet
```

### Error Handling
- Provider-specific exceptions mapped to common types
- Retry logic with provider-specific backoff
- Graceful degradation when possible

## Consequences

**Positive:**
- Easy to add new providers
- Consistent interface for business logic
- Provider-specific optimizations possible
- Testable with mock providers
- Configuration-driven provider selection
- Supports multiple providers simultaneously

**Negative:**
- Additional abstraction layer complexity
- Potential for leaky abstractions
- Need to handle lowest common denominator
- More code to maintain
- Risk of over-engineering
- Performance overhead from abstraction