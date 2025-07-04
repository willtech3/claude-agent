# CLAUDE.md - Backend Code Quality Guidelines

## Inheritance
- **Extends:** /CLAUDE.md (root)
- **Overrides:** None (CRITICAL RULES cannot be overridden)
- **Scope:** All Python code in backend/ and agent/ directories

## Rules

**Context:** Load this document when implementing backend features, reviewing Python code, or making architectural decisions for Lambda functions and Agent workers.

---

# Backend Code Quality Guidelines for Claude Agent

This document outlines practical code quality standards for our serverless backend and containerized agent. We prioritize clarity, testability, and cloud-native patterns over theoretical purity.

## Core Philosophy

> "Make it work, make it right, make it fast" - in that order

1. **Cloud-Native First** - Design for Lambda constraints and ECS scalability
2. **Provider Abstraction** - Never hardcode GitHub/GitLab specifics
3. **Explicit over Implicit** - Clear code beats clever code
4. **Async by Default** - Embrace Python's async/await
5. **YAGNI** - Don't build abstractions for hypothetical requirements

## Clean Code Principles (Serverless Python)

### 1. Function Design

```python
# ✅ GOOD: Pure function, single responsibility, type hints
async def queue_task(prompt: str, project_id: str, sqs_client=None) -> TaskResponse:
    """Queue a task for agent processing."""
    task_id = str(uuid.uuid4())
    message = TaskMessage(
        task_id=task_id,
        prompt=prompt,
        project_id=project_id,
        created_at=datetime.utcnow()
    )
    
    if not sqs_client:
        sqs_client = get_sqs_client()
    
    await sqs_client.send_message(
        QueueUrl=settings.TASK_QUEUE_URL,
        MessageBody=message.json()
    )
    
    return TaskResponse(task_id=task_id, status="queued")

# ❌ BAD: Doing too much, no type hints, hidden dependencies
class TaskManager:
    def __init__(self):
        self.sqs = boto3.client('sqs')
        self.dynamodb = boto3.resource('dynamodb')
        self.redis = redis.Redis()
        
    def process_and_track_everything(self, data):
        # 200 lines mixing queue, storage, and business logic...
```

### 2. Lambda Handler Pattern

```python
# ✅ GOOD: Thin handler, delegated logic
from mangum import Mangum
from fastapi import FastAPI

app = FastAPI()

@app.post("/api/tasks")
async def create_task(request: TaskRequest) -> TaskResponse:
    """API endpoint delegates to business logic."""
    return await task_service.create_task(request)

# Lambda handler is just an adapter
handler = Mangum(app)

# ❌ BAD: Business logic in handler
def lambda_handler(event, context):
    # 100 lines of parsing, validation, and business logic
    body = json.loads(event['body'])
    # ... tons of code ...
```

### 3. Provider Abstraction

```python
# ✅ GOOD: Abstract interface, concrete implementations
from abc import ABC, abstractmethod

class GitProvider(ABC):
    @abstractmethod
    async def create_pull_request(self, repo: str, title: str, body: str) -> PRInfo:
        """Create a pull request in the repository."""
        pass

class GitHubProvider(GitProvider):
    async def create_pull_request(self, repo: str, title: str, body: str) -> PRInfo:
        # GitHub-specific implementation
        response = await self.client.post(f"/repos/{repo}/pulls", ...)
        return PRInfo(number=response["number"], url=response["html_url"])

# Usage
provider = get_provider(settings.GIT_PROVIDER)  # Factory pattern
pr = await provider.create_pull_request(...)

# ❌ BAD: Direct API usage
if provider_type == "github":
    response = requests.post(f"https://api.github.com/repos/{repo}/pulls")
elif provider_type == "gitlab":
    response = requests.post(f"https://gitlab.com/api/v4/projects/{repo}/merge_requests")
```

### 4. Error Handling

