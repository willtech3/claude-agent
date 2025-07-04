# Claude Development Guidelines for Claude Agent - Core Document

## 🧠 Context Management
**For long conversations, review this document:**
- Before starting any new epic or issue
- When switching between layers (frontend/backend/infrastructure)
- If you feel context drifting (~3000 tokens)
- Before any git operations or deployments
- When implementing provider abstractions

## 🚨 CRITICAL RULES - NEVER VIOLATE

1. **🔐 NEVER commit secrets** - No API keys, tokens, or `.env` files
2. **📁 NEVER use `git add .`** - Always specify files explicitly
3. **☁️ ALWAYS support multiple AI providers** - Bedrock, Vertex AI, API keys
4. **🔌 ALWAYS use provider abstraction** - No direct GitHub/GitLab API calls
5. **📝 ALWAYS explain changes** - Clear commit messages and PR descriptions
6. **🚀 ALWAYS use CI for deployment** - Never deploy manually
7. **🌿 ALWAYS use feature branches** - Never commit directly to main
8. **🔄 ALWAYS create pull requests** - All changes go through PR review
9. **📖 ALWAYS follow architecture** - Respect layer boundaries

## 🏗️ Architecture Constraints (IMMUTABLE)

### Fixed Component Structure
```
frontend/                      # Next.js static site (S3/CloudFront)
backend/                       # FastAPI Lambda functions
agent/                        # Custom AI Agent (ECS Fargate)
infrastructure/               # Terraform/CDK for AWS
shared/                       # Shared types and schemas
```

### AWS Service Architecture
```
Frontend (S3) → CloudFront → API Gateway → Lambda (API)
                                ↓
                               SQS
                                ↓
                     ECS (Custom Agent) → S3 (Artifacts)
                                ↓
                    ElastiCache (Redis) / RDS (PostgreSQL)
                                ↓
        AWS Bedrock / Vertex AI / Anthropic API
```

### Provider Abstraction Rules
```python
# ✅ CORRECT
from app.core.providers import GitProvider
provider = get_provider(config.provider_type)

# ❌ WRONG - Direct API usage
from github import Github
github = Github(token)
```

### Quick Validation
```bash
pwd                           # Should be in project root
sam local start-api          # Lambda API running locally
docker ps                    # Agent container running
git branch                   # Should NOT be on main
npm test                     # Frontend tests passing
pytest                       # Backend tests passing
aws s3 ls                    # AWS CLI configured
```

## 📖 Documentation Hierarchy

**CLAUDE.md files are co-located with their components:**

```
/CLAUDE.md                    # Root - Core rules (this file)
├── frontend/
│   └── CLAUDE.md            # Frontend guidelines
├── backend/
│   ├── CLAUDE.md            # Backend guidelines
│   └── app/
│       ├── agent/
│       │   └── CLAUDE.md    # Agent-specific rules
│       └── providers/
│           └── CLAUDE.md    # Provider abstraction rules
├── infrastructure/
│   └── CLAUDE.md            # Infrastructure guidelines
└── .github/
    └── CLAUDE.md            # CI/CD guidelines
```

### Reading Order (MANDATORY)
1. **Always start with root CLAUDE.md** (this file) - contains critical rules
2. **Read component-specific CLAUDE.md** for your work area
3. **Consult CLOUD_TRANSFORMATION_PLAN.md** for epic context

## 🔄 Common Workflows

### Starting ANY Work
```bash
cd claude-agent
git pull origin main
git checkout -b feature/issue-XX-description  # Use issue number

# Start local AWS services
docker-compose -f docker-compose.local.yml up -d  # LocalStack, Redis, Postgres

# Agent development
cd agent && docker build -t claude-agent .
docker run -it claude-agent

# API development  
cd backend && sam local start-api
# OR
cd backend && serverless offline
```

### Working on Frontend
```bash
cd frontend
npm install                    # If package.json changed
npm run dev                    # Hot reload at localhost:3000
npm run test:watch            # TDD mode
npm run build                 # Static build for S3
npm run lint                  # Before commits
```

### Working on Backend (Lambda)
```bash
cd backend
uv sync                       # If pyproject.toml changed
sam local start-api           # Local Lambda environment
pytest tests/ -v              # Run tests
ruff check .                  # Lint code

# Test Lambda locally
sam local invoke FunctionName -e events/test.json
```

### Working on Agent (ECS)
```bash
cd agent
docker build -t claude-agent:local .

# Run with Anthropic API key
docker run -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
  -v $(pwd)/sessions:/sessions \
  claude-agent:local

# Run with mounted credentials
docker run -v ~/.anthropic:/root/.anthropic:ro \
  -v $(pwd)/sessions:/sessions \
  claude-agent:local

# Test with local SQS
docker run -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
  -e SQS_QUEUE_URL=http://localstack:4566/queue/tasks \
  -e AWS_ENDPOINT_URL=http://localstack:4566 \
  claude-agent:local
```

