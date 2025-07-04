# Architecture Decision Records

This directory contains Architecture Decision Records (ADRs) for the Claude Agent project.

## What is an ADR?

An Architecture Decision Record captures an important architectural decision made along with its context and consequences.

## ADR Index

| ADR | Title | Status | Date |
|-----|-------|--------|------|
| [0000](./0000-use-architecture-decision-records.md) | Use Architecture Decision Records | Accepted | 2025-01-04 |
| [0001](./0001-use-monorepo-structure.md) | Use Monorepo Structure | Accepted | 2025-01-04 |
| [0002](./0002-technology-stack-selection.md) | Technology Stack Selection | Accepted | 2025-01-04 |
| [0003](./0003-aws-services-architecture.md) | AWS Services Architecture | Accepted | 2025-01-04 |
| [0004](./0004-package-management-strategy.md) | Package Management Strategy | Accepted | 2025-01-04 |
| [0005](./0005-provider-abstraction-pattern.md) | Provider Abstraction Pattern | Accepted | 2025-01-04 |
| [0006](./0006-deployment-strategy.md) | Deployment Strategy | Accepted | 2025-01-04 |
| [0007](./0007-agent-wrapper-approach.md) | Agent Wrapper Approach | Accepted (Temporary) | 2025-01-04 |
| [0008](./0008-authentication-and-authorization.md) | Authentication and Authorization | Accepted | 2025-01-04 |
| [0009](./0009-event-driven-architecture.md) | Event-Driven Architecture | Accepted | 2025-01-04 |

## Creating a New ADR

1. Copy the [template](./template.md)
2. Name it `NNNN-title-with-dashes.md` where NNNN is the next number
3. Fill in the sections
4. Update this README with the new entry

## ADR Status Types

- **Proposed**: Decision under discussion
- **Accepted**: Decision approved and implemented/being implemented
- **Deprecated**: Decision no longer relevant but kept for history
- **Superseded**: Decision replaced by another ADR (link to new one)

## Key Architectural Decisions Summary

### Core Architecture
- **Monorepo** structure for code organization
- **Event-driven** architecture for async processing
- **Provider abstraction** for multi-platform support

### Technology Choices
- **Next.js** for frontend (static export)
- **FastAPI** for backend (serverless)
- **Claude Code CLI** wrapped for agent (temporary)

### Infrastructure
- **AWS** as primary cloud provider
- **Serverless** where possible (Lambda, Fargate)
- **SQS** for task queue
- **S3/CloudFront** for frontend hosting

### Development
- **npm workspaces** for JavaScript packages
- **uv** for Python package management
- **GitHub Actions** for CI/CD