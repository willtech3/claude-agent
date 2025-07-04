# 9. Event-Driven Architecture

Date: 2025-01-04

## Status

Accepted

## Context

The Claude Agent system needs to:
- Handle long-running AI tasks (minutes to hours)
- Provide real-time status updates
- Scale independently based on load
- Maintain system responsiveness
- Support async workflows

Traditional request-response patterns would:
- Timeout on long operations
- Block resources
- Provide poor user experience
- Limit scalability

## Decision

Implement event-driven architecture using:

### Message Flow
```
API Request → SQS → ECS Agent → S3/Database
      ↓                  ↓
  Task Created      Status Updates
      ↓                  ↓
  WebSocket ←────── Lambda Handler
```

### Event Types
```typescript
interface TaskEvent {
  type: 'task.created' | 'task.started' | 'task.progress' | 
        'task.completed' | 'task.failed'
  taskId: string
  timestamp: Date
  payload: any
}
```

### Components
- **SQS**: Task queue for reliability
- **EventBridge**: System-wide event bus (future)
- **WebSockets**: Real-time client updates
- **DynamoDB Streams**: Database change events

### Implementation
1. API creates task and enqueues to SQS
2. Returns task ID immediately
3. Agent processes from queue
4. Publishes status events
5. WebSocket handler forwards to client

## Consequences

**Positive:**
- Highly scalable architecture
- Resilient to failures
- Real-time user experience
- Decoupled components
- Easy to add new event consumers
- Natural audit log from events

**Negative:**
- Complex debugging across services
- Eventual consistency challenges
- Message ordering considerations
- Additional infrastructure (SQS, WebSockets)
- Potential message duplication
- Client complexity for event handling