```python
# ✅ GOOD: Specific errors with context
class ProviderError(Exception):
    """Base exception for provider operations."""
    pass

class RateLimitError(ProviderError):
    """Provider API rate limit exceeded."""
    def __init__(self, reset_time: datetime):
        self.reset_time = reset_time
        super().__init__(f"Rate limit exceeded. Resets at {reset_time}")

async def fetch_repository(self, repo_path: str) -> Repository:
    try:
        response = await self.client.get(f"/repos/{repo_path}")
        response.raise_for_status()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            reset_time = datetime.fromtimestamp(
                int(e.response.headers.get("X-RateLimit-Reset", 0))
            )
            raise RateLimitError(reset_time) from e
        elif e.response.status_code == 404:
            raise RepositoryNotFoundError(f"Repository {repo_path} not found") from e
        else:
            logger.error(f"Unexpected error fetching {repo_path}", exc_info=True)
            raise ProviderError(f"Failed to fetch repository: {e}") from e

# ❌ BAD: Generic errors, no context
def fetch_repository(repo):
    try:
        return requests.get(f"https://api.github.com/repos/{repo}").json()
    except Exception:
        return None  # Swallowing errors
```

## Async Best Practices

### 1. Concurrent Operations

```python
# ✅ GOOD: Concurrent execution when possible
async def enrich_task_data(task_id: str) -> EnrichedTask:
    """Fetch related data concurrently."""
    task_future = fetch_task(task_id)
    project_future = fetch_project(task.project_id)
    user_future = fetch_user(task.user_id)
    
    # Execute concurrently
    task, project, user = await asyncio.gather(
        task_future, project_future, user_future
    )
    
    return EnrichedTask(task=task, project=project, user=user)

# ❌ BAD: Sequential when could be concurrent
async def enrich_task_data(task_id: str) -> EnrichedTask:
    task = await fetch_task(task_id)
    project = await fetch_project(task.project_id)  # Waits unnecessarily
    user = await fetch_user(task.user_id)  # Waits unnecessarily
```

### 2. Streaming Responses

```python
# ✅ GOOD: Stream large responses
async def stream_agent_output(task_id: str) -> AsyncIterator[str]:
    """Stream agent output as it's generated."""
    async with aioredis.Redis() as redis:
        pubsub = redis.pubsub()
        await pubsub.subscribe(f"task:{task_id}")
        
        async for message in pubsub.listen():
            if message["type"] == "message":
                yield message["data"].decode()

# ❌ BAD: Load everything into memory
def get_agent_output(task_id: str) -> List[str]:
    return redis.lrange(f"task:{task_id}:output", 0, -1)  # Could be huge
```

## Agent Worker Patterns

### 1. Session Management

```python
# ✅ GOOD: Isolated sessions with cleanup
class AgentSession:
    def __init__(self, task_id: str):
        self.task_id = task_id
        self.workspace = Path(f"/workspaces/{task_id}")
        
    async def __aenter__(self):
        self.workspace.mkdir(parents=True, exist_ok=True)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Cleanup workspace
        if self.workspace.exists():
            shutil.rmtree(self.workspace)

async def process_task(task: Task):
    async with AgentSession(task.task_id) as session:
        result = await run_claude_code(task.prompt, session.workspace)
        await upload_artifacts(session.workspace, task.task_id)

# ❌ BAD: No isolation or cleanup
def process_task(task):
    os.chdir("/tmp")
    subprocess.run(["claude-code", task.prompt])
    # No cleanup, shared directory
```

### 2. Message Processing

```python
# ✅ GOOD: Robust message handling
async def process_sqs_messages():
    """Process messages with proper error handling and acknowledgment."""
    while True:
        try:
            messages = await receive_messages(max_messages=10)
            
            for message in messages:
                try:
                    await process_single_message(message)
                    await delete_message(message)
                except RetryableError:
                    # Leave in queue for retry
                    logger.warning(f"Retryable error for {message['MessageId']}")
                except Exception as e:
                    # Move to DLQ
                    await move_to_dlq(message, str(e))
                    
        except Exception as e:
            logger.error("Error in message processing loop", exc_info=True)
            await asyncio.sleep(5)  # Back off on errors

# ❌ BAD: No error handling
def process_messages():
    while True:
        messages = sqs.receive_message()["Messages"]
        for msg in messages:
            process_task(json.loads(msg["Body"]))
            sqs.delete_message(msg["ReceiptHandle"])
```

