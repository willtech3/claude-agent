# Claude Agent POC Testing Guide

This guide covers testing procedures for the Claude Agent POC, including setup, execution, and troubleshooting.

## Prerequisites

- Docker and docker compose installed
- Python 3.9+ with pip
- Node.js 18+ with npm
- AWS CLI configured (for LocalStack)
- Git and GitHub CLI (gh) installed

## Quick Start

1. **Start all services:**
   ```bash
   ./scripts/start-poc.sh
   ```

2. **Run integration tests:**
   ```bash
   ./scripts/test-integration.sh
   ```

3. **View logs:**
   ```bash
   docker compose -f docker compose.local.yml logs -f
   ```

## Service Architecture

The POC consists of the following services:

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Frontend  │────▶│   Backend   │────▶│    Agent    │
│  (Next.js)  │     │  (FastAPI)  │     │   (Docker)  │
└─────────────┘     └─────────────┘     └─────────────┘
       │                    │                    │
       └────────────────────┼────────────────────┘
                           │
                    ┌──────▼──────┐
                    │Infrastructure│
                    │ - Redis      │
                    │ - PostgreSQL │
                    │ - LocalStack │
                    └─────────────┘
```

## Test Scenarios

### 1. Basic Task Execution
**Test:** Submit a simple code generation request
```bash
curl -X POST http://localhost:8000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Create a Python hello world script", "context": {}}'
```

**Expected Result:**
- Task ID returned immediately
- WebSocket streams output in real-time
- `hello.py` created in workspace directory

### 2. Multi-file Generation
**Test:** Request creation of a complete application
```bash
curl -X POST http://localhost:8000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Create a Flask API with /users and /posts endpoints", "context": {}}'
```

**Expected Result:**
- Multiple files created (app.py, requirements.txt, etc.)
- Proper project structure
- All files in task-specific workspace

### 3. Error Handling
**Test:** Submit invalid requests
```bash
# Empty prompt
curl -X POST http://localhost:8000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"prompt": "", "context": {}}'

# Missing prompt
curl -X POST http://localhost:8000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"context": {}}'
```

**Expected Result:**
- 422 validation error
- Clear error message
- No task created

### 4. Long-running Tasks
**Test:** Submit complex, time-consuming request
```bash
curl -X POST http://localhost:8000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Create a complete React TODO app with TypeScript, tests, and documentation",
    "context": {}
  }'
```

**Expected Result:**
- Continuous output streaming
- No timeout errors
- Progress updates via WebSocket
- Complete file structure generated

### 5. Concurrent Tasks
**Test:** Submit multiple tasks rapidly
```bash
for i in {1..3}; do
  curl -X POST http://localhost:8000/api/tasks \
    -H "Content-Type: application/json" \
    -d "{\"prompt\": \"Create script number $i\", \"context\": {}}" &
done
```

**Expected Result:**
- All tasks queued successfully
- Sequential processing (FIFO)
- No race conditions
- Each task gets separate workspace

## Manual Testing Checklist

### Infrastructure
- [ ] Redis is running and accessible
- [ ] PostgreSQL is running and accessible
- [ ] LocalStack SQS queue is created
- [ ] All containers are healthy

### Backend API
- [ ] Health endpoint returns 200 OK
- [ ] Task creation endpoint works
- [ ] Task status endpoint works
- [ ] WebSocket connections establish
- [ ] Error responses are properly formatted

### Agent
- [ ] Processes SQS messages
- [ ] Executes Claude Code CLI
- [ ] Captures output correctly
- [ ] Handles errors gracefully
- [ ] Creates files in correct workspace

### Frontend (if running)
- [ ] Loads at http://localhost:3000
- [ ] Can submit tasks
- [ ] Shows real-time output
- [ ] Displays errors properly
- [ ] Shows task completion

### End-to-End Flow
- [ ] Submit task via UI/API
- [ ] Task queued in SQS
- [ ] Agent picks up task
- [ ] Output streams to WebSocket
- [ ] Files created in workspace
- [ ] Task marked complete

## Debugging Guide

### Check Service Health

```bash
# Redis
docker compose -f docker compose.local.yml exec redis redis-cli ping

# PostgreSQL
docker compose -f docker compose.local.yml exec postgres pg_isready