### Before ANY Commit
```bash
# Run quality checks based on what you modified
./scripts/check-quality.sh    # Must pass

# Add specific files only
git add frontend/src/specific/file.tsx backend/app/specific/file.py

# Commit with conventional message
git commit -m "feat(scope): implement feature X for issue #XX"
```

### Creating a Pull Request
```bash
# Push feature branch
git push origin feature/issue-XX-description

# Create PR linking to issue
gh pr create --title "feat: description" --body "Closes #XX"

# Let CI handle deployment - NEVER deploy manually
```

## 🎯 Current Epic Tracking

When working on epics, maintain context:
```python
# CURRENT EPIC: Epic 2 - Agent Enhancement
# CURRENT ISSUE: #19 - Autonomous Agent Architecture
# STATUS: Implementing planning system
# NEXT: Create execution engine
# BLOCKERS: None
```

## 🚦 Go/No-Go Checklist

Before implementing ANYTHING:
- [ ] Have I read the relevant epic and issue?
- [ ] Am I on a feature branch (not main)?
- [ ] Is local development environment running?
- [ ] Am I using provider abstraction (not direct APIs)?
- [ ] Have I read the relevant CLAUDE.md files?
- [ ] Is my approach aligned with Jules design principles?
- [ ] Am I using appropriate AWS services (Lambda/ECS)?

## 🔍 Architecture Quick Reference

### Frontend Structure (Jules-Inspired)
```
frontend/
├── components/       # Reusable UI components
├── features/        # Feature-specific components
├── lib/            # Utilities and helpers
├── styles/         # Global styles and design tokens
└── pages/          # Next.js pages
```

### Backend Structure (Lambda)
```
backend/
├── app/
│   ├── api/           # API endpoints
│   ├── core/          # Core functionality
│   ├── providers/     # Git provider implementations
│   └── models/        # Data models
├── lambda_handler.py  # Lambda entry point
├── template.yaml      # SAM template
└── requirements.txt
```

### Agent Structure (ECS)
```
agent/
├── wrapper/
│   ├── main.py            # Entry point
│   ├── claude_code.py     # Claude Code wrapper
│   ├── event_parser.py    # Output parsing
│   ├── session.py         # Session management
│   └── sqs_handler.py     # Queue integration
├── config/
│   └── auth.yaml          # Auth configuration
├── Dockerfile             # FROM python:3.12
└── requirements.txt       # claude-code, boto3, etc.
```

### Event Flow Architecture
```
User Request → API Gateway → Lambda → SQS → ECS Agent
                                ↓             ↓
                          DynamoDB      S3 (artifacts)
                                ↓             ↓
                    WebSocket ← Lambda ← SQS Events
```

**Red Flags:**
- Direct GitHub/GitLab API usage
- Hardcoded provider logic
- Missing provider abstraction
- Synchronous agent operations
- Missing event streaming
- UI not following Jules patterns
- Tests are hardcoded to pass or don't test behavior but only test setup

## 🆘 When Stuck

1. Check: Are local AWS services running (LocalStack)?
2. Check: Is SAM/Serverless configured correctly?
3. Check: Am I following provider abstraction?
4. Check: Are SQS messages flowing to ECS?
5. Check: Is my UI Jules-compliant?
6. Check: Are my tests actually testing behavior?
7. Review: Relevant epic and issues

If still stuck: Check AWS service logs and existing patterns

## 📝 Memory Aid

**C.L.A.U.D.E.**
- **C**loud-native AWS services (ECS/Lambda)
- **L**ayer boundaries respected
- **A**bstraction for providers
- **U**I follows Jules patterns
- **D**evelopment test-driven
- **E**vents via SQS and WebSockets

## 🔗 Key Resources

- **Epics**: See issues #13, #18, #24, #30
- **Design**: Jules-inspired, minimal, focused
- **Providers**: GitHub, GitLab (self-hosted too)
- **Stack**: 
  - Frontend: Next.js (S3/CloudFront)
  - API: FastAPI on Lambda
  - Agent: Python on ECS Fargate
  - Storage: RDS, ElastiCache, S3
  - Queue: SQS for async tasks
- **Agent**: Claude Code CLI (containerized for POC)
- **Approach**: Wrapper for rapid development, SDK migration planned
- **Future**: See SDK_MIGRATION_PLAN.md for roadmap

---

**Remember:** This document contains ONLY the essential rules. For detailed guidance on specific components, always consult the appropriate CLAUDE.md file in the relevant directory. Reference CLOUD_TRANSFORMATION_PLAN.md for overall project vision and epic details.