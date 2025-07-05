# Claude Code Container Wrapper

This is the minimal wrapper implementation for running Claude Code CLI in a container, as specified in issue #42.

## Architecture

The wrapper consists of several components:

1. **main.py** - Entry point that sets up Redis and SQS connections
2. **claude_code.py** - MinimalClaudeWrapper class that handles task execution
3. **sqs_handler.py** - Polls SQS for tasks and delegates to the wrapper
4. **event_parser.py** - Parses Claude Code output into structured events
5. **session.py** - Manages isolated sessions for each task

## Running Locally

1. Start the services:
```bash
docker-compose up -d
```

2. Send a test task:
```bash
python test_wrapper.py
```

3. Monitor output in Redis:
```bash
redis-cli subscribe 'task:test-task-001'
```

## Environment Variables

- `ANTHROPIC_API_KEY` - API key for Claude (required)
- `SQS_QUEUE_URL` - URL of the SQS queue for tasks
- `REDIS_URL` - Redis connection URL for publishing events
- `AWS_ENDPOINT_URL` - LocalStack endpoint for local development

## Task Message Format

```json
{
  "task_id": "unique-task-id",
  "prompt": "The prompt to send to Claude Code"
}
```

## Output Events

Events are published to Redis channel `task:{task_id}` with the following types:

- `tool_use` - Tool invocation by Claude
- `message` - Assistant messages
- `file_operation` - File read/write operations
- `command_execution` - Command executions
- `status` - Status updates
- `error` - Error messages
- `completion` - Task completion signal