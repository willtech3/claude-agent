import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from pathlib import Path

from agent.claude_code import ClaudeCodeWrapper
from agent.session import SessionManager, Session
from agent.event_parser import EventType


@pytest.fixture
def session_manager(tmp_path):
    return SessionManager(base_dir=str(tmp_path))


@pytest.fixture
def claude_wrapper(session_manager):
    return ClaudeCodeWrapper(session_manager)


@pytest.fixture
def mock_session(tmp_path):
    session = Session(
        session_id="test-123",
        task_id="task-456",
        session_dir=tmp_path / "session",
        repository_url="https://github.com/test/repo.git"
    )
    session.session_dir.mkdir(parents=True, exist_ok=True)
    session.workspace_dir.mkdir(parents=True, exist_ok=True)
    session.artifacts_dir.mkdir(parents=True, exist_ok=True)
    session.logs_dir.mkdir(parents=True, exist_ok=True)
    return session


class TestClaudeCodeWrapper:
    def test_find_claude_binary(self, claude_wrapper):
        # Test that it finds a binary path
        binary = claude_wrapper._find_claude_binary()
        assert isinstance(binary, str)
        assert binary  # Should not be empty
        
    @pytest.mark.asyncio
    async def test_execute_task_missing_params(self, claude_wrapper):
        # Test with missing required parameters
        task = {"id": "test-123"}
        
        events = []
        async for event in claude_wrapper.execute_task(task):
            events.append(event)
            
        assert len(events) == 1
        assert events[0]["type"] == EventType.ERROR
        assert "Missing required parameters" in events[0]["error"]
        
    @pytest.mark.asyncio
    async def test_execute_task_success(self, claude_wrapper, mock_session):
        # Mock the session manager
        claude_wrapper.session_manager.create_session = Mock(return_value=mock_session)
        claude_wrapper.session_manager.cleanup_session = Mock()
        
        # Mock subprocess methods
        with patch.object(claude_wrapper, '_clone_repository', new_callable=AsyncMock) as mock_clone:
            with patch.object(claude_wrapper, '_run_claude', new_callable=AsyncMock) as mock_run:
                # Set up mock_run to yield events
                async def mock_run_claude(*args):
                    yield {"type": EventType.PROGRESS, "status": "working"}
                    yield {"type": EventType.COMPLETION, "status": "completed", "summary": {}}
                    
                mock_run.side_effect = mock_run_claude
                
                task = {
                    "id": "test-123",
                    "repository_url": "https://github.com/test/repo.git",
                    "prompt": "Test prompt",
                    "mode": "write"
                }
                
                events = []
                async for event in claude_wrapper.execute_task(task):
                    events.append(event)
                    
                # Verify events
                assert len(events) >= 2
                assert events[0]["type"] == EventType.PROGRESS
                assert events[0]["status"] == "cloning_repository"
                
                # Verify methods were called
                mock_clone.assert_called_once()
                mock_run.assert_called_once()
                claude_wrapper.session_manager.cleanup_session.assert_called_once()
                
    @pytest.mark.asyncio
    async def test_clone_repository_success(self, claude_wrapper, mock_session):
        # Mock subprocess
        mock_proc = AsyncMock()
        mock_proc.returncode = 0
        mock_proc.communicate = AsyncMock(return_value=(b"", b""))
        
        with patch('asyncio.create_subprocess_exec', return_value=mock_proc) as mock_exec:
            await claude_wrapper._clone_repository("https://github.com/test/repo.git", mock_session)
            
            # Verify git clone was called
            calls = mock_exec.call_args_list
            assert len(calls) >= 1
            assert calls[0][0][0] == "git"
            assert calls[0][0][1] == "clone"
            
    @pytest.mark.asyncio
    async def test_clone_repository_failure(self, claude_wrapper, mock_session):
        # Mock subprocess failure
        mock_proc = AsyncMock()
        mock_proc.returncode = 1
        mock_proc.communicate = AsyncMock(return_value=(b"", b"Error: failed to clone"))
        
        with patch('asyncio.create_subprocess_exec', return_value=mock_proc):
            with pytest.raises(RuntimeError, match="Failed to clone repository"):
                await claude_wrapper._clone_repository("https://github.com/test/repo.git", mock_session)
                
    def test_build_claude_command_write_mode(self, claude_wrapper):
        cmd = claude_wrapper._build_claude_command("test prompt", "write", max_turns=5)
        
        assert claude_wrapper.claude_binary in cmd
        assert "-p" in cmd
        assert "--output-format" in cmd
        assert "stream-json" in cmd
        assert "--max-turns" in cmd
        assert "5" in cmd
        assert "--allowedTools" in cmd
        assert "Write" in cmd[cmd.index("--allowedTools") + 1]
        assert "Edit" in cmd[cmd.index("--allowedTools") + 1]
        
    def test_build_claude_command_review_mode(self, claude_wrapper):
        cmd = claude_wrapper._build_claude_command("test prompt", "review", max_turns=None)
        
        assert "--disallowedTools" in cmd
        assert "Write" in cmd[cmd.index("--disallowedTools") + 1]
        assert "Edit" in cmd[cmd.index("--disallowedTools") + 1]
        assert "--max-turns" not in cmd
        
    @pytest.mark.asyncio
    async def test_run_claude_success(self, claude_wrapper, mock_session):
        # Mock subprocess
        mock_proc = AsyncMock()
        mock_proc.returncode = 0
        mock_proc.stdin = AsyncMock()
        mock_proc.stdin.write = Mock()
        mock_proc.stdin.drain = AsyncMock()
        mock_proc.stdin.close = Mock()
        mock_proc.stdout = AsyncMock()
        mock_proc.stderr = AsyncMock()
        mock_proc.wait = AsyncMock(return_value=0)
        
        # Mock stdout to return JSON events
        async def mock_readline():
            for line in [
                '{"type": "message_start"}\n',
                '{"type": "content_block_start", "content_block": {"type": "tool_use", "name": "Write"}}\n',
                '{"type": "content_block_stop"}\n',
                '{"type": "message_delta", "delta": {"stop_reason": "end_turn"}}\n',
                ''
            ]:
                yield line.encode()
                
        mock_proc.stdout.readline = AsyncMock(side_effect=mock_readline().__anext__)
        
        with patch('asyncio.create_subprocess_exec', return_value=mock_proc):
            with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'}):
                events = []
                async for event in claude_wrapper._run_claude("test prompt", "write", None, mock_session):
                    events.append(event)
                    
                # Verify events were parsed
                assert len(events) > 0
                assert any(e["type"] == EventType.COMPLETION for e in events)
                
    @pytest.mark.asyncio
    async def test_run_claude_no_auth(self, claude_wrapper, mock_session):
        # Test with no authentication
        with patch.dict('os.environ', {}, clear=True):
            with patch('os.path.exists', return_value=False):
                with pytest.raises(ValueError, match="No Claude authentication available"):
                    async for _ in claude_wrapper._run_claude("test", "write", None, mock_session):
                        pass
                        
    @pytest.mark.asyncio
    async def test_run_claude_process_failure(self, claude_wrapper, mock_session):
        # Mock subprocess failure
        mock_proc = AsyncMock()
        mock_proc.returncode = 1
        mock_proc.stdin = AsyncMock()
        mock_proc.stdin.write = Mock()
        mock_proc.stdin.drain = AsyncMock()
        mock_proc.stdin.close = Mock()
        mock_proc.stdout = AsyncMock()
        mock_proc.stdout.readline = AsyncMock(return_value=b'')
        mock_proc.stderr = AsyncMock()
        mock_proc.stderr.read = AsyncMock(return_value=b'Claude error')
        mock_proc.wait = AsyncMock(return_value=1)
        
        with patch('asyncio.create_subprocess_exec', return_value=mock_proc):
            with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'}):
                events = []
                async for event in claude_wrapper._run_claude("test", "write", None, mock_session):
                    events.append(event)
                    
                # Should have an error event
                assert any(e["type"] == EventType.ERROR for e in events)
                error_event = next(e for e in events if e["type"] == EventType.ERROR)
                assert "exit code 1" in error_event["error"]