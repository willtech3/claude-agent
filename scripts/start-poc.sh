#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting Claude Agent POC Services...${NC}"

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Error: docker-compose not found. Please install Docker and docker-compose.${NC}"
    exit 1
fi

# Check if we're in the project root
if [ ! -f "docker-compose.local.yml" ]; then
    echo -e "${RED}Error: docker-compose.local.yml not found. Please run this script from the project root.${NC}"
    exit 1
fi

# Stop any existing services
echo -e "${YELLOW}Stopping any existing services...${NC}"
docker-compose -f docker-compose.local.yml down

# Start infrastructure services
echo -e "${GREEN}Starting infrastructure services...${NC}"
docker-compose -f docker-compose.local.yml up -d

# Wait for services to be ready
echo -e "${YELLOW}Waiting for services to be healthy...${NC}"
sleep 5

# Check service health
echo -e "${GREEN}Checking service health...${NC}"

# Check Redis
echo -n "Redis: "
if docker-compose -f docker-compose.local.yml exec -T redis redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
    echo -e "${RED}Redis is not responding. Check logs with: docker-compose logs redis${NC}"
fi

# Check PostgreSQL
echo -n "PostgreSQL: "
if docker-compose -f docker-compose.local.yml exec -T postgres pg_isready -U postgres > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
    echo -e "${RED}PostgreSQL is not responding. Check logs with: docker-compose logs postgres${NC}"
fi

# Check LocalStack
echo -n "LocalStack: "
if curl -s http://localhost:4566/_localstack/health | grep -q "\"sqs\": \"available\""; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
    echo -e "${RED}LocalStack is not responding. Check logs with: docker-compose logs localstack${NC}"
fi

# Create SQS queue if it doesn't exist
echo -e "${YELLOW}Setting up SQS queue...${NC}"
aws --endpoint-url=http://localhost:4566 sqs create-queue --queue-name tasks 2>/dev/null || echo "Queue already exists"

# Check if backend is running
echo -e "${YELLOW}Checking backend API...${NC}"
if [ -f "backend/template.yaml" ]; then
    echo -e "${GREEN}Backend SAM template found.${NC}"
    echo -e "${YELLOW}To start the backend API, run:${NC}"
    echo -e "  cd backend && sam local start-api"
elif [ -f "backend/serverless.yml" ]; then
    echo -e "${GREEN}Backend Serverless template found.${NC}"
    echo -e "${YELLOW}To start the backend API, run:${NC}"
    echo -e "  cd backend && serverless offline"
else
    echo -e "${YELLOW}Backend API configuration not found. You may need to run:${NC}"
    echo -e "  cd backend && uvicorn app.main:app --reload"
fi

# Check if frontend exists
echo -e "${YELLOW}Checking frontend...${NC}"
if [ -f "frontend/package.json" ]; then
    echo -e "${GREEN}Frontend found.${NC}"
    echo -e "${YELLOW}To start the frontend, run:${NC}"
    echo -e "  cd frontend && npm run dev"
else
    echo -e "${RED}Frontend not found at frontend/package.json${NC}"
fi

# Check if agent exists
echo -e "${YELLOW}Checking agent...${NC}"
if [ -f "agent/Dockerfile" ]; then
    echo -e "${GREEN}Agent Dockerfile found.${NC}"
    echo -e "${YELLOW}To build and run the agent, run:${NC}"
    echo -e "  cd agent && docker build -t claude-agent . && docker run -it claude-agent"
else
    echo -e "${RED}Agent Dockerfile not found at agent/Dockerfile${NC}"
fi

echo -e "${GREEN}Infrastructure services are running!${NC}"
echo -e "${YELLOW}Service URLs:${NC}"
echo -e "  LocalStack: http://localhost:4566"
echo -e "  Redis: localhost:6379"
echo -e "  PostgreSQL: localhost:5432 (user: postgres, password: postgres)"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo -e "1. Start the backend API (see above)"
echo -e "2. Start the frontend (see above)"
echo -e "3. Build and run the agent (see above)"
echo ""
echo -e "${YELLOW}To view logs:${NC}"
echo -e "  docker-compose -f docker-compose.local.yml logs -f"
echo ""
echo -e "${YELLOW}To stop all services:${NC}"
echo -e "  docker-compose -f docker-compose.local.yml down"