import pytest
import os
import shutil
from pathlib import Path
from unittest.mock import patch

from agent.session import SessionManager, Session
from agent.config import config


@pytest.fixture
def temp_dir(tmp_path):
    return tmp_path / "sessions"


@pytest.fixture
def session_manager(temp_dir):
    return SessionManager(base_dir=str(temp_dir))


class TestSessionManager:
    def test_init_creates_base_dir(self, temp_dir):
        manager = SessionManager(base_dir=str(temp_dir))
        assert temp_dir.exists()
        assert temp_dir.is_dir()
        
    def test_create_session(self, session_manager):
        task_id = "task-123"
        repo_url = "https://github.com/test/repo.git"
        
        session = session_manager.create_session(task_id, repo_url)
        
        assert session.task_id == task_id
        assert session.repository_url == repo_url
        assert session.session_id.startswith(f"{task_id}-")
        assert session.session_dir.exists()
        
        # Check subdirectories
        assert session.workspace_dir.exists()
        assert session.artifacts_dir.exists()
        assert session.logs_dir.exists()
        
    def test_cleanup_session_success(self, session_manager):
        # Create a session
        session = session_manager.create_session("task-123", "https://test.git")
        session_dir = session.session_dir
        
        # Create some files in the session
        test_file = session.workspace_dir / "test.txt"
        test_file.write_text("test content")
        
        assert session_dir.exists()
        assert test_file.exists()
        
        # Cleanup
        session_manager.cleanup_session(session)
        
        # Verify cleanup
        assert not session_dir.exists()
        assert not test_file.exists()
        
    def test_cleanup_session_error_handling(self, session_manager):
        # Create a mock session with non-existent directory
        session = Session(
            session_id="test-session",
            task_id="task-123",
            session_dir=Path("/non/existent/path"),
            repository_url="https://test.git"
        )
        
        # Should not raise exception
        session_manager.cleanup_session(session)
        
    def test_multiple_sessions(self, session_manager):
        # Create multiple sessions
        sessions = []
        for i in range(3):
            session = session_manager.create_session(f"task-{i}", f"https://repo-{i}.git")
            sessions.append(session)
            
        # All should have unique IDs and directories
        session_ids = [s.session_id for s in sessions]
        assert len(set(session_ids)) == 3
        
        session_dirs = [s.session_dir for s in sessions]
        assert len(set(session_dirs)) == 3
        
        # All directories should exist
        for session in sessions:
            assert session.session_dir.exists()


class TestSession:
    def test_session_init(self, tmp_path):
        session_dir = tmp_path / "test-session"
        session = Session(
            session_id="sess-123",
            task_id="task-456",
            session_dir=session_dir,
            repository_url="https://github.com/test/repo.git"
        )
        
        assert session.session_id == "sess-123"
        assert session.task_id == "task-456"
        assert session.session_dir == session_dir
        assert session.repository_url == "https://github.com/test/repo.git"
        
        # Check subdirectories were created
        assert session.workspace_dir.exists()
        assert session.artifacts_dir.exists()
        assert session.logs_dir.exists()
        
    def test_repo_dir_property(self, tmp_path):
        session = Session(
            session_id="sess-123",
            task_id="task-456",
            session_dir=tmp_path / "session",
            repository_url="https://test.git"
        )
        
        expected_repo_dir = session.workspace_dir / "repo"
        assert session.repo_dir == expected_repo_dir
        
    def test_get_env(self, tmp_path):
        session = Session(
            session_id="sess-123",
            task_id="task-456",
            session_dir=tmp_path / "session",
            repository_url="https://github.com/test/repo.git"
        )
        
        # Mock environment
        with patch.dict(os.environ, {"EXISTING_VAR": "value"}, clear=True):
            env = session.get_env()
            
            # Check original env is preserved
            assert env["EXISTING_VAR"] == "value"
            
            # Check session-specific vars
            assert env["TASK_ID"] == "task-456"
            assert env["SESSION_ID"] == "sess-123"
            assert env["WORKSPACE_DIR"] == str(session.workspace_dir)
            assert env["ARTIFACTS_DIR"] == str(session.artifacts_dir)
            assert env["REPO_URL"] == "https://github.com/test/repo.git"
            
    def test_session_directories_structure(self, tmp_path):
        session = Session(
            session_id="sess-123",
            task_id="task-456",
            session_dir=tmp_path / "session",
            repository_url="https://test.git"
        )
        
        # Verify directory structure
        assert session.workspace_dir == session.session_dir / "workspace"
        assert session.artifacts_dir == session.session_dir / "artifacts"
        assert session.logs_dir == session.session_dir / "logs"
        
        # All should be created
        for dir_path in [session.workspace_dir, session.artifacts_dir, session.logs_dir]:
            assert dir_path.exists()
            assert dir_path.is_dir()