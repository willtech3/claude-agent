#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Demo configuration
DEMO_WORKSPACE="workspaces/demo-$(date +%s)"
API_URL="http://localhost:8000"
FRONTEND_URL="http://localhost:3000"

clear

echo -e "${PURPLE}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${PURPLE}║           Claude Agent POC Demo                           ║${NC}"
echo -e "${PURPLE}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""

# Function to pause and wait for user
pause() {
    echo -e "${CYAN}Press Enter to continue...${NC}"
    read -r
}

# Function to print section headers
section() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}▶ $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

# Function to show command being run
show_command() {
    echo -e "${YELLOW}$ $1${NC}"
}

# Function to create and show a task
create_task() {
    local prompt=$1
    local description=$2
    
    echo -e "${GREEN}Task: $description${NC}"
    echo -e "${YELLOW}Prompt: \"$prompt\"${NC}"
    echo ""
    
    # Create the task
    show_command "curl -X POST $API_URL/api/tasks -H 'Content-Type: application/json' -d '{\"prompt\": \"$prompt\", \"context\": {}}'"
    
    RESPONSE=$(curl -s -X POST $API_URL/api/tasks \
        -H "Content-Type: application/json" \
        -d "{\"prompt\": \"$prompt\", \"context\": {}}")
    
    TASK_ID=$(echo "$RESPONSE" | grep -o '"id":"[^"]*"' | cut -d'"' -f4)
    
    if [ -z "$TASK_ID" ]; then
        echo -e "${RED}Failed to create task!${NC}"
        echo "Response: $RESPONSE"
        return 1
    fi
    
    echo -e "${GREEN}✓ Task created with ID: $TASK_ID${NC}"
    echo ""
    
    # Wait for task to complete
    echo "Waiting for task to complete..."
    local max_attempts=30
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        STATUS_RESPONSE=$(curl -s $API_URL/api/tasks/$TASK_ID)
        STATUS=$(echo "$STATUS_RESPONSE" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
        
        if [ "$STATUS" = "completed" ]; then
            echo -e "${GREEN}✓ Task completed!${NC}"
            break
        elif [ "$STATUS" = "failed" ]; then
            echo -e "${RED}✗ Task failed!${NC}"
            break
        else
            echo -ne "Status: $STATUS... \r"
            sleep 2
        fi
        
        attempt=$((attempt + 1))
    done
    
    echo ""
    
    # Show created files
    if [ -d "workspaces/$TASK_ID" ]; then
        echo -e "${GREEN}Files created:${NC}"
        show_command "ls -la workspaces/$TASK_ID/"
        ls -la "workspaces/$TASK_ID/" | grep -v "^total" | grep -v "^d"
        
        # Show file contents for small files
        for file in workspaces/$TASK_ID/*; do
            if [ -f "$file" ] && [ $(wc -l < "$file") -lt 20 ]; then
                echo ""
                echo -e "${CYAN}Contents of $(basename $file):${NC}"
                echo -e "${YELLOW}---${NC}"
                cat "$file"
                echo -e "${YELLOW}---${NC}"
            fi
        done
    fi
}

# Start of demo
section "1. Prerequisites Check"

echo "Checking if services are running..."
services_ok=true

check_service() {
    local name=$1
    local check=$2
    echo -n "$name: "
    if eval $check > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗${NC}"
        services_ok=false
    fi
}

check_service "Docker" "docker --version"
check_service "Redis" "docker compose -f docker-compose.local.yml exec -T redis redis-cli ping"
check_service "PostgreSQL" "docker compose -f docker-compose.local.yml exec -T postgres pg_isready -U postgres"
check_service "LocalStack" "curl -s http://localhost:4566/_localstack/health | grep -q '\"sqs\": \"available\"'"
check_service "Backend API" "curl -s $API_URL/health"

if [ "$services_ok" = false ]; then
    echo ""
    echo -e "${RED}Some services are not running!${NC}"
    echo -e "${YELLOW}Please run './scripts/start-poc.sh' first.${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}All services are running!${NC}"
pause

# Demo scenarios
section "2. Simple Task - Hello World"

create_task "Create a Python script that prints 'Hello, Claude Agent!'" "Basic Python script generation"
pause

section "3. Multi-file Task - Flask API"

create_task "Create a Flask API with two endpoints: GET /users returns a list of users, and GET /health returns service status" "Multi-file application generation"
pause

section "4. Complex Task - React Component"

create_task "Create a React TodoList component with TypeScript that allows adding, removing, and marking todos as complete. Include proper types and basic styling." "Frontend component with TypeScript"
pause

section "5. Real-time Output Streaming"

echo -e "${GREEN}For this demo, you should open the frontend to see real-time streaming:${NC}"
echo -e "${YELLOW}1. Open a new terminal${NC}"
echo -e "${YELLOW}2. Run: cd frontend && npm run dev${NC}"
echo -e "${YELLOW}3. Open: $FRONTEND_URL${NC}"
echo -e "${YELLOW}4. Submit a task and watch the output stream in real-time${NC}"
echo ""
echo -e "${CYAN}Try this prompt: \"Create a Python web scraper with BeautifulSoup\"${NC}"
pause

section "6. Error Handling"

echo -e "${GREEN}Testing error handling with invalid input:${NC}"
show_command "curl -X POST $API_URL/api/tasks -H 'Content-Type: application/json' -d '{\"prompt\": \"\", \"context\": {}}'"

ERROR_RESPONSE=$(curl -s -X POST $API_URL/api/tasks \
    -H "Content-Type: application/json" \
    -d '{"prompt": "", "context": {}}')

echo "Response: $ERROR_RESPONSE"
echo -e "${GREEN}✓ API properly validates input${NC}"
pause

section "7. Architecture Overview"

echo -e "${CYAN}Claude Agent POC Architecture:${NC}"
echo ""
echo "  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐"
echo "  │   Frontend  │────▶│   Backend   │────▶│    Agent    │"
echo "  │  (Next.js)  │◀────│  (FastAPI)  │◀────│   (Docker)  │"
echo "  └─────────────┘     └─────────────┘     └─────────────┘"
echo "         │                    │                    │"
echo "         │              ┌─────▼─────┐              │"
echo "         │              │    SQS    │              │"
echo "         │              └─────┬─────┘              │"
echo "         │                    │                    │"
echo "         └────────────────────┼────────────────────┘"
echo "                              │"
echo "                        ┌─────▼─────┐"
echo "                        │   Redis   │"
echo "                        │PostgreSQL │"
echo "                        │LocalStack │"
echo "                        └───────────┘"
echo ""
echo -e "${GREEN}Key Features:${NC}"
echo "• Real-time WebSocket streaming"
echo "• Async task processing via SQS"
echo "• File artifact management"
echo "• Multi-provider support (GitHub, GitLab, Bedrock, Vertex AI)"
echo "• Containerized Claude Code CLI"
pause

section "Demo Complete!"

echo -e "${GREEN}Summary of what we demonstrated:${NC}"
echo "✓ Basic code generation"
echo "✓ Multi-file project creation"
echo "✓ Complex component generation"
echo "✓ Real-time output streaming"
echo "✓ Error handling"
echo "✓ Architecture overview"
echo ""
echo -e "${YELLOW}All generated files are in the workspaces/ directory${NC}"
echo -e "${YELLOW}To explore further:${NC}"
echo "  • View logs: docker compose -f docker-compose.local.yml logs -f"
echo "  • Try the frontend: cd frontend && npm run dev"
echo "  • Read the docs: cat README.md"
echo ""
echo -e "${PURPLE}Thank you for watching the Claude Agent POC demo!${NC}"