# LocalStack
curl http://localhost:4566/_localstack/health

# Backend API
curl http://localhost:8000/health
```

### View Logs

```bash
# All services
docker compose -f docker compose.local.yml logs -f

# Specific service
docker compose -f docker compose.local.yml logs -f [service-name]

# Backend API logs
sam logs -n BackendFunction --tail

# Agent logs
docker logs claude-agent
```

### Check SQS Queue

```bash
# List queues
aws --endpoint-url=http://localhost:4566 sqs list-queues

# Get queue attributes
aws --endpoint-url=http://localhost:4566 sqs get-queue-attributes \
  --queue-url http://localhost:4566/000000000000/tasks \
  --attribute-names All

# Receive messages (for debugging)
aws --endpoint-url=http://localhost:4566 sqs receive-message \
  --queue-url http://localhost:4566/000000000000/tasks
```

### Database Inspection

```bash
# Connect to PostgreSQL
docker compose -f docker compose.local.yml exec postgres psql -U postgres

# In psql:
\dt  # List tables
SELECT * FROM tasks;  # View tasks
```

### Redis Monitoring

```bash
# Connect to Redis CLI
docker compose -f docker compose.local.yml exec redis redis-cli

# Monitor all commands
MONITOR

# Check pub/sub channels
PUBSUB CHANNELS

# Subscribe to task events
SUBSCRIBE "task:*"
```

## Common Issues and Solutions

### Issue: Services won't start
**Solution:**
```bash
# Clean up existing containers
docker compose -f docker compose.local.yml down -v
# Remove old volumes
docker volume prune
# Restart
./scripts/start-poc.sh
```

### Issue: Agent not processing tasks
**Solution:**
1. Check agent is running: `docker ps | grep claude-agent`
2. Check SQS queue has messages
3. Check agent logs for errors
4. Verify ANTHROPIC_API_KEY is set

### Issue: WebSocket connection fails
**Solution:**
1. Check backend is running
2. Verify CORS settings
3. Check browser console for errors
4. Try direct WebSocket test:
   ```javascript
   const ws = new WebSocket('ws://localhost:8000/ws/test-task-id');
   ws.onmessage = (e) => console.log(e.data);
   ```

### Issue: Files not created in workspace
**Solution:**
1. Check workspace directory permissions
2. Verify agent has volume mount
3. Check agent logs for file write errors
4. Ensure workspace directory exists

## Performance Testing

### Load Testing
```bash
# Install hey (HTTP load generator)
go install github.com/rakyll/hey@latest

# Test API endpoint
hey -n 100 -c 10 -m POST \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Create hello.py", "context": {}}' \
  http://localhost:8000/api/tasks
```

### Memory/CPU Monitoring
```bash
# Monitor container resources
docker stats

# Check specific container
docker stats claude-agent
```

## Automated Testing

### Run Python Integration Tests
```bash
# Install dependencies
pip install pytest requests websocket-client

# Run all tests
pytest tests/integration/test_poc_integration.py -v

# Run specific test
pytest tests/integration/test_poc_integration.py::TestBasicIntegration::test_create_simple_task -v

# Run with coverage
pytest tests/integration/test_poc_integration.py --cov=app --cov-report=html
```

### Frontend Tests
```bash
cd frontend
npm test
npm run test:watch  # Watch mode
npm run test:coverage  # With coverage
```

### Backend Unit Tests
```bash
cd backend
uv run pytest tests/ -v
```

## Continuous Integration

The POC includes GitHub Actions workflows that run on every push:

1. **Backend Tests:** Python unit and integration tests
2. **Frontend Tests:** Jest tests for React components
3. **Linting:** Code quality checks
4. **Security:** Dependency vulnerability scanning

To run CI checks locally:
```bash
make check  # Run all checks
make backend-check  # Backend only
make frontend-check  # Frontend only
```

## Next Steps

After successful testing:

1. Document any issues found
2. Create GitHub issues for bugs
3. Update this guide with new scenarios
4. Consider performance optimizations
5. Plan for production deployment

## Resources

- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [Jest Documentation](https://jestjs.io/docs/getting-started)
- [LocalStack Documentation](https://docs.localstack.cloud/)
- [WebSocket Testing](https://websocket.org/echo.html)