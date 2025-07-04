import os
import uuid
import tempfile
import shutil
from typing import Dict, Any, Optional
from pathlib import Path
import structlog

from agent.config import config

logger = structlog.get_logger()


class SessionManager:
    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = Path(base_dir or config.session_base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
    def create_session(self, task_id: str, repository_url: str) -> 'Session':
        session_id = f"{task_id}-{uuid.uuid4().hex[:8]}"
        session_dir = self.base_dir / session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        
        return Session(
            session_id=session_id,
            task_id=task_id,
            session_dir=session_dir,
            repository_url=repository_url
        )
        
    def cleanup_session(self, session: 'Session'):
        try:
            if session.session_dir.exists():
                shutil.rmtree(session.session_dir)
                logger.info("Cleaned up session", session_id=session.session_id)
        except Exception as e:
            logger.error("Failed to cleanup session", session_id=session.session_id, error=str(e))


class Session:
    def __init__(self, session_id: str, task_id: str, session_dir: Path, repository_url: str):
        self.session_id = session_id
        self.task_id = task_id
        self.session_dir = session_dir
        self.repository_url = repository_url
        
        # Create subdirectories
        self.workspace_dir = session_dir / "workspace"
        self.artifacts_dir = session_dir / "artifacts"
        self.logs_dir = session_dir / "logs"
        
        for dir_path in [self.workspace_dir, self.artifacts_dir, self.logs_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
            
    @property
    def repo_dir(self) -> Path:
        return self.workspace_dir / "repo"
        
    def get_env(self) -> Dict[str, str]:
        env = os.environ.copy()
        env.update({
            "TASK_ID": self.task_id,
            "SESSION_ID": self.session_id,
            "WORKSPACE_DIR": str(self.workspace_dir),
            "ARTIFACTS_DIR": str(self.artifacts_dir),
            "REPO_URL": self.repository_url
        })
        return env