## Performance Patterns

### 1. Lambda Cold Start Optimization

```python
# ✅ GOOD: Lazy imports, connection reuse
# Initialize outside handler
_bedrock_client = None

def get_bedrock_client():
    global _bedrock_client
    if _bedrock_client is None:
        _bedrock_client = boto3.client('bedrock-runtime')
    return _bedrock_client

async def handler(event, context):
    # Import heavy dependencies only when needed
    if event.get('use_embeddings'):
        from sentence_transformers import SentenceTransformer
        
# ❌ BAD: Heavy imports at module level
import pandas as pd  # Unnecessary for most requests
import numpy as np
from sentence_transformers import SentenceTransformer  # 500MB model
```

### 2. Batch Processing

```python
# ✅ GOOD: Process in batches
async def sync_repositories(org: str, provider: GitProvider):
    """Sync repositories in batches to avoid memory issues."""
    async for batch in provider.list_repositories_paginated(org, per_page=100):
        # Process batch
        tasks = [process_repo(repo) for repo in batch]
        await asyncio.gather(*tasks)
        
        # Let other operations run
        await asyncio.sleep(0)

# ❌ BAD: Load everything at once
async def sync_repositories(org: str, provider: GitProvider):
    all_repos = await provider.list_all_repositories(org)  # Could be thousands
    for repo in all_repos:
        await process_repo(repo)
```

## Configuration Management

```python
# ✅ GOOD: Typed configuration with validation
from pydantic import BaseSettings, SecretStr

class Settings(BaseSettings):
    # API Configuration
    api_key: SecretStr
    git_provider: Literal["github", "gitlab"] = "github"
    
    # AWS Configuration
    task_queue_url: str
    aws_region: str = "us-east-1"
    
    # Agent Configuration
    max_concurrent_tasks: int = 10
    task_timeout: int = 300
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()

# ❌ BAD: Scattered configuration
API_KEY = os.environ.get("API_KEY")  # No validation
QUEUE_URL = os.environ["QUEUE_URL"]  # Will crash if missing
TIMEOUT = int(os.environ.get("TIMEOUT", "300"))  # Type conversion everywhere
```

## Testing Patterns

### 1. Dependency Injection

```python
# ✅ GOOD: Injectable dependencies
async def create_task(
    request: TaskRequest,
    sqs_client=None,
    provider=None
) -> TaskResponse:
    """Create task with injectable dependencies."""
    if not sqs_client:
        sqs_client = get_sqs_client()
    if not provider:
        provider = get_provider()
    
    # Easy to test with mocks
    
# ❌ BAD: Hardcoded dependencies
async def create_task(request: TaskRequest) -> TaskResponse:
    sqs_client = boto3.client('sqs')  # Hard to test
    provider = GitHubProvider()  # Assumes GitHub
```

### 2. Test Fixtures

```python
# ✅ GOOD: Reusable fixtures
@pytest.fixture
async def task_service():
    """Provide configured task service."""
    return TaskService(
        sqs_client=mock_sqs_client(),
        redis_client=FakeRedis()
    )

@pytest.fixture
def valid_task_request():
    """Standard valid task request."""
    return TaskRequest(
        prompt="Create a Python hello world",
        project_id="test-project"
    )

# ❌ BAD: Duplicated setup in every test
async def test_something():
    sqs = Mock()
    redis = Mock()
    service = TaskService(sqs, redis)
    request = {"prompt": "test", "project_id": "test"}  # Repeated everywhere
```

## Code Organization

