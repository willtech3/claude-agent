# 6. Deployment Strategy

Date: 2025-01-04

## Status

Accepted

## Context

We need a deployment strategy that:
- Supports multiple environments (dev, staging, prod)
- Enables continuous deployment
- Minimizes downtime
- Allows rollback capabilities
- Handles infrastructure and application deployment
- Works with our monorepo structure

Key considerations:
- Frontend is static and can be deployed to CDN
- Backend is serverless (Lambda)
- Agent runs in containers (ECS)
- Infrastructure changes less frequently than code

## Decision

### Environment Strategy
- **Development**: Deployed on every commit to main
- **Staging**: Deployed on tag creation (v*.*.0-rc*)
- **Production**: Deployed on stable tags (v*.*.*)

### CI/CD Pipeline (GitHub Actions)
```yaml
1. On Push:
   - Run tests for changed components
   - Build affected packages
   - Deploy to dev (if main branch)

2. On Tag:
   - Full test suite
   - Build all components
   - Deploy to staging/prod based on tag
```

### Component Deployment

#### Frontend
1. Build static assets with Next.js
2. Upload to S3 bucket
3. Invalidate CloudFront cache

#### Backend
1. Build Lambda function with SAM
2. Deploy using SAM CLI
3. Update API Gateway

#### Agent
1. Build Docker image
2. Push to ECR
3. Update ECS task definition
4. Rolling deployment on ECS

#### Infrastructure
1. Terraform plan on PR
2. Manual approval required
3. Terraform apply on merge

### Rollback Strategy
- Frontend: Revert S3 objects to previous version
- Backend: Lambda alias pointing to previous version
- Agent: ECS blue/green deployment
- Infrastructure: Terraform state versioning

## Consequences

**Positive:**
- Automated deployment reduces human error
- Clear environment progression
- Component independence allows partial deployments
- Infrastructure as code ensures reproducibility
- Rollback capabilities for each component

**Negative:**
- Complex pipeline configuration
- Multiple deployment tools (SAM, Terraform, AWS CLI)
- Potential for environment drift
- Requires careful secret management
- Initial setup complexity