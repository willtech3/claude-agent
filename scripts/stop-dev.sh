#!/bin/bash
set -e

echo "Stopping Claude Agent development environment..."

# Stop docker services
echo "Stopping Docker services..."
docker-compose down

# Stop SAM API if running
echo "Stopping SAM API..."
pkill -f "sam local start-api" || true

# Clean up any orphaned containers
echo "Cleaning up..."
docker container prune -f

echo "✅ Development environment stopped!"