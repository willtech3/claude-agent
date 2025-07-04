import asyncio
import os
import json
import subprocess
from typing import Dict, Any, AsyncIterator, Optional, List
from pathlib import Path
import structlog

from agent.session import Session, SessionManager
from agent.event_parser import ClaudeOutputParser, EventType
from agent.config import config

logger = structlog.get_logger()


class ClaudeCodeWrapper:
    def __init__(self, session_manager: SessionManager):
        self.session_manager = session_manager
        self.claude_binary = self._find_claude_binary()
        
    def _find_claude_binary(self) -> str:
        # Check if claude is in PATH
        result = subprocess.run(["which", "claude"], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
            
        # Check common locations
        common_paths = [
            "/usr/local/bin/claude",
            "/usr/bin/claude",
            "/home/node/.npm-global/bin/claude",
            "/usr/local/lib/node_modules/@anthropic-ai/claude-code/bin/claude"
        ]
        
        for path in common_paths:
            if os.path.exists(path):
                return path
                
        # Default to assuming it's in PATH
        return "claude"
        
    async def execute_task(self, task: Dict[str, Any]) -> AsyncIterator[Dict[str, Any]]:
        task_id = task.get("id", "unknown")
        repository_url = task.get("repository_url", "")
        prompt = task.get("prompt", "")
        mode = task.get("mode", "write")
        max_turns = task.get("max_turns", None)
        
        if not repository_url or not prompt:
            yield {
                "type": EventType.ERROR,
                "error": "Missing required parameters: repository_url and prompt",
                "task_id": task_id
            }
            return
            
        # Create session
        session = self.session_manager.create_session(task_id, repository_url)
        
        try:
            # Clone repository
            yield {
                "type": EventType.PROGRESS,
                "status": "cloning_repository",
                "message": f"Cloning repository: {repository_url}",
                "task_id": task_id
            }
            
            await self._clone_repository(repository_url, session)
            
            # Prepare and run Claude
            yield {
                "type": EventType.PROGRESS,
                "status": "starting_claude",
                "message": "Starting Claude Code execution",
                "task_id": task_id
            }
            
            async for event in self._run_claude(prompt, mode, max_turns, session):
                event["task_id"] = task_id
                yield event
                
        except Exception as e:
            logger.error("Task execution failed", task_id=task_id, error=str(e))
            yield {
                "type": EventType.ERROR,
                "error": str(e),
                "task_id": task_id
            }
        finally:
            # Cleanup session
            self.session_manager.cleanup_session(session)
            
    async def _clone_repository(self, repo_url: str, session: Session):
        env = session.get_env()
        
        # Add GitHub token if available
        if config.gh_token:
            env["GH_TOKEN"] = config.gh_token
            # Configure git to use token
            repo_url = repo_url.replace("https://github.com/", f"https://x-access-token:{config.gh_token}@github.com/")
            
        cmd = ["git", "clone", repo_url, str(session.repo_dir)]
        
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env
        )
        
        stdout, stderr = await proc.communicate()
        
        if proc.returncode != 0:
            raise RuntimeError(f"Failed to clone repository: {stderr.decode()}")
            
        # Configure git user
        git_config_cmds = [
            ["git", "config", "user.name", "Claude Agent"],
            ["git", "config", "user.email", "claude@example.com"]
        ]
        
        for config_cmd in git_config_cmds:
            proc = await asyncio.create_subprocess_exec(
                *config_cmd,
                cwd=str(session.repo_dir),
                env=env
            )
            await proc.communicate()
            
    def _build_claude_command(self, prompt: str, mode: str, max_turns: Optional[int]) -> List[str]:
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
        if mode in ["review", "ask", "analyze"]:
            # Read-only tools
            cmd.extend([
                "--allowedTools", "Read,Grep,Glob,LS,Bash",
                "--disallowedTools", "Write,Edit,MultiEdit"
            ])
        else:
            # Full tools for write mode
            cmd.extend([
                "--allowedTools", 
                "Read,Write,Edit,MultiEdit,Grep,Glob,LS,Bash",
                "--disallowedTools",
                "WebSearch,WebFetch"  # Disable web tools for security
            ])
            
        return cmd
        
    async def _run_claude(self, prompt: str, mode: str, max_turns: Optional[int], session: Session) -> AsyncIterator[Dict[str, Any]]:
        cmd = self._build_claude_command(prompt, mode, max_turns)
        env = session.get_env()
        
        # Ensure Claude authentication
        if "ANTHROPIC_API_KEY" not in env and not os.path.exists(os.path.expanduser("~/.claude/.credentials.json")):
            raise ValueError("No Claude authentication available. Set ANTHROPIC_API_KEY or mount credentials.")
            
        # Add mode-specific prompt enforcement
        if mode == "write":
            enforced_prompt = f"""[SYSTEM: You MUST commit all changes and create a PR before finishing. Include these as todos: git add, git commit, git push, gh pr create. This is MANDATORY.]

{prompt}"""
        else:
            enforced_prompt = f"""[SYSTEM: This is {mode.upper()} mode - a READ-ONLY operation. Do NOT make any code changes. Save all outputs to {session.artifacts_dir}/. The artifacts directory is mounted and will persist after the container exits.]

{prompt}"""
            
        # Create process
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(session.repo_dir),
            env=env
        )
        
        # Write prompt to stdin
        proc.stdin.write(enforced_prompt.encode())
        await proc.stdin.drain()
        proc.stdin.close()
        
        # Parse output
        parser = ClaudeOutputParser()
        
        # Stream stdout
        while True:
            line = await proc.stdout.readline()
            if not line:
                break
                
            line_str = line.decode('utf-8', errors='replace')
            event = parser.parse_line(line_str)
            
            if event:
                yield event
                
        # Wait for process to complete
        await proc.wait()
        
        if proc.returncode != 0:
            stderr = await proc.stderr.read()
            error_msg = stderr.decode('utf-8', errors='replace')
            yield {
                "type": EventType.ERROR,
                "error": f"Claude Code failed with exit code {proc.returncode}: {error_msg}"
            }
        else:
            # Send completion event with summary
            yield {
                "type": EventType.COMPLETION,
                "status": "completed",
                "summary": parser.get_summary()
            }