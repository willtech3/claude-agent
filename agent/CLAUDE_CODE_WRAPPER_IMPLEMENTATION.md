# Claude Code Wrapper Implementation Plan

## Overview

The agent needs to integrate with the existing Claude Code CLI that's already installed in the main Dockerfile. The current implementation in `agent/` is a placeholder FastAPI app that needs to be replaced with a proper wrapper.

## Current Architecture

1. **Main Dockerfile** (`/Dockerfile`):
   - Installs Claude Code CLI via npm
   - Has `agent-entrypoint.sh` that runs Claude Code with proper arguments
   - Supports multiple modes (write, review, ask, analyze)

2. **Agent Service** (`/agent/`):
   - Currently a placeholder FastAPI app
   - Should wrap Claude Code CLI execution
   - Must handle SQS messages and process tasks

## Implementation Strategy

### 1. Task Processing Flow
```
SQS Message → Agent Worker → Task Parser → Claude Code Wrapper → Result Publisher
```

### 2. Claude Code Wrapper Component

```python
# agent/agent/claude_wrapper.py
import asyncio
import json
import subprocess
import tempfile
from typing import Dict, Any, AsyncIterator
import os
import shutil

class ClaudeCodeWrapper:
    def __init__(self):
        self.claude_binary = "claude"  # Installed globally via npm
        
    async def execute_task(self, task: Dict[str, Any]) -> AsyncIterator[Dict[str, Any]]:
        """Execute a Claude Code task and stream results"""
        
        # Extract task parameters
        repo_url = task.get("repository_url")
        prompt = task.get("prompt")
        mode = task.get("mode", "write")
        max_turns = task.get("max_turns")
        
        # Create temporary workspace
        with tempfile.TemporaryDirectory() as workspace:
            # Clone repository
            await self._clone_repository(repo_url, workspace)
            
            # Prepare Claude command
            cmd = self._build_claude_command(prompt, mode, max_turns)
            
            # Execute Claude Code and stream output
            async for event in self._run_claude(cmd, workspace):
                yield event
    
    async def _clone_repository(self, repo_url: str, workspace: str):
        """Clone repository to workspace"""
        repo_dir = os.path.join(workspace, "repo")
        proc = await asyncio.create_subprocess_exec(
            "git", "clone", repo_url, repo_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await proc.communicate()
        
    def _build_claude_command(self, prompt: str, mode: str, max_turns: int = None):
        """Build Claude CLI command"""
        cmd = [
            self.claude_binary,
            "-p",  # Pipe prompt
            "--output-format", "stream-json",
            "--verbose",
            "--dangerously-skip-permissions"
        ]
        
        if max_turns:
            cmd.extend(["--max-turns", str(max_turns)])
            
        # Add tool restrictions based on mode
        if mode == "review" or mode == "ask" or mode == "analyze":
            # Read-only tools only
            cmd.extend([
                "--allowedTools", "Read,Grep,Glob,LS",
                "--disallowedTools", "Write,Edit,MultiEdit,Bash"
            ])
        
        return cmd
    
    async def _run_claude(self, cmd: list, cwd: str) -> AsyncIterator[Dict[str, Any]]:
        """Run Claude Code and stream JSON events"""
        env = os.environ.copy()
        
        # Set up environment
        if "ANTHROPIC_API_KEY" in env:
            # API key will be used automatically
            pass
        elif os.path.exists(os.path.expanduser("~/.claude/.credentials.json")):
            # Credentials file will be used
            pass
        else:
            raise ValueError("No Claude authentication available")
        
        # Create process
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=os.path.join(cwd, "repo"),
            env=env
        )
        
        # Write prompt to stdin
        proc.stdin.write(prompt.encode())
        await proc.stdin.drain()
        proc.stdin.close()
        
        # Stream output
        buffer = ""
        while True:
            chunk = await proc.stdout.read(1024)
            if not chunk:
                break
                
            buffer += chunk.decode()
            lines = buffer.split("\n")
            buffer = lines[-1]  # Keep incomplete line
            
            for line in lines[:-1]:
                if line.strip():
                    try:
                        event = json.loads(line)
                        yield event
                    except json.JSONDecodeError:
                        # Not JSON, might be plain text output
                        yield {"type": "output", "text": line}
        
        # Wait for process to complete
        await proc.wait()
        
        if proc.returncode != 0:
            stderr = await proc.stderr.read()
            raise RuntimeError(f"Claude Code failed: {stderr.decode()}")
```

