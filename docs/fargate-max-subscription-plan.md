# AWS Fargate Plan for Claude Agent with Max Subscription

## Overview

This document outlines how to use AWS Fargate for secure AI code execution while leveraging your existing Claude Max ($200/month) subscription instead of requiring separate API keys.

## Key Insight

Your `~/.claude/credentials.json` file contains a portable session token that can be used in any environment, including AWS Fargate containers. This allows you to:
- Use your existing Max subscription (20x usage of Pro)
- Get true VM-level isolation via Fargate
- Avoid additional API costs

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌──────────────────┐
│   Local CLI     │────▶│   S3 Bucket     │────▶│  Fargate Task    │
│ (credentials)   │     │ (encrypted)     │     │  (isolated VM)   │
└─────────────────┘     └─────────────────┘     └──────────────────┘
                                                          │
                                                          ▼
                                                 ┌──────────────────┐
                                                 │   Claude Code    │
                                                 │ (Max subscription)│
                                                 └──────────────────┘
```

## Implementation Options

### Option 1: S3-Based Credential Management (Recommended)

**Pros**: Secure, easy to update, works across regions
**Cons**: Requires S3 permissions, slight startup delay

1. **Local Setup**:
   ```bash
   # Create S3 bucket for credentials
   aws s3 mb s3://my-claude-agent-creds
   
   # Upload encrypted credentials
   aws s3 cp ~/.claude/credentials.json \
     s3://my-claude-agent-creds/credentials.json \
     --sse --acl private
   ```

2. **Fargate Container Startup**:
   ```bash
   # In entrypoint.sh
   mkdir -p ~/.claude
   aws s3 cp s3://my-claude-agent-creds/credentials.json ~/.claude/
   chmod 600 ~/.claude/credentials.json
   ```

### Option 2: AWS Secrets Manager

**Pros**: Better for teams, automatic rotation possible
**Cons**: More complex, higher cost (~$0.40/month)

```bash
# Store credentials
SESSION_JSON=$(cat ~/.claude/credentials.json)
aws secretsmanager create-secret \
  --name claude-agent/session \
  --secret-string "$SESSION_JSON"

# In Fargate task definition
"secrets": [{
  "name": "CLAUDE_CREDENTIALS",
  "valueFrom": "arn:aws:secretsmanager:region:account:secret:claude-agent/session"
}]
```

### Option 3: Build into Docker Image

**Pros**: Fastest startup, no runtime dependencies
**Cons**: Less secure, requires rebuild for updates

```dockerfile
# In Dockerfile
COPY --chown=claude:claude credentials.json /home/claude/.claude/credentials.json
RUN chmod 600 /home/claude/.claude/credentials.json
```

## Modified Fargate Task Definition

Key changes from API-based approach:

```json
{
  "containerDefinitions": [{
    "name": "claude-agent",
    "environment": [
      {
        "name": "CREDENTIAL_SOURCE",
        "value": "s3://my-claude-agent-creds/credentials.json"
      }
    ],
    // Remove API key secrets
    // Add S3 read permissions to task role
  }]
}
```

## Credential Refresh Strategy

Session tokens expire (~30 days). Options:

1. **Manual Refresh**:
   - Run `claude login` locally monthly
   - Re-upload to S3
   - Simple but requires maintenance

2. **Automated Refresh Script**:
   ```bash
   #!/bin/bash
   # Check expiry
   EXPIRES=$(jq -r .expiresAt ~/.claude/credentials.json)
   if [[ $(date +%s) -gt $(date -d "$EXPIRES" +%s) ]]; then
     echo "Token expired, please run: claude login"
     exit 1
   fi
   # Upload fresh credentials
   aws s3 cp ~/.claude/credentials.json s3://bucket/ --sse
   ```

3. **Lambda Function**:
   - Monitor expiry in DynamoDB
   - Send SNS notification when refresh needed
   - More complex but hands-off

## Security Considerations

1. **Encryption**:
   - Always use S3 server-side encryption (SSE)
   - Consider client-side encryption for extra security
   - Never commit credentials to Git

2. **Access Control**:
   - Restrict S3 bucket access to Fargate task role only
   - Use VPC endpoints to avoid internet transit
   - Enable CloudTrail for audit logs

3. **Token Isolation**:
   - Each Fargate task gets read-only access
   - Tasks cannot modify stored credentials
   - Use separate S3 paths for different environments

## Cost Analysis

### Max Subscription Approach:
- Claude Max: $200/month (you already pay this)
- S3 Storage: ~$0.01/month
- Fargate Tasks: ~$0.004 per 5-minute task
- **Total Additional**: ~$3-5/month for moderate use

### API Key Approach (comparison):
- API Keys: ~$50-100/month for heavy use
- Fargate Tasks: ~$0.004 per 5-minute task
- **Total**: ~$53-105/month

**Savings**: $50-100/month by using Max subscription

## Pros and Cons

### Pros:
- ✅ No additional API costs
- ✅ Use existing Max subscription benefits
- ✅ True VM isolation for security
- ✅ Works with your current auth flow
- ✅ 20x usage capacity

### Cons:
- ❌ Token expiry management needed
- ❌ Slightly more complex than API keys
- ❌ Potential rate limiting with concurrent tasks
- ❌ Not officially supported pattern

## Rate Limiting Considerations

With Max subscription (20x Pro limits):
- Should handle multiple concurrent tasks
- Monitor for 429 errors
- Consider task queuing if needed
- Add exponential backoff

## Quick Start Commands

```bash
# 1. Upload credentials
aws s3 cp ~/.claude/credentials.json s3://my-bucket/claude/ --sse

# 2. Run Fargate task
./claude-agent-aws.sh https://github.com/user/repo "task" \
  --credential-source s3://my-bucket/claude/credentials.json

# 3. Refresh credentials (monthly)
claude login
aws s3 cp ~/.claude/credentials.json s3://my-bucket/claude/ --sse
```

## Decision Matrix

| Factor | S3 Storage | Secrets Manager | Docker Image |
|--------|------------|-----------------|--------------|
| Security | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| Ease of Update | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐ |
| Startup Speed | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Cost | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Team Sharing | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐ |

**Recommendation**: S3 Storage for personal use, Secrets Manager for teams

## Next Steps

1. Decide on credential management approach
2. Test token portability with a simple Fargate task
3. Implement credential refresh strategy
4. Update Terraform to remove API key requirements
5. Add monitoring for token expiry

## Alternative: Hybrid Approach

Keep both options available:
- Local Docker for trusted code (fast, free)
- Fargate for untrusted code (secure, small cost)
- Same Max subscription works for both