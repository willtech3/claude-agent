# Claude Agent Development Environment Setup Guide

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Initial Setup](#initial-setup)
3. [Component-Specific Setup](#component-specific-setup)
4. [Local AWS Services Setup](#local-aws-services-setup)
5. [Running the Application](#running-the-application)
6. [POC Implementation Stages](#poc-implementation-stages)
7. [Troubleshooting](#troubleshooting)
8. [Manual Tasks Checklist](#manual-tasks-checklist)

## Prerequisites

### Required Software
```bash
# Check if installed with these commands:
node --version          # Need: v20+ (LTS)
npm --version           # Need: v9+
python --version        # Need: Python 3.12+
docker --version        # Need: Docker 20+
docker-compose --version # Need: Docker Compose 2+
aws --version           # Need: AWS CLI v2
sam --version           # Need: SAM CLI 1.100+
gh --version            # Need: GitHub CLI (optional but recommended)
```

### Installation Instructions

#### macOS (using Homebrew)
```bash
# Install Homebrew if not present
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install prerequisites
brew install node@20
brew install python@3.12
brew install --cask docker
brew install awscli
brew install aws-sam-cli
brew install gh

# Install Python package manager
pip3 install uv
```

#### Linux (Ubuntu/Debian)
```bash
# Update package manager
sudo apt update

# Install Node.js (via NodeSource)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install Python 3.12
sudo apt install python3.12 python3.12-venv python3-pip

# Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
# Log out and back in for group changes

# Install AWS CLI v2
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Install SAM CLI
wget https://github.com/aws/aws-sam-cli/releases/latest/download/aws-sam-cli-linux-x86_64.zip
unzip aws-sam-cli-linux-x86_64.zip -d sam-installation
sudo ./sam-installation/install

# Install uv
pip3 install uv
```

#### Windows (using WSL2)
```powershell
# Install WSL2 first
wsl --install

# Then follow Linux instructions inside WSL2
```

### API Keys and Credentials

#### 1. Anthropic API Key (Required for Agent)
```bash
# Option A: Environment variable
export ANTHROPIC_API_KEY="sk-ant-..."

# Option B: Create config file
mkdir -p ~/.anthropic
echo "your-api-key" > ~/.anthropic/api_key
chmod 600 ~/.anthropic/api_key
```

#### 2. AWS Credentials (Required for deployment, optional for local)
```bash
# Configure AWS CLI
aws configure
# Enter:
# - AWS Access Key ID
# - AWS Secret Access Key
# - Default region (us-east-1 recommended)
# - Default output format (json)
```

#### 3. GitHub/GitLab Tokens (Required for provider functionality)
```bash
# GitHub Personal Access Token
# Go to: https://github.com/settings/tokens
# Create token with: repo, workflow, read:org permissions

# GitLab Personal Access Token
# Go to: https://gitlab.com/-/profile/personal_access_tokens
# Create token with: api, read_repository, write_repository scopes
```

## Initial Setup

### 1. Clone Repository
```bash
git clone https://github.com/your-org/claude-agent.git
cd claude-agent
```

### 2. Install Global Dependencies
```bash
# Install frontend dependencies
cd frontend
npm install

# Install backend dependencies
cd ../backend
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv sync

# Return to root
cd ..
```

### 3. Create Local Configuration Files
```bash
# Create .env.local for frontend
cat > frontend/.env.local << EOF
NEXT_PUBLIC_API_URL=http://localhost:3001
NEXT_PUBLIC_WS_URL=ws://localhost:3001
EOF

# Create .env for backend
cat > backend/.env << EOF
ENVIRONMENT=development
LOG_LEVEL=DEBUG
CORS_ORIGINS=["http://localhost:3000"]
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/claude_agent
REDIS_URL=redis://localhost:6379
SQS_QUEUE_URL=http://localhost:4566/000000000000/agent-tasks
AWS_ENDPOINT_URL=http://localhost:4566
EOF

# Create agent configuration
mkdir -p agent/config
cat > agent/config/auth.yaml << EOF
providers:
  anthropic:
    type: api_key
    location: environment
    env_var: ANTHROPIC_API_KEY
  bedrock:
    type: aws_credentials
    region: us-east-1
  vertex:
    type: gcp_credentials
    project_id: your-project-id
EOF
```

## Component-Specific Setup

### Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
# Frontend available at: http://localhost:3000

# Build for production
npm run build
npm run export  # Creates static files in 'out' directory
```

### Backend Setup (Lambda Functions)
```bash
cd backend

# Create Python virtual environment
uv venv
source .venv/bin/activate

# Install dependencies
uv sync

# Run SAM local API
sam local start-api --port 3001
# API available at: http://localhost:3001

# Alternative: Use Serverless Framework
npm install -g serverless
serverless offline --httpPort 3001
```

### Agent Setup (Docker)
```bash
cd agent

# Build Docker image
docker build -t claude-agent:local .

# Run with API key
docker run -it \
  -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
  -v $(pwd)/sessions:/sessions \
  claude-agent:local

# Run with mounted config
docker run -it \
  -v ~/.anthropic:/root/.anthropic:ro \
  -v $(pwd)/sessions:/sessions \
  claude-agent:local
```

## Local AWS Services Setup

### Using LocalStack
```bash
# Create docker-compose.local.yml
cat > docker-compose.local.yml << 'EOF'
version: '3.8'

services:
  localstack:
    image: localstack/localstack:latest
    ports:
      - "4566:4566"
    environment:
      - SERVICES=s3,sqs,dynamodb,lambda,apigateway,cloudfront
      - DEBUG=1
      - DATA_DIR=/tmp/localstack/data
    volumes:
      - "./tmp/localstack:/tmp/localstack"
      - "/var/run/docker.sock:/var/run/docker.sock"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes
    volumes:
      - "./tmp/redis:/data"

  postgres:
    image: postgres:15-alpine
    ports:
      - "5432:5432"
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: claude_agent
    volumes:
      - "./tmp/postgres:/var/lib/postgresql/data"
EOF

# Start local services
docker-compose -f docker-compose.local.yml up -d

# Wait for services to be ready
sleep 10

# Create local AWS resources
aws --endpoint-url=http://localhost:4566 s3 mb s3://claude-agent-artifacts
aws --endpoint-url=http://localhost:4566 sqs create-queue --queue-name agent-tasks
aws --endpoint-url=http://localhost:4566 dynamodb create-table \
  --table-name sessions \
  --attribute-definitions AttributeName=session_id,AttributeType=S \
  --key-schema AttributeName=session_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST
```

### Database Migrations
```bash
cd backend

# Run migrations
alembic upgrade head

# Create test data (optional)
python scripts/seed_data.py
```

## Running the Application

### Full Stack Development Mode
```bash
# Terminal 1: Start local AWS services
docker-compose -f docker-compose.local.yml up

# Terminal 2: Start backend API
cd backend
source .venv/bin/activate
sam local start-api --port 3001

# Terminal 3: Start frontend
cd frontend
npm run dev

# Terminal 4: Start agent (if testing agent functionality)
cd agent
docker run -it \
  -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
  -e SQS_QUEUE_URL=http://host.docker.internal:4566/000000000000/agent-tasks \
  -e AWS_ENDPOINT_URL=http://host.docker.internal:4566 \
  --network host \
  claude-agent:local
```

### Testing Individual Components

#### Frontend Only
```bash
cd frontend
npm run dev
# Use mock API responses (configured in next.config.js)
```

#### Backend Only
```bash
cd backend
sam local start-api --port 3001
# Test with curl or Postman
curl http://localhost:3001/health
```

#### Agent Only
```bash
cd agent
docker run -it -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY claude-agent:local
# Interactive testing without SQS integration
```

## POC Implementation Stages

### Stage 1: Basic Infrastructure ✅
**What Works:**
- LocalStack for S3, SQS, DynamoDB
- Basic Lambda functions via SAM
- Docker containers for agent

**What Doesn't Work:**
- Real AWS deployment
- Provider integrations
- WebSocket connections
- Authentication

**Manual Tasks:**
1. Set up LocalStack
2. Create S3 buckets manually
3. Create SQS queues manually
4. Configure environment variables

### Stage 2: Core Functionality 🚧
**What Works:**
- Basic API endpoints
- Simple agent execution
- File storage in S3
- Task queuing in SQS

**What Doesn't Work:**
- Real-time updates
- Complex agent operations
- Provider authentication
- Session persistence

**Manual Tasks:**
1. Configure API Gateway routes in SAM
2. Set up CORS headers
3. Create test GitHub/GitLab apps
4. Generate provider tokens

### Stage 3: Agent Integration 🔄
**What Works:**
- Agent wrapper functionality
- Basic Claude Code operations
- SQS message processing
- S3 artifact storage

**What Doesn't Work:**
- Advanced agent features
- Multi-model support
- Complex file operations
- Real-time streaming

**Manual Tasks:**
1. Build agent Docker image
2. Configure SQS polling
3. Set up S3 permissions
4. Create session directories

### Stage 4: Provider Abstraction 📋
**What Works:**
- GitHub basic operations
- GitLab basic operations
- Repository listing
- File reading

**What Doesn't Work:**
- Self-hosted GitLab
- Advanced Git operations
- PR/MR creation
- Webhooks

**Manual Tasks:**
1. Register OAuth apps
2. Configure callback URLs
3. Store provider credentials
4. Test each provider manually

### Stage 5: Production Readiness ❌
**Not Yet Implemented:**
- Real AWS deployment
- Auto-scaling
- Monitoring
- Security hardening
- Cost optimization

**Future Manual Tasks:**
1. Set up AWS accounts
2. Configure IAM roles
3. Set up CloudFront
4. Configure Route53
5. Set up monitoring

## Troubleshooting

### Common Issues and Solutions

#### Docker Issues
```bash
# Permission denied
sudo usermod -aG docker $USER
# Log out and back in

# Cannot connect to Docker daemon
sudo systemctl start docker

# Port already in use
lsof -i :3000  # Find process
kill -9 <PID>  # Kill process
```

#### Python/Node Issues
```bash
# Python version conflicts
pyenv install 3.12.0
pyenv local 3.12.0

# Node version conflicts
nvm install 20
nvm use 20

# Package conflicts
rm -rf node_modules package-lock.json
npm install
```

#### LocalStack Issues
```bash
# Services not starting
docker-compose -f docker-compose.local.yml logs localstack

# Reset LocalStack data
docker-compose -f docker-compose.local.yml down -v
rm -rf tmp/localstack
```

#### Agent Issues
```bash
# Claude Code not found
# Ensure claude-code is in requirements.txt
# Rebuild Docker image

# API key not working
# Check key format: sk-ant-...
# Verify key permissions

# Session errors
# Create sessions directory
mkdir -p agent/sessions
chmod 777 agent/sessions
```

## Manual Tasks Checklist

### Initial Setup
- [ ] Install all prerequisites
- [ ] Configure AWS CLI (even for local development)
- [ ] Create Anthropic API key
- [ ] Create GitHub/GitLab tokens
- [ ] Clone repository
- [ ] Create all .env files
- [ ] Create local directories (tmp/, sessions/)

### Before Each Development Session
- [ ] Start Docker Desktop (if on macOS/Windows)
- [ ] Pull latest code from main
- [ ] Update dependencies if needed
- [ ] Start LocalStack services
- [ ] Verify all services are running

### Testing Checklist
- [ ] Run frontend tests: `npm test`
- [ ] Run backend tests: `pytest`
- [ ] Test API endpoints manually
- [ ] Test agent Docker image
- [ ] Verify S3 uploads work
- [ ] Check SQS message flow

### Before Committing
- [ ] Run linters (frontend: `npm run lint`, backend: `ruff check`)
- [ ] Run formatters (frontend: `npm run format`, backend: `black .`)
- [ ] Update tests for new features
- [ ] Update documentation if needed
- [ ] Test full stack locally

### Deployment Preparation (Future)
- [ ] Build production frontend
- [ ] Package Lambda functions
- [ ] Build agent Docker image
- [ ] Tag all images appropriately
- [ ] Update infrastructure code
- [ ] Review security settings

## Notes for POC Development

1. **Start Small**: Focus on getting basic functionality working before adding complexity
2. **Use Mocks**: Mock external services during early development
3. **Document Issues**: Keep track of what doesn't work and why
4. **Iterate Quickly**: Don't aim for perfection in the POC
5. **Test Manually**: Automated testing can come after POC validation

## Support and Resources

- **LocalStack Dashboard**: http://localhost:4566/_localstack/health
- **SAM Local Logs**: `sam local start-api --debug`
- **Docker Logs**: `docker logs <container-id>`
- **Frontend Dev Tools**: React Developer Tools browser extension
- **Backend API Docs**: http://localhost:3001/docs (when running)

---

Remember: This is a POC implementation. Many production features are intentionally simplified or omitted. Focus on demonstrating core functionality rather than building a production-ready system.