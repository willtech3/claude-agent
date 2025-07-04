#!/bin/bash
set -e

# Script to test all services are working

echo "Testing Claude Agent services..."

# Test LocalStack
echo -n "LocalStack: "
curl -s http://localhost:4566/_localstack/health | jq -r .services[] | head -1 && echo "✓"

# Test PostgreSQL
echo -n "PostgreSQL: "
docker exec repo_postgres_1 pg_isready -U claude -d claude_agent && echo "✓"

# Test Redis
echo -n "Redis: "
docker exec repo_redis_1 redis-cli ping && echo "✓"

# Test Agent
echo -n "Agent: "
curl -s http://localhost:8080/health | jq -r .status && echo "✓"

# Test API (if running)
echo -n "API: "
curl -s http://localhost:3001/health 2>/dev/null && echo "✓" || echo "Not running"

echo ""
echo "All services tested!"