### Directory Structure
```
backend/
├── app/
│   ├── api/          # FastAPI routes (thin layer)
│   ├── core/         # Business logic
│   ├── providers/    # Git provider implementations
│   ├── models/       # Pydantic models
│   └── services/     # Service layer
├── tests/
│   ├── unit/         # Fast, isolated tests
│   └── integration/  # Tests with real dependencies
└── lambda_handler.py # Lambda entry point

agent/
├── wrapper/
│   ├── claude_code.py  # Claude Code wrapper
│   ├── session.py      # Session management
│   └── sqs_handler.py  # Queue processing
├── tests/
└── Dockerfile
```

## Anti-Patterns to Avoid

### 1. God Classes
```python
# ❌ BAD: Class doing everything
class AgentManager:
    def __init__(self):
        self.sqs = boto3.client('sqs')
        self.s3 = boto3.client('s3')
        self.dynamodb = boto3.resource('dynamodb')
        self.redis = redis.Redis()
        
    def receive_messages(self): ...
    def process_task(self): ...
    def store_results(self): ...
    def send_notifications(self): ...
    # 1000 lines of mixed concerns
```

### 2. Premature Optimization
```python
# ❌ BAD: Complex caching for unproven need
class CachedProviderWithMemoryPoolAndCircuitBreaker:
    def __init__(self):
        self.cache = LRUCache(maxsize=1000)
        self.memory_pool = MemoryPool()
        self.circuit_breaker = CircuitBreaker()
        # Over-engineered before measuring
```

### 3. Implicit Provider Logic
```python
# ❌ BAD: Provider-specific code scattered
if "github.com" in url:
    headers = {"Authorization": f"token {token}"}
elif "gitlab.com" in url:
    headers = {"Private-Token": token}
```

## Code Review Checklist

Before submitting code, verify:

- [ ] **Provider Abstraction**: No hardcoded GitHub/GitLab specifics
- [ ] **Type Hints**: All functions have type annotations
- [ ] **Error Handling**: Specific exceptions with context
- [ ] **Async Correctness**: Proper use of async/await
- [ ] **Testability**: Dependencies are injectable
- [ ] **No Secrets**: No hardcoded credentials or keys
- [ ] **Lambda Constraints**: Consider cold starts and timeouts
- [ ] **Clean Resources**: Files, connections cleaned up

## Examples: Refactoring for Quality

### Before: Monolithic Function
```python
def process_webhook(event):
    body = json.loads(event['body'])
    
    # Validation
    if 'action' not in body:
        return {'statusCode': 400}
    
    # Provider detection
    if 'github' in event['headers'].get('user-agent', ''):
        # GitHub logic
        token = os.environ['GITHUB_TOKEN']
        repo = body['repository']['full_name']
    else:
        # GitLab logic
        token = os.environ['GITLAB_TOKEN']
        repo = body['project']['path_with_namespace']
    
    # Processing
    result = subprocess.run(['claude-code', body['prompt']])
    
    # Storage
    s3 = boto3.client('s3')
    s3.put_object(...)
    
    return {'statusCode': 200}
```

### After: Clean Separation
```python
@app.post("/webhooks/{provider}")
async def handle_webhook(
    provider: str,
    request: Request,
    background_tasks: BackgroundTasks
):
    """Handle incoming webhooks from git providers."""
    # Validate webhook signature
    webhook_handler = get_webhook_handler(provider)
    if not await webhook_handler.validate_signature(request):
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    # Parse webhook data
    event = await webhook_handler.parse_event(request)
    
    # Queue for processing
    task_id = await task_service.create_from_webhook(event)
    
    # Process asynchronously
    background_tasks.add_task(process_webhook_task, task_id)
    
    return {"task_id": task_id, "status": "queued"}
```

## Conclusion

Good backend code in our serverless architecture should be:
- **Cloud-Native** - Designed for Lambda and ECS constraints
- **Provider-Agnostic** - Abstract away GitHub/GitLab specifics  
- **Type-Safe** - Use type hints everywhere
- **Async-First** - Embrace concurrent operations
- **Testable** - Dependencies are injectable
- **Simple** - Avoid premature abstraction

Remember: We're building a POC that can scale. Start simple, measure, then optimize.