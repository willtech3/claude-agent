# CLAUDE.md - Backend Testing Guidelines

## Inheritance
- **Extends:** /CLAUDE.md (root)
- **Overrides:** None (CRITICAL RULES cannot be overridden)
- **Scope:** All Python test files in backend/tests and agent/tests

## Rules

**Context:** This document provides testing best practices and guidelines for Claude Agent backend services. Read this when writing tests for FastAPI endpoints, Lambda functions, Agent workers, or reviewing test quality.

---

# Backend Testing Guidelines for Claude Agent

This document outlines testing best practices for our Python backend services including the FastAPI Lambda API and the containerized Agent worker.

## Table of Contents
- [Testing Philosophy](#testing-philosophy)
- [Test Quality Standards](#test-quality-standards)
- [Mock Usage Guidelines](#mock-usage-guidelines)
- [Coverage Requirements](#coverage-requirements)
- [Test Organization](#test-organization)
- [Testing Async Code](#testing-async-code)
- [Testing AWS Services](#testing-aws-services)
- [Testing Provider Abstractions](#testing-provider-abstractions)
- [Common Anti-Patterns](#common-anti-patterns)
- [Best Practices by Component](#best-practices-by-component)

## Testing Philosophy

### Core Principles
1. **Test behavior, not implementation** - Focus on what the code does, not how it does it
2. **Test public interfaces only** - Private methods are tested through public ones
3. **Prefer fixtures over mocks** - Use real objects when possible, mock only external dependencies
4. **Build refactoring confidence** - Tests should make developers confident to change code

### Test Pyramid for Cloud-Native Apps
```
         /\
        /  \    E2E Tests (Lambda→SQS→Agent)
       /    \
      /------\  Integration Tests (API + LocalStack)
     /        \
    /----------\ Unit Tests (Business logic, providers)
```

## Test Quality Standards

### High-Quality Test Characteristics
- **Clear intent**: Test name describes scenario and expected outcome
- **Focused**: Each test verifies one specific behavior
- **Deterministic**: Consistent results every run
- **Fast**: Unit tests < 100ms, integration tests < 5s
- **Independent**: No shared state between tests

### Example of a Good Test
```python
async def test_create_task_sends_message_to_sqs(
    test_client, mock_sqs_client, valid_task_request
):
    """Creating a task should send a properly formatted message to SQS."""
    # Arrange
    expected_task_id = "test-123"
    
    # Act
    response = await test_client.post("/api/tasks", json=valid_task_request)
    
    # Assert behavior, not implementation
    assert response.status_code == 201
    assert response.json()["task_id"]
    
    # Verify the message was sent with correct structure
    mock_sqs_client.send_message.assert_called_once()
    message_body = json.loads(
        mock_sqs_client.send_message.call_args[1]["MessageBody"]
    )
    assert message_body["prompt"] == valid_task_request["prompt"]
    assert "task_id" in message_body
```

## Mock Usage Guidelines

### When to Mock
| What to Mock | Reason |
|--------------|--------|
| AWS Services (SQS, S3, Bedrock) | Avoid AWS costs and ensure deterministic behavior |
| External APIs (GitHub, GitLab) | Prevent rate limiting and network dependencies |
| Claude Code CLI | Test wrapper logic without running actual AI |
| Redis/Database in unit tests | Test logic in isolation |
| Time/UUID generation | Control test values |

### When NOT to Mock
| What NOT to Mock | Reason |
|------------------|--------|
| Provider abstractions | Test the actual abstraction behavior |
| Data models/schemas | Ensure serialization works correctly |
| Business logic classes | Test real behavior |
| FastAPI dependencies | Use override_dependency instead |

### Prefer Fixtures
```python
# ✅ GOOD - Fixture with real object
@pytest.fixture
def github_provider():
    return GitHubProvider(
        token="test-token",
        base_url="https://api.github.com"
    )

# ❌ AVOID - Mock when fixture would work
def test_with_mock():
    provider = Mock(spec=GitHubProvider)
    # Missing real behavior
```

## Coverage Requirements

### By Component (Target Goals)
| Component | Target Coverage | Rationale |
|-----------|-----------------|-----------|
| API Endpoints | 85% | Critical user-facing functionality |
| Provider Abstractions | 90% | Core abstraction must be reliable |
| Agent Worker | 80% | Complex external dependencies |
| Data Models | 95% | Simple but critical for contracts |
| Overall | 80% | Reasonable target for confidence |

**Note**: Focus on meaningful tests over coverage percentage. A well-tested critical path is better than 100% coverage with shallow tests.

## Test Organization

### Directory Structure
```
backend/tests/
├── unit/                    # Fast, isolated tests
│   ├── providers/          # Provider abstraction tests
│   ├── models/             # Data model tests
│   └── core/               # Business logic tests
├── integration/            # Tests with dependencies
│   ├── test_api_e2e.py    # Full API flow tests
│   ├── test_sqs_flow.py   # Queue integration tests
│   └── test_providers.py  # Real provider tests
├── fixtures/              # Shared test data
│   ├── __init__.py
│   ├── providers.py       # Provider test fixtures
│   └── tasks.py           # Task/request fixtures
└── conftest.py            # Pytest configuration

agent/tests/
├── unit/
│   ├── test_wrapper.py    # Claude Code wrapper tests
│   ├── test_session.py    # Session management tests
│   └── test_parser.py     # Output parser tests
└── integration/
    └── test_sqs_worker.py # SQS integration tests
```

## Testing Async Code

### FastAPI Async Endpoints
```python
# Use httpx for async client
async def test_websocket_streaming(test_client):
    async with test_client.websocket_connect(f"/ws/{task_id}") as websocket:
        # Send task
        await websocket.send_json({"action": "start"})
        
        # Verify streaming
        data = await websocket.receive_json()
        assert data["type"] == "output"
```

### Async AWS Operations
```python
# Use pytest-asyncio
@pytest.mark.asyncio
async def test_agent_processes_sqs_message(sqs_message, mock_claude_code):
    # Arrange
    worker = AgentWorker()
    mock_claude_code.run.return_value = AsyncIterator(["line1", "line2"])
    
    # Act
    await worker.process_message(sqs_message)
    
    # Assert
    assert mock_claude_code.run.called_with(sqs_message["prompt"])
```

## Testing AWS Services

### LocalStack for Integration Tests
```python
@pytest.fixture
def localstack_sqs():
    """Use LocalStack for integration tests."""
    return boto3.client(
        "sqs",
        endpoint_url="http://localhost:4566",
        region_name="us-east-1"
    )

async def test_task_flow_with_localstack(test_client, localstack_sqs):
    # Create real queue
    queue_url = localstack_sqs.create_queue(QueueName="test-tasks")["QueueUrl"]
    
    # Test real SQS behavior
    response = await test_client.post("/api/tasks", json={"prompt": "test"})
    
    # Verify message in queue
    messages = localstack_sqs.receive_message(QueueUrl=queue_url)
    assert len(messages.get("Messages", [])) == 1
```

### Mocking AWS Services for Unit Tests
```python
@pytest.fixture
def mock_sqs():
    with patch("boto3.client") as mock:
        yield mock.return_value

def test_send_task_to_queue(mock_sqs):
    # Control AWS behavior
    mock_sqs.send_message.return_value = {"MessageId": "123"}
    
    # Test your code
    service = TaskService(sqs_client=mock_sqs)
    result = service.queue_task("test prompt")
    
    # Verify behavior
    assert result.message_id == "123"
```

## Testing Provider Abstractions

### Test the Contract, Not the Provider
```python
class TestGitProviderContract:
    """Test that all providers meet the contract."""
    
    @pytest.fixture(params=["github", "gitlab"])
    def provider(self, request):
        if request.param == "github":
            return GitHubProvider(token="test")
        else:
            return GitLabProvider(token="test")
    
    def test_get_repository_returns_standard_format(self, provider, mock_responses):
        """All providers must return repositories in standard format."""
        # Arrange
        mock_responses.add(
            method="GET",
            url=re.compile(r".*/(repos|projects)/.*"),
            json={"id": 123, "name": "test-repo"}
        )
        
        # Act
        repo = provider.get_repository("owner/repo")
        
        # Assert standard format
        assert isinstance(repo, Repository)
        assert repo.id
        assert repo.name
```

## Common Anti-Patterns

### 1. Testing Implementation Details
```python
# ❌ BAD - Tests private method
def test_private_parser():
    worker = AgentWorker()
    result = worker._parse_claude_output("data")
    assert result == expected

# ✅ GOOD - Tests through public interface
def test_worker_processes_claude_output():
    worker = AgentWorker()
    result = worker.process_task("create a function")
    assert "function" in result.artifacts[0].content
```

### 2. Over-Mocking
```python
# ❌ BAD - Mocks everything
def test_with_all_mocks():
    mock_sqs = Mock()
    mock_redis = Mock()
    mock_provider = Mock()
    service = TaskService(mock_sqs, mock_redis, mock_provider)
    # Not testing real behavior

# ✅ GOOD - Mock only external dependencies
def test_with_minimal_mocks(real_provider):
    mock_sqs = Mock()  # Mock AWS service
    redis = FakeRedis()  # Use fake implementation
    service = TaskService(mock_sqs, redis, real_provider)
    # Tests real interaction between components
```

### 3. Ignoring Async Context
```python
# ❌ BAD - Doesn't handle async properly
def test_async_endpoint():
    response = client.post("/api/tasks", json=data)  # Misses async

# ✅ GOOD - Proper async testing
async def test_async_endpoint(async_client):
    response = await async_client.post("/api/tasks", json=data)
    assert response.status_code == 201
```

## Best Practices by Component

### API Endpoint Tests
```python
# Use test client fixture
async def test_create_task_validates_input(test_client):
    # Test validation
    response = await test_client.post("/api/tasks", json={})
    assert response.status_code == 422
    assert "prompt" in response.json()["detail"][0]["loc"]

# Test error handling
async def test_handles_provider_errors_gracefully(test_client, mock_provider):
    mock_provider.create_issue.side_effect = ProviderError("API limit")
    
    response = await test_client.post("/api/tasks", json=valid_data)
    assert response.status_code == 503
    assert "temporarily unavailable" in response.json()["message"]
```

### Agent Worker Tests
```python
# Test message processing
async def test_worker_handles_malformed_messages(worker, bad_message):
    # Should not crash on bad input
    result = await worker.process_message(bad_message)
    assert result.status == "failed"
    assert "Invalid message format" in result.error

# Test Claude Code integration
async def test_worker_streams_output_to_redis(worker, mock_claude, mock_redis):
    mock_claude.run.return_value = AsyncIterator(["Building...", "Done!"])
    
    await worker.process_task("task-123", "create app")
    
    # Verify streaming
    calls = mock_redis.publish.call_args_list
    assert len(calls) == 2
    assert "Building..." in calls[0][0][1]
```

### Provider Tests
```python
# Test error handling
def test_github_provider_handles_rate_limits(github_provider, mock_responses):
    mock_responses.add(
        method="GET",
        url="https://api.github.com/repos/test/repo",
        status=429,
        headers={"X-RateLimit-Reset": "1234567890"}
    )
    
    with pytest.raises(RateLimitError) as exc:
        github_provider.get_repository("test/repo")
    
    assert exc.value.reset_time == 1234567890
```

## Performance Testing

### Load Testing Endpoints
```python
# Use pytest-benchmark for performance tests
def test_task_creation_performance(benchmark, test_client):
    def create_task():
        response = test_client.post("/api/tasks", json={"prompt": "test"})
        assert response.status_code == 201
    
    # Should handle 100 requests/second
    result = benchmark(create_task)
    assert result.stats.mean < 0.01  # 10ms average
```

## WebSocket Testing

```python
async def test_websocket_handles_disconnection(test_client):
    async with test_client.websocket_connect(f"/ws/{task_id}") as ws:
        # Simulate work
        await ws.send_json({"action": "start"})
        
        # Client disconnects
        await ws.close()
        
    # Verify cleanup happened
    assert task_id not in active_connections
```

## Continuous Improvement

### Test Maintenance
1. **Remove obsolete tests** when features are removed
2. **Update fixtures** when data models change
3. **Refactor test code** - apply same quality standards as production
4. **Monitor flaky tests** - Fix or remove unreliable tests

### Red Flags in Tests
- Tests that only verify mocks were called
- Tests with more than 20 lines of setup
- Tests that break when refactoring without changing behavior
- Tests slower than 5 seconds (except integration tests)
- Tests that depend on execution order

Remember: **Tests should give you confidence to refactor and deploy. If they don't, improve them.**