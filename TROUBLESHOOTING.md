# Claude Agent Troubleshooting Guide

This guide helps diagnose and resolve common issues with the Claude Agent POC.

## Quick Diagnostics

Run this command to check all services:
```bash
./scripts/test-integration.sh
```

## Common Issues

### 🔴 Services Won't Start

#### Symptom
```
Error: docker-compose not found
```

#### Solution
Install Docker Desktop from https://www.docker.com/products/docker-desktop/

---

#### Symptom
```
Error: bind: address already in use
```

#### Solution
Check what's using the ports:
```bash
# Check common ports
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis
lsof -i :4566  # LocalStack
lsof -i :8000  # Backend API
lsof -i :3000  # Frontend

# Kill the process using the port
kill -9 <PID>

# Or change the port in docker-compose.local.yml
```

---

### 🔴 Backend API Issues

#### Symptom
```
Error: SAM/Serverless not found
```

#### Solution
```bash
# Install SAM CLI
brew install aws-sam-cli

# OR use Python directly
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

---

#### Symptom
```
Error: Module 'app' not found
```

#### Solution
```bash
cd backend
# Use uv (recommended)
uv sync
uv run uvicorn app.main:app --reload

# OR use pip
pip install -e .
```

---

### 🔴 Agent Issues

#### Symptom
```
Error: ANTHROPIC_API_KEY not set
```

#### Solution
```bash
# Set your API key
export ANTHROPIC_API_KEY="your-key-here"

# Or create .env file
echo "ANTHROPIC_API_KEY=your-key-here" > agent/.env

# Restart agent
cd agent
docker build -t claude-agent .
docker run -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY claude-agent
```

---

#### Symptom
```
Agent not processing tasks
```

#### Solution
1. Check SQS queue:
```bash
aws --endpoint-url=http://localhost:4566 sqs get-queue-attributes \
  --queue-url http://localhost:4566/000000000000/tasks \
  --attribute-names ApproximateNumberOfMessages
```

2. Check agent logs:
```bash
docker logs claude-agent
```

3. Verify agent can access LocalStack:
```bash
docker network ls
# Ensure agent and localstack are on same network
```

---

### 🔴 Frontend Issues

#### Symptom
```
Error: Cannot find module 'next'
```

#### Solution
```bash
cd frontend
npm install
npm run dev
```

---

#### Symptom
```
WebSocket connection failed
```

#### Solution
1. Check backend is running
2. Check CORS configuration in backend
3. Verify WebSocket URL in frontend config
4. Test with:
```javascript
// In browser console
const ws = new WebSocket('ws://localhost:8000/ws/test');
ws.onopen = () => console.log('Connected');
ws.onerror = (e) => console.error('Error:', e);
```

---

### 🔴 Database Issues

#### Symptom
```
Error: relation "tasks" does not exist
```

#### Solution
Run migrations:
```bash
cd backend
alembic upgrade head
```

---

#### Symptom
```
PostgreSQL connection refused
```

#### Solution
1. Check PostgreSQL is running:
```bash
docker-compose -f docker-compose.local.yml ps postgres
```

2. Verify credentials in backend/.env:
```
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/claude_agent
```

---

### 🔴 Redis Issues

#### Symptom
```
Redis connection timeout
```

#### Solution
1. Check Redis is running:
```bash
docker-compose -f docker-compose.local.yml exec redis redis-cli ping
```

2. Verify Redis URL in backend config:
```
REDIS_URL=redis://localhost:6379
```

---

### 🔴 LocalStack/SQS Issues

#### Symptom
```
SQS queue not found
```

#### Solution
Create the queue manually:
```bash
aws --endpoint-url=http://localhost:4566 sqs create-queue --queue-name tasks
```

---

### 🔴 File/Workspace Issues

#### Symptom
```
Files not appearing in workspace
```

#### Solution
1. Check workspace directory exists:
```bash
mkdir -p workspaces
chmod 755 workspaces
```

2. Verify agent volume mount:
```bash
docker run -v $(pwd)/workspaces:/workspaces claude-agent
```

---

## Debugging Commands

### Check All Services
```bash
# Docker containers
docker ps -a

# Docker compose services
docker-compose -f docker-compose.local.yml ps

# Service logs
docker-compose -f docker-compose.local.yml logs
```

### Backend Debugging
```bash
# Test API directly
curl http://localhost:8000/health

# View API docs
open http://localhost:8000/docs

# Check task creation
curl -X POST http://localhost:8000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"prompt": "test", "context": {}}'
```

### Agent Debugging
```bash
# Run agent interactively
docker run -it --entrypoint /bin/bash claude-agent

# Inside container, test Claude Code
claude-code "Create hello.py"

# Check environment
env | grep -E "(ANTHROPIC|AWS|SQS)"
```

### Database Debugging
```bash
# Connect to PostgreSQL
docker-compose -f docker-compose.local.yml exec postgres psql -U postgres

# Useful queries
\dt                    -- List tables
\d tasks              -- Describe tasks table
SELECT * FROM tasks;  -- View all tasks
```

### Redis Debugging
```bash
# Connect to Redis
docker-compose -f docker-compose.local.yml exec redis redis-cli

# Useful commands
KEYS *                -- List all keys
SUBSCRIBE "task:*"    -- Monitor task events
MONITOR              -- Watch all commands
```

## Performance Issues

### High Memory Usage
```bash
# Check container stats
docker stats

# Limit container resources in docker-compose.local.yml:
services:
  agent:
    mem_limit: 2g
    cpus: '2.0'
```

### Slow Response Times
1. Check service logs for errors
2. Monitor Redis for bottlenecks
3. Check PostgreSQL query performance
4. Verify network connectivity between services

## Reset Everything

If all else fails, clean slate:
```bash
# Stop all services
docker-compose -f docker-compose.local.yml down -v

# Remove all containers and volumes
docker system prune -a --volumes

# Clean workspace
rm -rf workspaces/*

# Remove node_modules and reinstall
rm -rf frontend/node_modules
cd frontend && npm install

# Remove Python cache
find . -type d -name __pycache__ -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

# Start fresh
./scripts/start-poc.sh
```

## Getting Help

1. **Check logs first** - Most issues are visible in logs
2. **Search existing issues** - https://github.com/willtech3/claude-agent/issues
3. **Create detailed bug report** with:
   - Error messages
   - Steps to reproduce
   - Environment details (OS, Docker version, etc.)
   - Relevant logs

## Useful Resources

- [Docker Troubleshooting](https://docs.docker.com/desktop/troubleshoot/overview/)
- [FastAPI Debugging](https://fastapi.tiangolo.com/tutorial/debugging/)
- [LocalStack Issues](https://github.com/localstack/localstack/issues)
- [WebSocket Debugging](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)