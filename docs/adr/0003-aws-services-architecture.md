# 3. AWS Services Architecture

Date: 2025-01-04

## Status

Accepted

## Context

We need to design a cloud architecture that:
- Scales automatically based on demand
- Minimizes costs during low usage
- Provides high availability
- Supports async task processing
- Enables real-time updates to clients
- Securely stores artifacts and data

The system must handle:
- Web traffic (frontend)
- API requests (backend)
- Long-running AI agent tasks
- File storage for generated artifacts
- Real-time status updates

## Decision

We will use the following AWS services architecture:

### Frontend Hosting
- **S3**: Static website hosting
- **CloudFront**: CDN for global distribution
- **Route 53**: DNS management

### API Layer
- **API Gateway**: HTTP API for Lambda
- **Lambda**: Serverless compute for API
- **API Gateway WebSockets**: Real-time updates

### Task Processing
- **SQS**: Queue for async tasks
- **ECS Fargate**: Container hosting for AI agent
- **ECR**: Container registry

### Storage
- **RDS PostgreSQL**: Primary database
- **ElastiCache Redis**: Caching and sessions
- **S3**: Artifact storage
- **DynamoDB**: Session state (optional)

### Security & Monitoring
- **Secrets Manager**: API keys and secrets
- **CloudWatch**: Logs and metrics
- **X-Ray**: Distributed tracing
- **IAM**: Fine-grained permissions

### AI Providers
- **Bedrock**: Native AWS AI service
- **Direct API**: Anthropic Claude API
- **Vertex AI**: Google Cloud integration

## Architecture Flow

```
User → CloudFront → S3 (Frontend)
         ↓
    API Gateway → Lambda → SQS → ECS (Agent)
         ↓           ↓             ↓
    WebSocket    RDS/Redis    S3 (Artifacts)
```

## Consequences

**Positive:**
- Serverless components reduce operational overhead
- Auto-scaling built into most services
- Pay-per-use pricing model
- High availability by default
- Native AWS service integration
- Strong security boundaries

**Negative:**
- Vendor lock-in to AWS
- Cold starts for Lambda functions
- Complexity of distributed system
- Requires AWS expertise
- Potential for unexpected costs
- ECS Fargate more expensive than EC2