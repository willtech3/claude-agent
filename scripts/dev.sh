#!/bin/bash
set -e

# Script to start development environment

echo "Starting Claude Agent development environment..."

# Ensure docker network exists
docker network create repo_default 2>/dev/null || true

# Start infrastructure services
echo "Starting infrastructure services..."
docker-compose up -d localstack postgres redis

# Wait for services to be healthy
echo "Waiting for services to be ready..."
sleep 5

# Initialize LocalStack resources
echo "Creating LocalStack resources..."
aws --endpoint-url=http://localhost:4566 sqs create-queue --queue-name claude-agent-tasks 2>/dev/null || true
aws --endpoint-url=http://localhost:4566 s3 mb s3://claude-agent-files 2>/dev/null || true

# Start agent service
echo "Starting agent service..."
docker-compose up -d agent

# Start API with SAM
echo "Starting API with SAM..."
cd backend
sam local start-api --docker-network repo_default &
cd ..

# Instructions
echo ""
echo "✅ Development environment started!"
echo ""
echo "Services:"
echo "  - Frontend: http://localhost:3000 (run 'npm run dev' in frontend/)"
echo "  - API: http://localhost:3001"
echo "  - Agent: http://localhost:8080"
echo "  - LocalStack: http://localhost:4566"
echo "  - PostgreSQL: localhost:5432"
echo "  - Redis: localhost:6379"
echo ""
echo "To stop all services: docker-compose down"