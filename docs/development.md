# Development Environment

This document describes how to set up and use the Claude Agent development environment.

## Architecture Overview

```
┌─────────────┐     ┌──────────────┐     ┌───────────┐
│   Frontend  │────▶│   Backend    │────▶│   Agent   │
│  (Next.js)  │     │ (FastAPI/    │     │   (ECS)   │
│             │     │  Lambda)     │     │           │
└─────────────┘     └──────────────┘     └───────────┘
                            │                    │
                            ▼                    ▼
                    ┌──────────────┐     ┌───────────┐
                    │  LocalStack  │     │   Redis   │
                    │ (AWS Services)│     │  (Cache)  │
                    └──────────────┘     └───────────┘
                            │
                            ▼
                    ┌──────────────┐
                    │  PostgreSQL  │
                    │  (Database)  │
                    └──────────────┘
```

## Quick Start

1. **Start all services:**
   ```bash
   ./scripts/dev.sh
   ```

2. **Start frontend (in a new terminal):**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

3. **Test services:**
   ```bash
   ./scripts/test-services.sh
   ```

## Services

### Frontend (Next.js)
- **URL:** http://localhost:3000
- **Hot Reload:** Yes
- **Start:** `npm run dev` in `frontend/`

### Backend API (FastAPI on Lambda)
- **URL:** http://localhost:3001
- **Hot Reload:** Yes (via SAM)
- **Start:** Automatically started by `dev.sh`
- **Direct run:** `cd backend && sam local start-api`

### Agent (ECS Container)
- **URL:** http://localhost:8080
- **Health:** http://localhost:8080/health
- **Metrics:** http://localhost:8080/metrics
- **Hot Reload:** Yes (volume mounted)

### LocalStack (AWS Services)
- **URL:** http://localhost:4566
- **Services:** S3, SQS, DynamoDB, Lambda, ECS, ECR, CloudWatch Logs
- **Credentials:** Use any value (e.g., "test")

### PostgreSQL
- **Host:** localhost:5432
- **Database:** claude_agent
- **User:** claude
- **Password:** claude_dev_password

### Redis
- **Host:** localhost:6379
- **No authentication in dev**

## Development Workflow

### API Development

1. **Make changes** to backend code
2. **SAM automatically reloads** the Lambda function
3. **Test endpoints** at http://localhost:3001

### Agent Development

1. **Make changes** to agent code
2. **Container automatically reloads** (if using uvicorn with reload)
3. **Monitor logs:** `docker-compose logs -f agent`

### Database Migrations

```bash
cd backend
alembic revision --autogenerate -m "Description"
alembic upgrade head
```

### Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test

# Integration tests
docker-compose run tests
```

## Environment Variables

### Backend (.env or env.json)
```json
{
  "ENVIRONMENT": "development",
  "DATABASE_URL": "postgresql://claude:claude_dev_password@postgres:5432/claude_agent",
  "REDIS_URL": "redis://redis:6379",
  "AWS_ENDPOINT_URL": "http://localstack:4566",
  "JWT_SECRET_KEY": "dev-secret-key",
  "ALLOWED_ORIGINS": "[\"http://localhost:3000\"]"
}
```

### Agent
- `ENV`: development
- `REDIS_URL`: redis://redis:6379
- `SQS_QUEUE_URL`: http://localstack:4566/000000000000/claude-agent-tasks
- `AWS_ENDPOINT_URL`: http://localstack:4566

## Troubleshooting

### Services not starting
```bash
# Check status
docker-compose ps

# View logs
docker-compose logs [service-name]

# Restart everything
docker-compose down
./scripts/dev.sh
```

### Port conflicts
- Frontend: 3000
- API: 3001
- Agent: 8080
- LocalStack: 4566
- PostgreSQL: 5432
- Redis: 6379

### AWS CLI with LocalStack
```bash
aws --endpoint-url=http://localhost:4566 [command]
```

## Useful Commands

```bash
# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v

# View logs
docker-compose logs -f [service]

# Shell into container
docker-compose exec [service] sh

# Reset database
docker-compose exec postgres psql -U claude -c "DROP DATABASE claude_agent; CREATE DATABASE claude_agent;"
```