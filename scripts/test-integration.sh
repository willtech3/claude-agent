#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Running Claude Agent POC Integration Tests${NC}"
echo "================================================"

# Check if services are running
echo -e "${YELLOW}Checking if services are running...${NC}"

# Function to check if a service is accessible
check_service() {
    local service_name=$1
    local check_command=$2
    
    echo -n "$service_name: "
    if eval $check_command > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
        return 0
    else
        echo -e "${RED}✗${NC}"
        return 1
    fi
}

# Check each service
services_ok=true

check_service "Redis" "docker-compose -f docker-compose.local.yml exec -T redis redis-cli ping" || services_ok=false
check_service "PostgreSQL" "docker-compose -f docker-compose.local.yml exec -T postgres pg_isready -U postgres" || services_ok=false
check_service "LocalStack" "curl -s http://localhost:4566/_localstack/health | grep -q '\"sqs\": \"available\"'" || services_ok=false
check_service "Backend API" "curl -s http://localhost:8000/health" || services_ok=false

if [ "$services_ok" = false ]; then
    echo -e "${RED}Some services are not running!${NC}"
    echo -e "${YELLOW}Please run './scripts/start-poc.sh' first and ensure all services are up.${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}All services are running!${NC}"
echo ""

# Run different test scenarios
run_test_scenario() {
    local scenario_name=$1
    local test_command=$2
    
    echo -e "${BLUE}Running: $scenario_name${NC}"
    echo "----------------------------------------"
    
    if eval $test_command; then
        echo -e "${GREEN}✓ $scenario_name passed${NC}"
    else
        echo -e "${RED}✗ $scenario_name failed${NC}"
        return 1
    fi
    echo ""
}

# Test 1: Basic connectivity
run_test_scenario "Basic API Health Check" \
    "curl -s http://localhost:8000/health | grep -q '\"status\":\"healthy\"'"

# Test 2: Create a simple task via API
echo -e "${BLUE}Test 2: Creating a simple task${NC}"
echo "----------------------------------------"
TASK_RESPONSE=$(curl -s -X POST http://localhost:8000/api/tasks \
    -H "Content-Type: application/json" \
    -d '{"prompt": "Create a Python hello world script", "context": {}}' 2>/dev/null || echo '{"error": "Failed to create task"}')

if echo "$TASK_RESPONSE" | grep -q '"id"'; then
    TASK_ID=$(echo "$TASK_RESPONSE" | grep -o '"id":"[^"]*"' | cut -d'"' -f4)
    echo -e "${GREEN}✓ Task created with ID: $TASK_ID${NC}"
    
    # Wait a bit for processing
    echo "Waiting for task to process..."
    sleep 5
    
    # Check task status
    STATUS_RESPONSE=$(curl -s http://localhost:8000/api/tasks/$TASK_ID)
    echo "Task status: $(echo "$STATUS_RESPONSE" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)"
else
    echo -e "${RED}✗ Failed to create task${NC}"
    echo "Response: $TASK_RESPONSE"
fi
echo ""

# Test 3: Check WebSocket connectivity (if frontend is running)
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo -e "${BLUE}Test 3: Frontend accessibility${NC}"
    echo "----------------------------------------"
    echo -e "${GREEN}✓ Frontend is accessible at http://localhost:3000${NC}"
else
    echo -e "${YELLOW}Frontend is not running. Start it with: cd frontend && npm run dev${NC}"
fi
echo ""

# Test 4: Check workspaces directory
echo -e "${BLUE}Test 4: Workspace management${NC}"
echo "----------------------------------------"
if [ -d "workspaces" ]; then
    WORKSPACE_COUNT=$(ls -1 workspaces 2>/dev/null | wc -l)
    echo -e "${GREEN}✓ Workspaces directory exists (contains $WORKSPACE_COUNT items)${NC}"
else
    echo -e "${YELLOW}Creating workspaces directory...${NC}"
    mkdir -p workspaces
    echo -e "${GREEN}✓ Workspaces directory created${NC}"
fi
echo ""

# Summary
echo -e "${BLUE}Integration Test Summary${NC}"
echo "================================================"
echo -e "${GREEN}Basic infrastructure: ✓${NC}"
echo -e "${GREEN}API connectivity: ✓${NC}"
if [ "$TASK_ID" != "" ]; then
    echo -e "${GREEN}Task creation: ✓${NC}"
else
    echo -e "${RED}Task creation: ✗${NC}"
fi

echo ""
echo -e "${YELLOW}To run full Python integration tests:${NC}"
echo "  pip install pytest requests websocket-client"
echo "  pytest tests/integration/test_poc_integration.py -v"

echo ""
echo -e "${YELLOW}To view service logs:${NC}"
echo "  docker-compose -f docker-compose.local.yml logs -f"

echo ""
echo -e "${YELLOW}To debug a specific service:${NC}"
echo "  docker-compose -f docker-compose.local.yml logs <service-name>"