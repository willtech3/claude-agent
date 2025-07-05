import asyncio
import json
import logging
import os
import shutil
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional

import redis.asyncio as redis

from .event_parser import OutputParser
from .session import SessionManager

logger = logging.getLogger(__name__)


class MinimalClaudeWrapper:
    """Wrapper for running Claude Code CLI in a container."""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis_client = redis_client
        self.output_parser = OutputParser()
        self.session_manager = SessionManager()
        
    async def process_tasks(self):
        """Main task processing loop (called by SQS handler)."""
        # This is handled by the SQSHandler, but kept for interface compatibility
        pass
        
    async def handle_task(self, message: Dict[str, Any]) -> None:
        """Handle a single task from SQS."""
        task_id = message.get("task_id")
        prompt = message.get("prompt")
        
        if not task_id or not prompt:
            logger.error(f"Invalid message format: {message}")
            return
            
        logger.info(f"Processing task {task_id}")
        
        # Create workspace for this task
        workspace_path = None
        try:
            workspace_path = await self._create_workspace(task_id)
            
            # Run Claude Code subprocess
            await self._run_claude_code(task_id, prompt, workspace_path)
            
            # Signal task completion
            await self._publish_event(task_id, {
                "type": "completion",
                "status": "success"
            })
            
        except Exception as e:
            logger.error(f"Error processing task {task_id}: {e}", exc_info=True)
            await self._publish_event(task_id, {
                "type": "error",
                "message": str(e)
            })
        finally:
            # Clean up workspace
            if workspace_path and os.path.exists(workspace_path):
                shutil.rmtree(workspace_path)
                
    async def _create_workspace(self, task_id: str) -> str:
        """Create isolated workspace for task."""
        workspace_dir = Path("/workspaces") / task_id
        workspace_dir.mkdir(parents=True, exist_ok=True)
        
        # Create .claude directory for Claude Code config
        claude_dir = workspace_dir / ".claude"
        claude_dir.mkdir(exist_ok=True)
        
        logger.info(f"Created workspace at {workspace_dir}")
        return str(workspace_dir)
        
    async def _run_claude_code(self, task_id: str, prompt: str, workspace: str) -> None:
        """Run Claude Code CLI subprocess and stream output."""
        
        # Build command
        cmd = [
            "claude-code",  # Assuming claude-code is in PATH
            "--prompt", prompt,
            "--output-format", "json",
            "--no-interactive"
        ]
        
        # Check for API key
        if not os.getenv("ANTHROPIC_API_KEY"):
            logger.warning("ANTHROPIC_API_KEY not set, Claude Code will use stored credentials")
            
        # Create subprocess
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=workspace
        )
        
        # Stream stdout
        async for line in self._read_stream(process.stdout):
            await self._process_output_line(task_id, line)
            
        # Stream stderr (for errors/warnings)
        async for line in self._read_stream(process.stderr):
            await self._publish_event(task_id, {
                "type": "stderr",
                "content": line
            })
            
        # Wait for completion
        return_code = await process.wait()
        
        if return_code != 0:
            raise RuntimeError(f"Claude Code exited with code {return_code}")
            
    async def _read_stream(self, stream):
        """Read from async stream line by line."""
        while True:
            line = await stream.readline()
            if not line:
                break
            yield line.decode("utf-8").rstrip()
            
    async def _process_output_line(self, task_id: str, line: str) -> None:
        """Process a line of output from Claude Code."""
        # Parse the output
        event = self.output_parser.parse_line(line)
        
        if event:
            # Add task_id to event
            event["task_id"] = task_id
            
            # Publish to Redis
            await self._publish_event(task_id, event)
            
    async def _publish_event(self, task_id: str, event: Dict[str, Any]) -> None:
        """Publish event to Redis channel."""
        channel = f"task:{task_id}"
        message = json.dumps(event)
        
        await self.redis_client.publish(channel, message)
        logger.debug(f"Published to {channel}: {event['type']}")