### 3. Worker Integration

```python
# agent/agent/worker.py
import asyncio
import json
from typing import Dict, Any
import boto3
from agent.claude_wrapper import ClaudeCodeWrapper

class AgentWorker:
    def __init__(self):
        self.sqs = boto3.client('sqs', endpoint_url=os.getenv('AWS_ENDPOINT_URL'))
        self.s3 = boto3.client('s3', endpoint_url=os.getenv('AWS_ENDPOINT_URL'))
        self.queue_url = os.getenv('SQS_QUEUE_URL')
        self.wrapper = ClaudeCodeWrapper()
        
    async def start(self):
        """Start processing tasks from SQS"""
        while True:
            try:
                # Receive messages from SQS
                response = self.sqs.receive_message(
                    QueueUrl=self.queue_url,
                    MaxNumberOfMessages=1,
                    WaitTimeSeconds=20
                )
                
                messages = response.get('Messages', [])
                for message in messages:
                    await self._process_message(message)
                    
            except Exception as e:
                logger.error(f"Error processing messages: {e}")
                await asyncio.sleep(5)
    
    async def _process_message(self, message: Dict[str, Any]):
        """Process a single SQS message"""
        try:
            # Parse task from message
            task = json.loads(message['Body'])
            task_id = task['id']
            
            # Update task status to PROCESSING
            await self._update_task_status(task_id, "PROCESSING")
            
            # Execute task
            results = []
            async for event in self.wrapper.execute_task(task):
                results.append(event)
                
                # Stream progress updates
                if event.get('type') == 'progress':
                    await self._send_progress_update(task_id, event)
            
            # Save results to S3
            artifact_url = await self._save_artifacts(task_id, results)
            
            # Update task as completed
            await self._update_task_status(task_id, "COMPLETED", {
                "artifact_url": artifact_url,
                "summary": self._generate_summary(results)
            })
            
            # Delete message from queue
            self.sqs.delete_message(
                QueueUrl=self.queue_url,
                ReceiptHandle=message['ReceiptHandle']
            )
            
        except Exception as e:
            logger.error(f"Error processing task: {e}")
            await self._update_task_status(task_id, "FAILED", {"error": str(e)})
```

### 4. Key Features

1. **Stream Processing**: Events are streamed from Claude Code and processed in real-time
2. **Mode Support**: Different modes (write, review, ask, analyze) with appropriate tool restrictions
3. **Authentication**: Supports both API key and credentials file
4. **Error Handling**: Graceful error handling with proper task status updates
5. **Artifact Storage**: Results saved to S3 for persistence
6. **Progress Updates**: Real-time progress updates via task status API

### 5. Environment Variables

```env
# Claude Configuration
ANTHROPIC_API_KEY=sk-ant-...
CLAUDE_MODEL=claude-3-sonnet-20240229

# AWS Configuration
AWS_ENDPOINT_URL=http://localstack:4566
SQS_QUEUE_URL=http://localstack:4566/000000000000/claude-agent-tasks
S3_BUCKET_NAME=claude-agent-artifacts

# GitHub Token (for Claude to access repos)
GH_TOKEN=ghp_...
```

### 6. Testing Strategy

1. **Unit Tests**: Test wrapper methods individually
2. **Integration Tests**: Test with mock Claude Code process
3. **E2E Tests**: Test full flow with LocalStack and real tasks

## Next Steps

1. Replace current placeholder agent implementation with this wrapper
2. Add proper error handling and logging
3. Implement progress streaming via WebSockets
4. Add metrics and monitoring
5. Create comprehensive tests

## Note

This implementation leverages the existing Claude Code CLI installation from the main Dockerfile. The agent service acts as a wrapper that:
- Receives tasks from SQS
- Executes Claude Code in isolated environments
- Streams results and progress
- Stores artifacts in S3
- Updates task status in the database

The actual Claude Code integration would require the official CLI to be available, which is why this is provided as an implementation plan rather than working code.