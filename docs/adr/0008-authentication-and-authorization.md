# 8. Authentication and Authorization

Date: 2025-01-04

## Status

Accepted

## Context

The system needs to:
- Authenticate users securely
- Authorize access to resources
- Support multiple authentication methods
- Integrate with git providers (OAuth)
- Manage API keys for AI providers
- Handle service-to-service authentication

Security requirements:
- No credentials in code
- Encrypted storage of secrets
- Token rotation capability
- Audit logging

## Decision

### User Authentication
- **Primary**: OAuth 2.0 with git providers (GitHub, GitLab)
- **JWT tokens** for session management
- **Refresh tokens** stored in Redis
- **MFA** optional via provider

### Authorization Model
```
User → Projects → Resources
         ↓
      Permissions
    (read, write, admin)
```

### Secret Management
- **AWS Secrets Manager** for all secrets
- **IAM roles** for service authentication
- **Temporary credentials** via STS when possible

### API Authentication
```python
# Headers required
Authorization: Bearer <jwt_token>
X-API-Version: 1.0

# Service-to-service
X-Service-Token: <service_jwt>
```

### Git Provider Integration
- OAuth apps for each provider
- Encrypted token storage per user
- Token refresh handled automatically

## Consequences

**Positive:**
- Industry standard OAuth flow
- No password management required
- Centralized secret management
- Audit trail for compliance
- Scalable permission model
- Secure by default

**Negative:**
- Complex OAuth implementation
- Dependency on git providers
- Token refresh complexity
- AWS Secrets Manager costs
- Additional latency for secret retrieval